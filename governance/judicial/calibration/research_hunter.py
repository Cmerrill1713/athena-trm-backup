#!/usr/bin/env python3
"""
Research Hunter Agent - Autonomous Paper Discovery & Analysis
============================================================
Monitors arXiv, Papers with Code, and other sources for new research
Scores relevance, extracts algorithms, and queues for implementation
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import xml.etree.ElementTree as ET

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ResearchPaper:
    """Research paper metadata"""
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    published: str
    url: str
    source: str  # arxiv, papers_with_code, etc.
    categories: List[str]
    relevance_score: float = 0.0
    has_code: bool = False
    code_url: Optional[str] = None
    algorithms: List[str] = None

    def __post_init__(self):
        if self.algorithms is None:
            self.algorithms = []


@dataclass
class ImplementationTask:
    """Task for implementing a research paper"""
    task_id: str
    paper: ResearchPaper
    priority: float
    status: str = "pending"  # pending, implementing, testing, completed, failed
    created_at: str = None
    completed_at: Optional[str] = None
    test_results: Optional[Dict] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


class ResearchHunter:
    """Autonomous research paper discovery and analysis"""

    def __init__(self):
        self.arxiv_base = "https://export.arxiv.org/api/query"  # Use HTTPS
        self.pwc_base = "https://paperswithcode.com/api/v1"

        # Relevance keywords (weighted by importance)
        self.relevance_keywords = {
            # High priority (weight: 2.0)
            "multi-armed bandit": 2.0,
            "thompson sampling": 2.0,
            "reinforcement learning": 2.0,
            "prompt engineering": 2.0,
            "agent orchestration": 2.0,
            "recursive reasoning": 2.0,
            "self-improving": 2.0,
            "autonomous agent": 2.0,

            # Medium priority (weight: 1.5)
            "neural network": 1.5,
            "fine-tuning": 1.5,
            "parameter-efficient": 1.5,
            "retrieval augmented": 1.5,
            "code generation": 1.5,
            "test generation": 1.5,
            "model selection": 1.5,

            # Lower priority (weight: 1.0)
            "machine learning": 1.0,
            "deep learning": 1.0,
            "natural language": 1.0,
            "optimization": 1.0,
        }

        # Categories to monitor
        self.arxiv_categories = [
            "cs.AI",  # Artificial Intelligence
            "cs.LG",  # Machine Learning
            "cs.CL",  # Computation and Language
            "cs.NE",  # Neural and Evolutionary Computing
            "cs.SE",  # Software Engineering
        ]

        self.discovered_papers: List[ResearchPaper] = []
        self.implementation_queue: List[ImplementationTask] = []

    async def hunt_daily(self, lookback_days: int = 1) -> List[ResearchPaper]:
        """
        Daily research hunt - find new relevant papers

        Args:
            lookback_days: How many days back to search

        Returns:
            List of discovered papers sorted by relevance
        """
        logger.info(f"🔍 Starting daily research hunt (lookback: {lookback_days} days)")

        discovered = []

        # Search arXiv
        arxiv_papers = await self._search_arxiv(lookback_days)
        discovered.extend(arxiv_papers)

        # Search Papers with Code
        # pwc_papers = await self._search_papers_with_code(lookback_days)
        # discovered.extend(pwc_papers)

        # Score relevance
        for paper in discovered:
            paper.relevance_score = self._calculate_relevance(paper)

        # Filter and sort
        relevant_papers = [p for p in discovered if p.relevance_score > 0.5]
        relevant_papers.sort(key=lambda p: p.relevance_score, reverse=True)

        self.discovered_papers.extend(relevant_papers)

        logger.info(f"✅ Discovered {len(relevant_papers)} relevant papers (from {len(discovered)} total)")

        return relevant_papers

    async def _search_arxiv(self, lookback_days: int) -> List[ResearchPaper]:
        """Search arXiv for recent papers"""

        papers = []
        date_threshold = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y%m%d0000")

        # Search by relevant keywords instead of categories (more results)
        search_terms = [
            "multi-armed bandit",
            "thompson sampling",
            "reinforcement learning agent",
            "prompt engineering",
            "autonomous agent"
        ]

        for search_term in search_terms[:2]:  # Limit to avoid rate limits
            try:
                query = f"all:{search_term.replace(' ', '+')}"
                params = {
                    "search_query": query,
                    "start": 0,
                    "max_results": 20,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending"
                }

                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(self.arxiv_base, params=params)

                    if response.status_code != 200:
                        logger.warning(f"arXiv search failed for '{search_term}': {response.status_code}")
                        continue

                    # Parse XML response
                    root = ET.fromstring(response.text)
                    ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}

                    current_count = len(papers)

                    for entry in root.findall('atom:entry', ns):
                        try:
                            paper = self._parse_arxiv_entry(entry, ns, search_term)
                            if paper:
                                papers.append(paper)
                        except Exception as e:
                            logger.warning(f"Failed to parse arXiv entry: {e}")
                            continue

                new_papers = len(papers) - current_count
                logger.info(f"📄 Found {new_papers} papers for '{search_term}'")

            except Exception as e:
                logger.error(f"Error searching arXiv for '{search_term}': {e}")
                continue

        logger.info(f"📚 Total papers found across all searches: {len(papers)}")
        return papers

    def _parse_arxiv_entry(self, entry, namespaces, category: str) -> Optional[ResearchPaper]:
        """Parse arXiv XML entry into ResearchPaper"""

        try:
            title_elem = entry.find('atom:title', namespaces)
            summary_elem = entry.find('atom:summary', namespaces)
            published_elem = entry.find('atom:published', namespaces)
            id_elem = entry.find('atom:id', namespaces)

            if not all([title_elem, summary_elem, published_elem, id_elem]):
                return None

            title = title_elem.text.strip()
            abstract = summary_elem.text.strip()
            published = published_elem.text.strip()
            paper_url = id_elem.text.strip()
            paper_id = paper_url.split('/')[-1]

            # Extract authors
            authors = []
            for author in entry.findall('atom:author', namespaces):
                name_elem = author.find('atom:name', namespaces)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())

            # Extract categories
            categories = [category]
            for cat_elem in entry.findall('atom:category', namespaces):
                term = cat_elem.get('term')
                if term and term not in categories:
                    categories.append(term)

            return ResearchPaper(
                paper_id=paper_id,
                title=title,
                authors=authors,
                abstract=abstract,
                published=published,
                url=paper_url,
                source="arxiv",
                categories=categories
            )

        except Exception as e:
            logger.warning(f"Error parsing arXiv entry: {e}")
            return None

    def _calculate_relevance(self, paper: ResearchPaper) -> float:
        """
        Calculate paper relevance score (0.0 - 1.0)

        Scoring factors:
        - Keyword matches in title/abstract (60%)
        - Has implementation code available (20%)
        - Recent publication date (10%)
        - Category match (10%)
        """
        score = 0.0

        # Combine title and abstract for keyword matching
        text = f"{paper.title} {paper.abstract}".lower()

        # Keyword scoring (max 0.6)
        keyword_score = 0.0
        keyword_count = 0

        for keyword, weight in self.relevance_keywords.items():
            if keyword.lower() in text:
                keyword_score += weight
                keyword_count += 1

        # Normalize to 0-0.6 range
        if keyword_count > 0:
            keyword_score = min(0.6, (keyword_score / keyword_count) * 0.3)

        score += keyword_score

        # Code availability (0.2)
        if paper.has_code:
            score += 0.2

        # Recency (0.1) - papers from last 7 days get full points
        try:
            pub_date = datetime.fromisoformat(paper.published.replace('Z', '+00:00'))
            days_old = (datetime.utcnow().replace(tzinfo=pub_date.tzinfo) - pub_date).days
            recency_score = max(0, 1 - (days_old / 30)) * 0.1
            score += recency_score
        except:
            pass

        # Category relevance (0.1)
        relevant_cats = {"cs.AI", "cs.LG", "cs.NE"}
        if any(cat in relevant_cats for cat in paper.categories):
            score += 0.1

        return min(1.0, score)

    def extract_algorithms(self, paper: ResearchPaper) -> List[str]:
        """
        Extract algorithm names and techniques from paper abstract/title

        Returns:
            List of identified algorithms
        """
        algorithms = []
        text = f"{paper.title} {paper.abstract}"

        # Common algorithm patterns
        algorithm_patterns = [
            r'(\w+)\s+algorithm',
            r'(\w+)\s+sampling',
            r'(\w+)\s+optimization',
            r'(\w+)\s+learning',
            r'(\w+)\s+network',
            r'(\w+)\s+approach',
        ]

        for pattern in algorithm_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) > 3:  # Ignore very short words
                    algorithms.append(match.capitalize())

        # Deduplicate
        paper.algorithms = list(set(algorithms))

        return paper.algorithms

    async def queue_for_implementation(self, paper: ResearchPaper) -> ImplementationTask:
        """
        Queue a paper for autonomous implementation

        Args:
            paper: Research paper to implement

        Returns:
            Implementation task
        """
        # Extract algorithms first
        self.extract_algorithms(paper)

        # Calculate priority (0.0 - 1.0)
        priority = paper.relevance_score

        # Boost priority if code is available
        if paper.has_code:
            priority = min(1.0, priority * 1.2)

        # Create task
        task = ImplementationTask(
            task_id=f"impl-{paper.paper_id}",
            paper=paper,
            priority=priority
        )

        self.implementation_queue.append(task)
        self.implementation_queue.sort(key=lambda t: t.priority, reverse=True)

        logger.info(f"📋 Queued paper for implementation: {paper.title} (priority: {priority:.2f})")

        return task

    async def get_top_papers(self, limit: int = 10) -> List[ResearchPaper]:
        """Get top N papers by relevance score"""
        sorted_papers = sorted(self.discovered_papers, key=lambda p: p.relevance_score, reverse=True)
        return sorted_papers[:limit]

    async def get_implementation_queue(self) -> List[ImplementationTask]:
        """Get current implementation queue"""
        return self.implementation_queue

    def get_stats(self) -> Dict[str, Any]:
        """Get research hunter statistics"""
        return {
            "total_papers_discovered": len(self.discovered_papers),
            "papers_queued": len(self.implementation_queue),
            "avg_relevance_score": sum(p.relevance_score for p in self.discovered_papers) / max(1, len(self.discovered_papers)),
            "papers_with_code": sum(1 for p in self.discovered_papers if p.has_code),
            "top_categories": self._get_top_categories(),
        }

    def _get_top_categories(self, limit: int = 5) -> List[Dict[str, int]]:
        """Get most common paper categories"""
        from collections import Counter
        all_cats = []
        for paper in self.discovered_papers:
            all_cats.extend(paper.categories)

        counts = Counter(all_cats)
        return [{"category": cat, "count": count} for cat, count in counts.most_common(limit)]


# Global instance
_hunter: Optional[ResearchHunter] = None

def get_research_hunter() -> ResearchHunter:
    """Get global research hunter instance"""
    global _hunter
    if _hunter is None:
        _hunter = ResearchHunter()
    return _hunter
