#!/usr/bin/env python3
"""
Paper Analyzer Agent - Extract Implementation Details from Research Papers
=========================================================================
Analyzes paper abstracts, identifies key algorithms, and generates
implementation specifications for the VM Coding Agent
"""

import logging
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AlgorithmSpec:
    """Specification for implementing an algorithm"""
    name: str
    description: str
    input_format: str
    output_format: str
    key_steps: List[str]
    complexity: str  # "simple", "medium", "complex"
    dependencies: List[str]
    test_criteria: List[str]


@dataclass
class ImplementationPlan:
    """Complete implementation plan for a paper"""
    paper_id: str
    paper_title: str
    algorithms: List[AlgorithmSpec]
    programming_language: str = "python"  # Default to Python
    estimated_complexity: str = "medium"
    test_strategy: str = "unit_and_integration"
    deployment_target: str = "local_service"
    
    # Generated code structure
    project_structure: Optional[Dict[str, Any]] = None
    dependencies: Optional[List[str]] = None
    entry_point: Optional[str] = None


class PaperAnalyzer:
    """Analyzes research papers and generates implementation plans"""
    
    def __init__(self):
        self.llm_available = True  # Will use Athena for analysis
        
        # Algorithm complexity indicators
        self.complexity_indicators = {
            "simple": ["baseline", "simple", "naive", "basic"],
            "medium": ["improved", "enhanced", "optimized", "efficient"],
            "complex": ["novel", "state-of-the-art", "advanced", "hybrid", "multi-stage"]
        }
    
    async def analyze_paper(self, paper_data: Dict[str, Any]) -> ImplementationPlan:
        """
        Analyze a research paper and generate implementation plan
        
        Args:
            paper_data: Research paper metadata (from ResearchHunter)
            
        Returns:
            Complete implementation plan
        """
        paper_id = paper_data.get("paper_id", "unknown")
        title = paper_data.get("title", "")
        abstract = paper_data.get("abstract", "")
        
        logger.info(f"📊 Analyzing paper: {title}")
        
        # Extract algorithms
        algorithms = await self._extract_algorithms(title, abstract)
        
        # Determine complexity
        complexity = self._estimate_complexity(title, abstract)
        
        # Generate implementation plan
        plan = ImplementationPlan(
            paper_id=paper_id,
            paper_title=title,
            algorithms=algorithms,
            estimated_complexity=complexity,
            programming_language=self._select_language(algorithms),
            test_strategy=self._plan_test_strategy(algorithms, complexity)
        )
        
        # Generate project structure
        plan.project_structure = self._generate_project_structure(plan)
        plan.dependencies = self._identify_dependencies(algorithms)
        plan.entry_point = self._determine_entry_point(plan)
        
        logger.info(f"✅ Generated implementation plan with {len(algorithms)} algorithms")
        
        return plan
    
    async def _extract_algorithms(self, title: str, abstract: str) -> List[AlgorithmSpec]:
        """Extract algorithm specifications from paper text"""
        
        algorithms = []
        text = f"{title} {abstract}".lower()
        
        # Pattern matching for common algorithm descriptions
        patterns = {
            "bandit": r"(thompson sampling|ucb|epsilon-greedy|multi-armed bandit)",
            "optimization": r"(gradient descent|adam|sgd|particle swarm|genetic algorithm)",
            "neural": r"(neural network|lstm|transformer|attention mechanism|gru)",
            "reinforcement": r"(q-learning|policy gradient|actor-critic|dqn|ppo)",
            "search": r"(vector search|semantic search|knn|faiss|approximate nearest)",
        }
        
        for algo_type, pattern in patterns.items():
            matches = re.findall(pattern, text)
            for match in set(matches):
                algo_name = match.capitalize()
                
                # Create spec
                spec = AlgorithmSpec(
                    name=algo_name,
                    description=f"Implementation of {algo_name} from research paper",
                    input_format="Dict[str, Any]",
                    output_format="Dict[str, Any]",
                    key_steps=self._generate_key_steps(algo_name, text),
                    complexity=self._estimate_algo_complexity(text),
                    dependencies=self._suggest_dependencies(algo_name),
                    test_criteria=self._generate_test_criteria(algo_name)
                )
                
                algorithms.append(spec)
        
        # If no algorithms detected, create generic one
        if not algorithms:
            algorithms.append(AlgorithmSpec(
                name="Generic Implementation",
                description=f"Implementation based on: {title[:100]}",
                input_format="Dict[str, Any]",
                output_format="Dict[str, Any]",
                key_steps=["Parse input", "Process data", "Return result"],
                complexity="medium",
                dependencies=["numpy", "scipy"],
                test_criteria=["Validate input/output", "Check performance"]
            ))
        
        return algorithms
    
    def _generate_key_steps(self, algo_name: str, context: str) -> List[str]:
        """Generate implementation steps for an algorithm"""
        
        # Generic steps based on algorithm type
        steps_map = {
            "thompson": [
                "Initialize beta distributions for each arm",
                "Sample from distributions to select arm",
                "Execute selected arm and observe reward",
                "Update distribution parameters",
                "Persist state for next iteration"
            ],
            "gradient": [
                "Initialize parameters",
                "Compute forward pass",
                "Calculate loss/gradient",
                "Update parameters",
                "Check convergence"
            ],
            "neural": [
                "Define network architecture",
                "Initialize weights",
                "Forward propagation",
                "Backward propagation",
                "Update weights via optimizer"
            ],
            "search": [
                "Build/load index",
                "Encode query",
                "Compute similarity scores",
                "Rank results",
                "Return top-k matches"
            ]
        }
        
        # Match algorithm name to steps
        for key, steps in steps_map.items():
            if key in algo_name.lower():
                return steps
        
        # Generic fallback
        return [
            "Parse and validate input",
            "Execute core algorithm logic",
            "Format and return output",
            "Log metrics and telemetry"
        ]
    
    def _estimate_complexity(self, title: str, abstract: str) -> str:
        """Estimate implementation complexity"""
        text = f"{title} {abstract}".lower()
        
        scores = {"simple": 0, "medium": 0, "complex": 0}
        
        for complexity, indicators in self.complexity_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    scores[complexity] += 1
        
        # Return highest scoring complexity
        if scores["complex"] > 0:
            return "complex"
        elif scores["medium"] > scores["simple"]:
            return "medium"
        else:
            return "simple"
    
    def _estimate_algo_complexity(self, text: str) -> str:
        """Estimate specific algorithm complexity"""
        if "novel" in text or "state-of-the-art" in text:
            return "complex"
        elif "improved" in text or "optimized" in text:
            return "medium"
        return "simple"
    
    def _select_language(self, algorithms: List[AlgorithmSpec]) -> str:
        """Select best programming language for implementation"""
        
        # Check algorithm types
        algo_names = " ".join([a.name.lower() for a in algorithms])
        
        if "neural" in algo_names or "deep learning" in algo_names:
            return "python"  # PyTorch/MLX
        elif "web" in algo_names or "service" in algo_names:
            return "go"  # Fast web services
        elif "system" in algo_names or "performance" in algo_names:
            return "rust"  # High performance
        
        return "python"  # Default
    
    def _plan_test_strategy(self, algorithms: List[AlgorithmSpec], complexity: str) -> str:
        """Plan testing strategy based on algorithms"""
        
        if complexity == "complex":
            return "unit_integration_performance"
        elif complexity == "medium":
            return "unit_and_integration"
        else:
            return "unit_tests"
    
    def _generate_project_structure(self, plan: ImplementationPlan) -> Dict[str, Any]:
        """Generate project directory structure"""
        
        structure = {
            "src": {
                "main": f"main.{self._get_extension(plan.programming_language)}",
                "algorithms": {
                    f"{algo.name.lower().replace(' ', '_')}.{self._get_extension(plan.programming_language)}": None
                    for algo in plan.algorithms
                },
                "utils": {
                    f"helpers.{self._get_extension(plan.programming_language)}": None
                }
            },
            "tests": {
                f"test_{algo.name.lower().replace(' ', '_')}.{self._get_extension(plan.programming_language)}": None
                for algo in plan.algorithms
            },
            "README.md": None,
            "requirements.txt": None if plan.programming_language == "python" else None,
        }
        
        return structure
    
    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            "python": "py",
            "rust": "rs",
            "go": "go",
            "typescript": "ts",
            "javascript": "js",
        }
        return extensions.get(language, "py")
    
    def _identify_dependencies(self, algorithms: List[AlgorithmSpec]) -> List[str]:
        """Identify required dependencies"""
        
        deps = set()
        
        for algo in algorithms:
            deps.update(algo.dependencies)
        
        # Add common dependencies
        deps.update(["pydantic", "httpx", "pytest"])
        
        return sorted(list(deps))
    
    def _suggest_dependencies(self, algo_name: str) -> List[str]:
        """Suggest dependencies for an algorithm"""
        
        deps_map = {
            "thompson": ["numpy", "scipy"],
            "neural": ["torch", "mlx"],
            "gradient": ["numpy", "scipy", "torch"],
            "search": ["numpy", "faiss-cpu"],
            "vector": ["numpy", "sentence-transformers"],
        }
        
        for key, deps in deps_map.items():
            if key in algo_name.lower():
                return deps
        
        return ["numpy"]
    
    def _generate_test_criteria(self, algo_name: str) -> List[str]:
        """Generate test criteria for an algorithm"""
        
        return [
            f"Verify {algo_name} produces valid output format",
            f"Test {algo_name} with edge cases",
            f"Benchmark {algo_name} performance",
            f"Validate {algo_name} against known examples",
            "Check error handling and recovery"
        ]
    
    def _determine_entry_point(self, plan: ImplementationPlan) -> str:
        """Determine main entry point for the implementation"""
        
        ext = self._get_extension(plan.programming_language)
        return f"src/main.{ext}"


# Global instance
_analyzer: Optional[PaperAnalyzer] = None

def get_paper_analyzer() -> PaperAnalyzer:
    """Get global paper analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = PaperAnalyzer()
    return _analyzer

