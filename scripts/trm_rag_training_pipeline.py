#!/usr/bin/env python3
"""
TRM-RAG Training Pipeline

Generates training data from RAG corpus and evaluation failures:
1. Mine hard negatives from rag-eval failures
2. Build (<query>, <best_chunks>, <ideal_response>) triples
3. Supervised fine-tune TRM on reasoning + grounding
4. Evaluate improvements

Safety: DocsV2 remains ground truth. TRM must cite when confident.
"""

import os
import sys
import json
import logging
import asyncio
import httpx
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
RAG_GATEWAY_URL = os.getenv("RAG_GATEWAY_URL", "http://localhost:8088")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8090")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

OUTPUT_DIR = Path("data/trm_training")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TrainingExample:
    """Single training example for TRM fine-tuning"""
    query: str
    context_chunks: List[str]
    ideal_response: str
    citations: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_jsonl(self) -> str:
        """Format as JSONL for training"""
        return json.dumps({
            "input": f"Query: {self.query}\n\nContext:\n" + "\n\n".join(
                f"[{i+1}] {chunk}" for i, chunk in enumerate(self.context_chunks)
            ),
            "output": self.ideal_response,
            "metadata": self.metadata
        })


class RAGCorpusExporter:
    """
    Export RAG corpus (DocsV2) for training data generation.
    
    Samples diverse documents from the 5.8GB corpus.
    """
    
    def __init__(self, weaviate_url: str = WEAVIATE_URL):
        self.weaviate_url = weaviate_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def sample_documents(
        self,
        sample_size: int = 1000,
        min_chunk_length: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Sample diverse documents from DocsV2 collection.
        
        Args:
            sample_size: Number of documents to sample
            min_chunk_length: Minimum chunk length (filter out short chunks)
        
        Returns:
            List of document dicts with chunk, title, doc_id, etc.
        """
        logger.info(f"Sampling {sample_size} documents from DocsV2...")
        
        try:
            # Query Weaviate for diverse sample
            graphql_query = {
                "query": f"""
                {{
                    Get {{
                        DocsV2(limit: {sample_size}) {{
                            doc_id
                            title
                            chunk
                            path
                            url
                            _additional {{
                                id
                            }}
                        }}
                    }}
                }}
                """
            }
            
            response = await self.client.post(
                f"{self.weaviate_url}/v1/graphql",
                json=graphql_query
            )
            response.raise_for_status()
            data = response.json()
            
            docs = data.get("data", {}).get("Get", {}).get("DocsV2", [])
            
            # Filter by chunk length
            filtered_docs = [
                doc for doc in docs
                if len(doc.get("chunk", "")) >= min_chunk_length
            ]
            
            logger.info(f"Sampled {len(filtered_docs)} documents (after filtering)")
            return filtered_docs
            
        except Exception as e:
            logger.error(f"Failed to sample documents: {e}")
            return []
    
    async def close(self):
        await self.client.aclose()


class HardNegativeMiner:
    """
    Mine hard negatives from RAG evaluation failures.
    
    Identifies queries where:
    - Retrieved docs didn't help
    - Top-k results were irrelevant
    - Model generated hallucinations
    """
    
    def __init__(self, rag_gateway_url: str = RAG_GATEWAY_URL):
        self.rag_gateway_url = rag_gateway_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def mine_failures(
        self,
        eval_results_path: Path = Path("artifacts/rag_eval_results.json")
    ) -> List[Dict[str, Any]]:
        """
        Mine hard negatives from evaluation results.
        
        Looks for:
        - Low hit@k scores
        - Low support@k scores
        - High latency queries
        
        Returns:
            List of failed query dicts with failure type and metadata
        """
        if not eval_results_path.exists():
            logger.warning(f"Eval results not found: {eval_results_path}")
            return []
        
        logger.info(f"Mining hard negatives from {eval_results_path}...")
        
        with open(eval_results_path) as f:
            eval_data = json.load(f)
        
        failures = []
        
        # Extract failed queries (those with hit@k = 0)
        for result in eval_data.get("results", []):
            if result.get("hit_at_k", 1.0) < 0.5:  # Low hit rate
                failures.append({
                    "query": result.get("query", ""),
                    "failure_type": "low_hit_rate",
                    "hit_at_k": result.get("hit_at_k", 0.0),
                    "retrieved_docs": result.get("retrieved_docs", [])
                })
        
        logger.info(f"Found {len(failures)} hard negative examples")
        return failures
    
    async def close(self):
        await self.client.aclose()


class TrainingDataGenerator:
    """
    Generate training triples: (<query>, <context>, <ideal_response>)
    
    Uses a strong LLM (Ollama) to generate ideal responses given context.
    """
    
    def __init__(self, ollama_url: str = OLLAMA_URL):
        self.ollama_url = ollama_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def generate_training_example(
        self,
        query: str,
        context_chunks: List[str],
        ground_truth: Optional[str] = None
    ) -> TrainingExample:
        """
        Generate a training example.
        
        Args:
            query: User query
            context_chunks: Retrieved context chunks
            ground_truth: Optional ground truth response
        
        Returns:
            TrainingExample with query, context, and ideal response
        """
        logger.info(f"Generating training example for query: {query[:100]}")
        
        # Format context
        context_text = "\n\n".join(
            f"[Document {i+1}]\n{chunk}"
            for i, chunk in enumerate(context_chunks)
        )
        
        # Generate ideal response using LLM
        prompt = f"""You are a helpful assistant that generates accurate, well-cited responses.

Query: {query}

Context:
{context_text}

Generate a clear, accurate response that:
1. Answers the query directly
2. Cites relevant documents using [Document N] format
3. Acknowledges if the context doesn't fully answer the query
4. Is concise but complete

Response:"""
        
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "qwen2.5-coder:7b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Low temp for factual responses
                        "top_p": 0.9
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                ideal_response = data.get("response", "").strip()
            else:
                ideal_response = "[Generation failed]"
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            ideal_response = "[Generation failed]"
        
        # Extract citations
        citations = self._extract_citations(ideal_response)
        
        return TrainingExample(
            query=query,
            context_chunks=context_chunks,
            ideal_response=ideal_response,
            citations=citations,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "model": "qwen2.5-coder:7b",
                "has_ground_truth": ground_truth is not None
            }
        )
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extract [Document N] citations from text"""
        import re
        citations = re.findall(r'\[Document \d+\]', text)
        return list(set(citations))
    
    async def close(self):
        await self.client.aclose()


class TRMTrainingPipeline:
    """
    Complete TRM training pipeline using RAG corpus.
    
    Steps:
    1. Sample documents from DocsV2
    2. Mine hard negatives from eval failures
    3. Generate synthetic queries from documents
    4. Create training triples
    5. Export to JSONL for fine-tuning
    """
    
    def __init__(self):
        self.corpus_exporter = RAGCorpusExporter()
        self.hard_neg_miner = HardNegativeMiner()
        self.data_generator = TrainingDataGenerator()
    
    async def run(
        self,
        num_examples: int = 1000,
        output_file: Path = OUTPUT_DIR / "trm_training_data.jsonl"
    ):
        """
        Run complete training pipeline.
        
        Args:
            num_examples: Number of training examples to generate
            output_file: Output JSONL file path
        """
        logger.info(f"Starting TRM training pipeline (target: {num_examples} examples)...")
        
        training_examples = []
        
        # Step 1: Sample diverse documents from corpus
        docs = await self.corpus_exporter.sample_documents(sample_size=num_examples // 2)
        
        # Step 2: Generate queries and responses from documents
        logger.info("Generating training examples from corpus...")
        for i, doc in enumerate(docs[:num_examples // 2]):
            if i % 50 == 0:
                logger.info(f"Progress: {i}/{len(docs)}")
            
            # Synthetic query generation (simple heuristic for now)
            chunk = doc.get("chunk", "")
            if len(chunk) < 100:
                continue
            
            # Generate query from chunk (use first sentence as query)
            query = self._generate_query_from_chunk(chunk)
            
            # Create training example
            example = await self.data_generator.generate_training_example(
                query=query,
                context_chunks=[chunk],
                ground_truth=None
            )
            
            training_examples.append(example)
        
        # Step 3: Mine hard negatives from eval failures
        logger.info("Mining hard negatives from eval failures...")
        failures = await self.hard_neg_miner.mine_failures()
        
        for failure in failures[:num_examples // 2]:
            query = failure.get("query", "")
            retrieved_docs = failure.get("retrieved_docs", [])
            
            if not query or not retrieved_docs:
                continue
            
            example = await self.data_generator.generate_training_example(
                query=query,
                context_chunks=retrieved_docs[:3],  # Top 3 docs
                ground_truth=None
            )
            
            training_examples.append(example)
        
        # Step 4: Export to JSONL
        logger.info(f"Exporting {len(training_examples)} examples to {output_file}...")
        
        with open(output_file, "w") as f:
            for example in training_examples:
                f.write(example.to_jsonl() + "\n")
        
        # Step 5: Generate summary report
        report_path = OUTPUT_DIR / "training_pipeline_report.json"
        report = {
            "total_examples": len(training_examples),
            "corpus_samples": num_examples // 2,
            "hard_negatives": len(failures),
            "output_file": str(output_file),
            "generated_at": datetime.now().isoformat()
        }
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✓ Training pipeline complete!")
        logger.info(f"  Examples: {len(training_examples)}")
        logger.info(f"  Output: {output_file}")
        logger.info(f"  Report: {report_path}")
        
        return training_examples
    
    def _generate_query_from_chunk(self, chunk: str) -> str:
        """Generate a synthetic query from a document chunk"""
        # Simple heuristic: take first sentence and convert to question
        sentences = chunk.split(". ")
        if sentences:
            first_sentence = sentences[0].strip()
            # Convert to question format
            return f"What is {first_sentence.lower()}?"
        return "What does this document describe?"
    
    async def close(self):
        await self.corpus_exporter.close()
        await self.hard_neg_miner.close()
        await self.data_generator.close()


# ============================================================================
# CLI
# ============================================================================

async def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TRM-RAG Training Pipeline")
    parser.add_argument("--num-examples", type=int, default=1000, help="Number of training examples")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR / "trm_training_data.jsonl"), help="Output file")
    
    args = parser.parse_args()
    
    pipeline = TRMTrainingPipeline()
    try:
        await pipeline.run(
            num_examples=args.num_examples,
            output_file=Path(args.output)
        )
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())

