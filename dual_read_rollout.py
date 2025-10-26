#!/usr/bin/env python3
"""
Dual-Read Rollout Strategy for DocsV2
=====================================

Safe cutover from BM25 to semantic search with shadow comparison.
Merge + dedupe results by doc_id for seamless transition.
"""

import requests
import json
import time
import statistics
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Single search result"""
    doc_id: str
    path: str
    text: str
    score: float
    method: str  # 'bm25' or 'semantic'
    rank: int

@dataclass
class DualSearchResult:
    """Combined BM25 + semantic search results"""
    query: str
    bm25_results: List[SearchResult]
    semantic_results: List[SearchResult]
    merged_results: List[SearchResult]
    latency_ms: float

class DualReadRollout:
    """Dual-read rollout manager for safe semantic search cutover"""
    
    def __init__(self, weaviate_url: str = "http://127.0.0.1:8090"):
        self.weaviate_url = weaviate_url
        self.feature_flag_enabled = True
        self.semantic_weight = 0.7  # Weight for semantic results in merge
        self.bm25_weight = 0.3      # Weight for BM25 results in merge
    
    def search_bm25(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search using BM25 keyword matching"""
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
            
            if "errors" in result:
                logger.error(f"BM25 search errors: {result['errors']}")
                return []
            
            docs = result.get("data", {}).get("Get", {}).get("DocsV2", [])
            
            results = []
            for i, doc in enumerate(docs):
                results.append(SearchResult(
                    doc_id=doc["path"],  # Use path as doc_id
                    path=doc["path"],
                    text=doc["text"],
                    score=doc["_additional"]["score"],
                    method="bm25",
                    rank=i + 1
                ))
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"BM25 search failed: {e}")
            return []
    
    def search_semantic(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search using semantic similarity"""
        if not self.feature_flag_enabled:
            logger.info("Semantic search disabled via feature flag")
            return []
        
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
            
            if "errors" in result:
                logger.error(f"Semantic search errors: {result['errors']}")
                return []
            
            docs = result.get("data", {}).get("Get", {}).get("DocsV2", [])
            
            results = []
            for i, doc in enumerate(docs):
                # Convert distance to score (lower distance = higher score)
                distance = doc["_additional"]["distance"]
                score = 1.0 - distance  # Convert to 0-1 range
                
                results.append(SearchResult(
                    doc_id=doc["path"],  # Use path as doc_id
                    path=doc["path"],
                    text=doc["text"],
                    score=score,
                    method="semantic",
                    rank=i + 1
                ))
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def merge_results(self, bm25_results: List[SearchResult], 
                     semantic_results: List[SearchResult]) -> List[SearchResult]:
        """Merge and dedupe BM25 + semantic results"""
        
        # Create doc_id -> result mapping
        doc_results = {}
        
        # Add BM25 results
        for result in bm25_results:
            doc_id = result.doc_id
            if doc_id not in doc_results:
                doc_results[doc_id] = {
                    'bm25': None,
                    'semantic': None,
                    'combined_score': 0.0
                }
            
            doc_results[doc_id]['bm25'] = result
            doc_results[doc_id]['combined_score'] += result.score * self.bm25_weight
        
        # Add semantic results
        for result in semantic_results:
            doc_id = result.doc_id
            if doc_id not in doc_results:
                doc_results[doc_id] = {
                    'bm25': None,
                    'semantic': None,
                    'combined_score': 0.0
                }
            
            doc_results[doc_id]['semantic'] = result
            doc_results[doc_id]['combined_score'] += result.score * self.semantic_weight
        
        # Create merged results
        merged_results = []
        for doc_id, data in doc_results.items():
            # Prefer semantic result if available, otherwise BM25
            primary_result = data['semantic'] if data['semantic'] else data['bm25']
            
            if primary_result:
                merged_result = SearchResult(
                    doc_id=primary_result.doc_id,
                    path=primary_result.path,
                    text=primary_result.text,
                    score=data['combined_score'],
                    method=f"merged({primary_result.method})",
                    rank=0  # Will be set after sorting
                )
                merged_results.append(merged_result)
        
        # Sort by combined score
        merged_results.sort(key=lambda x: x.score, reverse=True)
        
        # Update ranks
        for i, result in enumerate(merged_results):
            result.rank = i + 1
        
        return merged_results
    
    def dual_search(self, query: str, limit: int = 10) -> DualSearchResult:
        """Perform dual search (BM25 + semantic) and merge results"""
        start_time = time.time()
        
        logger.info(f"🔍 Dual search: '{query}'")
        
        # Search both methods
        bm25_results = self.search_bm25(query, limit)
        semantic_results = self.search_semantic(query, limit)
        
        # Merge results
        merged_results = self.merge_results(bm25_results, semantic_results)
        
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info(f"  BM25: {len(bm25_results)} results")
        logger.info(f"  Semantic: {len(semantic_results)} results")
        logger.info(f"  Merged: {len(merged_results)} results")
        logger.info(f"  Latency: {latency_ms:.1f}ms")
        
        return DualSearchResult(
            query=query,
            bm25_results=bm25_results,
            semantic_results=semantic_results,
            merged_results=merged_results,
            latency_ms=latency_ms
        )
    
    def compare_methods(self, test_queries: List[str]) -> Dict:
        """Compare BM25 vs semantic vs merged performance"""
        logger.info("📊 Comparing search methods...")
        
        results = {
            'bm25_only': [],
            'semantic_only': [],
            'merged': []
        }
        
        for query in test_queries:
            dual_result = self.dual_search(query, limit=5)
            
            # BM25 only
            bm25_latency = sum(r.score for r in dual_result.bm25_results) / max(len(dual_result.bm25_results), 1)
            results['bm25_only'].append({
                'query': query,
                'result_count': len(dual_result.bm25_results),
                'avg_score': bm25_latency
            })
            
            # Semantic only
            semantic_latency = sum(r.score for r in dual_result.semantic_results) / max(len(dual_result.semantic_results), 1)
            results['semantic_only'].append({
                'query': query,
                'result_count': len(dual_result.semantic_results),
                'avg_score': semantic_latency
            })
            
            # Merged
            merged_score = sum(r.score for r in dual_result.merged_results) / max(len(dual_result.merged_results), 1)
            results['merged'].append({
                'query': query,
                'result_count': len(dual_result.merged_results),
                'avg_score': merged_score,
                'latency_ms': dual_result.latency_ms
            })
        
        return results
    
    def rollout_status(self) -> Dict:
        """Get current rollout status"""
        return {
            'feature_flag_enabled': self.feature_flag_enabled,
            'semantic_weight': self.semantic_weight,
            'bm25_weight': self.bm25_weight,
            'rollout_percentage': self.semantic_weight * 100,
            'status': 'dual_read' if self.feature_flag_enabled else 'bm25_only'
        }
    
    def promote_semantic(self, weight: float = 1.0):
        """Promote semantic search (increase weight)"""
        self.semantic_weight = min(weight, 1.0)
        self.bm25_weight = 1.0 - self.semantic_weight
        
        logger.info(f"🎯 Promoted semantic search: {self.semantic_weight:.1%} weight")
    
    def rollback_to_bm25(self):
        """Rollback to BM25-only search"""
        self.feature_flag_enabled = False
        self.semantic_weight = 0.0
        self.bm25_weight = 1.0
        
        logger.info("🔄 Rolled back to BM25-only search")

def main():
    rollout = DualReadRollout()
    
    print("🚀 Dual-Read Rollout Strategy")
    print("=" * 30)
    
    # Test queries
    test_queries = [
        "authentication configuration",
        "API rate limiting",
        "database connection pooling",
        "error handling best practices"
    ]
    
    # Compare methods
    comparison = rollout.compare_methods(test_queries)
    
    print(f"\n📊 Method Comparison:")
    print(f"   BM25 only: {len(comparison['bm25_only'])} queries")
    print(f"   Semantic only: {len(comparison['semantic_only'])} queries")
    print(f"   Merged: {len(comparison['merged'])} queries")
    
    # Show rollout status
    status = rollout.rollout_status()
    print(f"\n🎯 Rollout Status:")
    print(f"   Feature flag: {'✅ Enabled' if status['feature_flag_enabled'] else '❌ Disabled'}")
    print(f"   Semantic weight: {status['semantic_weight']:.1%}")
    print(f"   BM25 weight: {status['bm25_weight']:.1%}")
    print(f"   Status: {status['status']}")
    
    # Demonstrate dual search
    print(f"\n🔍 Dual Search Example:")
    dual_result = rollout.dual_search("authentication setup", limit=3)
    
    print(f"   Query: '{dual_result.query}'")
    print(f"   BM25 results: {len(dual_result.bm25_results)}")
    print(f"   Semantic results: {len(dual_result.semantic_results)}")
    print(f"   Merged results: {len(dual_result.merged_results)}")
    print(f"   Latency: {dual_result.latency_ms:.1f}ms")
    
    print(f"\n📋 Rollout Strategy:")
    print("   1. Start with dual-read (BM25 + semantic)")
    print("   2. Monitor quality metrics for 2+ hours")
    print("   3. Gradually increase semantic weight")
    print("   4. Promote to semantic-only when gates are green")
    print("   5. Keep BM25 as fallback for edge cases")

if __name__ == "__main__":
    main()
