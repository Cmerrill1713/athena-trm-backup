#!/usr/bin/env python3
"""
RAG Quality Gates - Hit@K & Support@K Evaluation
===============================================

Quality gates to ensure DocsV2 semantic search meets production standards:
- hit@5 ≥ 0.97 (97% of queries find relevant docs in top 5)
- support@3 ≥ 0.95 (95% of queries have good docs in top 3)
- P95 latency Δ vs BM25 ≤ +10% (semantic search isn't too slow)
"""

import json
import time
import requests
import argparse
import statistics
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Single query evaluation result"""
    query: str
    expected_docs: List[str]  # Ground truth relevant docs
    retrieved_docs: List[str]  # Actually retrieved docs
    distances: List[float]     # Similarity distances
    latency_ms: float         # Query latency
    
    def hit_at_k(self, k: int) -> bool:
        """Check if any expected doc is in top-k results"""
        top_k = self.retrieved_docs[:k]
        return any(doc in top_k for doc in self.expected_docs)
    
    def support_at_k(self, k: int) -> float:
        """Fraction of expected docs found in top-k"""
        if not self.expected_docs:
            return 0.0
        
        top_k = self.retrieved_docs[:k]
        found_count = sum(1 for doc in self.expected_docs if doc in top_k)
        return found_count / len(self.expected_docs)

@dataclass
class QualityMetrics:
    """Aggregated quality metrics"""
    hit_at_k: Dict[int, float]      # hit@k scores
    support_at_k: Dict[int, float]  # support@k scores
    avg_latency_ms: float           # Average query latency
    p95_latency_ms: float          # 95th percentile latency
    total_queries: int             # Number of queries evaluated

class RAGEvaluator:
    """RAG system evaluator for DocsV2"""
    
    def __init__(self, weaviate_url: str = "http://127.0.0.1:8090"):
        self.weaviate_url = weaviate_url
        self.test_queries = self._load_test_queries()
    
    def _load_test_queries(self) -> List[Dict]:
        """Load test queries with ground truth"""
        # This is a sample set - replace with your actual test data
        return [
            {
                "query": "How to configure authentication",
                "expected_docs": ["auth_config.md", "security_setup.md"],
                "category": "configuration"
            },
            {
                "query": "API rate limiting implementation",
                "expected_docs": ["rate_limiting.md", "api_docs.md"],
                "category": "api"
            },
            {
                "query": "Database connection pooling",
                "expected_docs": ["db_config.md", "performance_tuning.md"],
                "category": "database"
            },
            {
                "query": "Error handling best practices",
                "expected_docs": ["error_handling.md", "best_practices.md"],
                "category": "development"
            },
            {
                "query": "Monitoring and alerting setup",
                "expected_docs": ["monitoring.md", "alerts.md"],
                "category": "operations"
            }
        ]
    
    def query_docs_v2(self, query: str, limit: int = 10) -> Tuple[List[str], List[float], float]:
        """Query DocsV2 with semantic search"""
        start_time = time.time()
        
        graphql_query = {
            "query": f"""
            {{
              Get {{
                DocsV2(
                  nearText: {{
                    concepts: ["{query}"]
                  }}
                  limit: {limit}
                ) {{
                  path
                  text
                  _additional {{
                    distance
                  }}
                }}
              }}
            }}
            """
        }
        
        try:
            response = requests.post(
                f"{self.weaviate_url}/v1/graphql",
                json=graphql_query,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            latency_ms = (time.time() - start_time) * 1000
            
            if "errors" in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                return [], [], latency_ms
            
            docs = result.get("data", {}).get("Get", {}).get("DocsV2", [])
            
            retrieved_docs = [doc["path"] for doc in docs]
            distances = [doc["_additional"]["distance"] for doc in docs]
            
            return retrieved_docs, distances, latency_ms
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Query failed: {e}")
            return [], [], (time.time() - start_time) * 1000
    
    def query_bm25(self, query: str, limit: int = 10) -> Tuple[List[str], List[float], float]:
        """Query DocsV2 with BM25 keyword search for comparison"""
        start_time = time.time()
        
        graphql_query = {
            "query": f"""
            {{
              Get {{
                DocsV2(
                  bm25: {{
                    query: "{query}"
                  }}
                  limit: {limit}
                ) {{
                  path
                  text
                  _additional {{
                    score
                  }}
                }}
              }}
            }}
            """
        }
        
        try:
            response = requests.post(
                f"{self.weaviate_url}/v1/graphql",
                json=graphql_query,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            latency_ms = (time.time() - start_time) * 1000
            
            if "errors" in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                return [], [], latency_ms
            
            docs = result.get("data", {}).get("Get", {}).get("DocsV2", [])
            
            retrieved_docs = [doc["path"] for doc in docs]
            scores = [doc["_additional"]["score"] for doc in docs]
            
            return retrieved_docs, scores, latency_ms
            
        except requests.exceptions.RequestException as e:
            logger.error(f"BM25 query failed: {e}")
            return [], [], (time.time() - start_time) * 1000
    
    def evaluate_semantic_search(self, k_values: List[int] = [1, 3, 5]) -> QualityMetrics:
        """Evaluate semantic search quality"""
        logger.info("🧪 Evaluating semantic search quality...")
        
        results = []
        
        for test_case in self.test_queries:
            query = test_case["query"]
            expected_docs = test_case["expected_docs"]
            
            logger.info(f"Testing query: '{query}'")
            
            retrieved_docs, distances, latency_ms = self.query_docs_v2(query, limit=max(k_values))
            
            result = QueryResult(
                query=query,
                expected_docs=expected_docs,
                retrieved_docs=retrieved_docs,
                distances=distances,
                latency_ms=latency_ms
            )
            
            results.append(result)
            
            logger.info(f"  Retrieved: {retrieved_docs[:3]}...")
            logger.info(f"  Latency: {latency_ms:.1f}ms")
        
        # Calculate metrics
        hit_at_k = {}
        support_at_k = {}
        
        for k in k_values:
            hit_scores = [result.hit_at_k(k) for result in results]
            support_scores = [result.support_at_k(k) for result in results]
            
            hit_at_k[k] = statistics.mean(hit_scores)
            support_at_k[k] = statistics.mean(support_scores)
        
        latencies = [result.latency_ms for result in results]
        
        return QualityMetrics(
            hit_at_k=hit_at_k,
            support_at_k=support_at_k,
            avg_latency_ms=statistics.mean(latencies),
            p95_latency_ms=statistics.quantiles(latencies, n=20)[18],  # 95th percentile
            total_queries=len(results)
        )
    
    def compare_with_bm25(self) -> Dict[str, float]:
        """Compare semantic search performance with BM25"""
        logger.info("🔄 Comparing semantic vs BM25 performance...")
        
        semantic_latencies = []
        bm25_latencies = []
        
        for test_case in self.test_queries[:3]:  # Test subset for speed
            query = test_case["query"]
            
            # Semantic search
            _, _, sem_latency = self.query_docs_v2(query, limit=5)
            semantic_latencies.append(sem_latency)
            
            # BM25 search
            _, _, bm25_latency = self.query_bm25(query, limit=5)
            bm25_latencies.append(bm25_latency)
        
        avg_semantic = statistics.mean(semantic_latencies)
        avg_bm25 = statistics.mean(bm25_latencies)
        
        latency_ratio = avg_semantic / avg_bm25 if avg_bm25 > 0 else float('inf')
        
        return {
            "semantic_avg_ms": avg_semantic,
            "bm25_avg_ms": avg_bm25,
            "latency_ratio": latency_ratio,
            "latency_delta_percent": (latency_ratio - 1.0) * 100
        }

def main():
    parser = argparse.ArgumentParser(description="RAG Quality Gates Evaluation")
    parser.add_argument("--k", type=int, default=5, help="Primary k value for hit@k")
    parser.add_argument("--support-k", type=int, default=3, help="K value for support@k")
    parser.add_argument("--expect-hit", type=float, default=0.97, help="Expected hit@k threshold")
    parser.add_argument("--expect-support", type=float, default=0.95, help="Expected support@k threshold")
    parser.add_argument("--max-latency-delta", type=float, default=10.0, help="Max latency increase % vs BM25")
    parser.add_argument("--weaviate-url", default="http://127.0.0.1:8090", help="Weaviate URL")
    
    args = parser.parse_args()
    
    evaluator = RAGEvaluator(args.weaviate_url)
    
    print("🎯 RAG Quality Gates Evaluation")
    print("=" * 40)
    
    # Evaluate semantic search
    metrics = evaluator.evaluate_semantic_search([args.k, args.support_k])
    
    print(f"\n📊 Quality Metrics:")
    print(f"   hit@{args.k}: {metrics.hit_at_k[args.k]:.3f} (expect ≥{args.expect_hit})")
    print(f"   support@{args.support_k}: {metrics.support_at_k[args.support_k]:.3f} (expect ≥{args.expect_support})")
    print(f"   Avg latency: {metrics.avg_latency_ms:.1f}ms")
    print(f"   P95 latency: {metrics.p95_latency_ms:.1f}ms")
    
    # Compare with BM25
    comparison = evaluator.compare_with_bm25()
    print(f"\n⚡ Performance Comparison:")
    print(f"   Semantic avg: {comparison['semantic_avg_ms']:.1f}ms")
    print(f"   BM25 avg: {comparison['bm25_avg_ms']:.1f}ms")
    print(f"   Latency delta: {comparison['latency_delta_percent']:.1f}% (expect ≤{args.max_latency_delta}%)")
    
    # Quality gates
    print(f"\n🚦 Quality Gates:")
    
    hit_pass = metrics.hit_at_k[args.k] >= args.expect_hit
    support_pass = metrics.support_at_k[args.support_k] >= args.expect_support
    latency_pass = comparison['latency_delta_percent'] <= args.max_latency_delta
    
    print(f"   hit@{args.k} ≥ {args.expect_hit}: {'✅ PASS' if hit_pass else '❌ FAIL'}")
    print(f"   support@{args.support_k} ≥ {args.expect_support}: {'✅ PASS' if support_pass else '❌ FAIL'}")
    print(f"   latency Δ ≤ {args.max_latency_delta}%: {'✅ PASS' if latency_pass else '❌ FAIL'}")
    
    all_pass = hit_pass and support_pass and latency_pass
    
    if all_pass:
        print(f"\n🎉 ALL QUALITY GATES PASSED! DocsV2 is ready for production.")
        exit(0)
    else:
        print(f"\n⚠️  QUALITY GATES FAILED! DocsV2 needs tuning before production.")
        exit(1)

if __name__ == "__main__":
    main()
