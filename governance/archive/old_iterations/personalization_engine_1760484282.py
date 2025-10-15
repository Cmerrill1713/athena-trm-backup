"""
Personalization Engine v1 - Minimal, Safe, Effective
==================================================

Implements user-adaptive retrieval and tone with privacy protection.

Features:
- Feature vector: preferred_length, tone, citations, opt-out
- Rolling histogram learning from accepted replies
- Soft bias application to rerank scores and prompts
- Privacy: hashed user IDs, 90-day TTL, opt-out respected
"""

import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """User preference profile with rolling statistics."""
    user_hash: str  # Hashed user ID for privacy
    preferred_length: Dict[str, int] = None  # {'short': count, 'medium': count, 'long': count}
    preferred_tone: Dict[str, int] = None    # {'direct': count, 'empathetic': count, 'formal': count}
    citation_preference: Dict[str, int] = None  # {'yes': count, 'no': count}
    total_interactions: int = 0
    last_updated: datetime = None
    opt_out: bool = False

    def __post_init__(self):
        if self.preferred_length is None:
            self.preferred_length = defaultdict(int)
        if self.preferred_tone is None:
            self.preferred_tone = defaultdict(int)
        if self.citation_preference is None:
            self.citation_preference = defaultdict(int)
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def get_length_preference(self) -> str:
        """Get most preferred length."""
        if not self.preferred_length:
            return 'medium'  # Default
        return max(self.preferred_length.items(), key=lambda x: x[1])[0]

    def get_tone_preference(self) -> str:
        """Get most preferred tone."""
        if not self.preferred_tone:
            return 'direct'  # Default
        return max(self.preferred_tone.items(), key=lambda x: x[1])[0]

    def get_citation_preference(self) -> bool:
        """Get citation preference (True for citations)."""
        if not self.citation_preference:
            return False  # Default: no citations
        yes_count = self.citation_preference.get('yes', 0)
        no_count = self.citation_preference.get('no', 0)
        return yes_count > no_count

    def update_from_feedback(self, length: str, tone: str, citations: bool, accepted: bool):
        """Update profile from user feedback on a reply."""
        if not accepted:
            return  # Only learn from accepted replies

        self.preferred_length[length] += 1
        self.preferred_tone[tone] += 1
        self.citation_preference['yes' if citations else 'no'] += 1
        self.total_interactions += 1
        self.last_updated = datetime.now()

@dataclass
class PersonalizationSignal:
    """Personalization hints for reranking and generation."""
    length_hint: str = 'medium'      # 'short', 'medium', 'long'
    tone_hint: str = 'direct'        # 'direct', 'empathetic', 'formal'
    citation_hint: bool = False      # True to prefer cited sources
    confidence: float = 0.0          # 0.0 to 1.0 based on data strength

class PersonalizationEngine:
    """
    Personalization Engine v1 with privacy-first design.

    Features:
    - Hashed user IDs (SHA-256 + salt)
    - 90-day TTL on data
    - Opt-out flag respected
    - Rolling histogram learning
    - Soft bias application (λ=0.15)
    """

    def __init__(self,
                 salt: str = "neuroforge_personalization_salt_2024",
                 ttl_days: int = 90,
                 min_interactions: int = 3,
                 bias_strength: float = 0.15):
        self.salt = salt
        self.ttl_days = ttl_days
        self.min_interactions = min_interactions
        self.bias_strength = bias_strength

        # In-memory storage (in production, use Redis/PostgreSQL)
        self.user_profiles: Dict[str, UserProfile] = {}

        # Cleanup tracking
        self.last_cleanup = datetime.now()

    def _hash_user_id(self, user_id: str) -> str:
        """Create privacy-preserving hash of user ID."""
        salted = f"{user_id}:{self.salt}"
        return hashlib.sha256(salted.encode()).hexdigest()

    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get existing profile or create new one for user."""
        user_hash = self._hash_user_id(user_id)

        if user_hash not in self.user_profiles:
            self.user_profiles[user_hash] = UserProfile(user_hash=user_hash)

        return self.user_profiles[user_hash]

    def record_user_feedback(self,
                           user_id: str,
                           reply_length: str,
                           reply_tone: str,
                           reply_has_citations: bool,
                           user_accepted: bool):
        """
        Record user feedback for learning.

        Only learns from accepted replies to avoid negative reinforcement.
        """
        profile = self.get_or_create_profile(user_id)

        if profile.opt_out:
            return  # Respect opt-out

        profile.update_from_feedback(reply_length, reply_tone, reply_has_citations, user_accepted)

        logger.debug(f"Updated profile for user {user_id[:8]}...: interactions={profile.total_interactions}")

    def get_personalization_signal(self, user_id: str) -> PersonalizationSignal:
        """
        Get personalization signal for user.

        Returns neutral signal if insufficient data or user opted out.
        """
        profile = self.get_or_create_profile(user_id)

        if profile.opt_out or profile.total_interactions < self.min_interactions:
            return PersonalizationSignal()  # Neutral defaults

        # Calculate confidence based on data strength
        confidence = min(1.0, profile.total_interactions / 10.0)  # Max confidence at 10+ interactions

        return PersonalizationSignal(
            length_hint=profile.get_length_preference(),
            tone_hint=profile.get_tone_preference(),
            citation_hint=profile.get_citation_preference(),
            confidence=confidence
        )

    def apply_personalization_bias(self,
                                 documents: List[Any],
                                 user_signal: PersonalizationSignal) -> List[Any]:
        """
        Apply soft bias to document reranking scores.

        Uses λ=0.15 bias towards user's citation preference.
        Documents with matching citation style get slight boost.
        """
        if not user_signal.confidence > 0:
            return documents  # No bias if low confidence

        biased_docs = []
        for doc in documents:
            bias = 0.0

            # Citation preference bias
            doc_has_citations = self._document_has_citations(doc)
            if doc_has_citations == user_signal.citation_hint:
                bias += self.bias_strength * user_signal.confidence

            # Apply bias to rerank score (assuming document has rerank_score attribute)
            if hasattr(doc, 'rerank_score'):
                doc.rerank_score += bias

            biased_docs.append(doc)

        return biased_docs

    def generate_personalized_prompt_hints(self, user_signal: PersonalizationSignal) -> str:
        """
        Generate soft prompt hints based on user preferences.

        Returns system message hints for length, tone, and citations.
        """
        if user_signal.confidence < 0.5:
            return ""  # Don't add hints if confidence too low

        hints = []

        # Length hint
        if user_signal.length_hint == 'short':
            hints.append("Keep the response concise and to the point.")
        elif user_signal.length_hint == 'long':
            hints.append("Provide a comprehensive, detailed response.")

        # Tone hint
        if user_signal.tone_hint == 'empathetic':
            hints.append("Use a warm, understanding tone.")
        elif user_signal.tone_hint == 'formal':
            hints.append("Use a professional, formal tone.")

        # Citation hint
        if user_signal.citation_hint:
            hints.append("Include references to sources where appropriate.")
        else:
            hints.append("Focus on direct answers without extensive citations.")

        if hints:
            return " ".join(hints)
        return ""

    def set_user_opt_out(self, user_id: str, opt_out: bool):
        """Set user's opt-out preference."""
        profile = self.get_or_create_profile(user_id)
        profile.opt_out = opt_out

        if opt_out:
            logger.info(f"User {user_id[:8]}... opted out of personalization")

    def cleanup_expired_profiles(self):
        """Remove profiles older than TTL."""
        cutoff_date = datetime.now() - timedelta(days=self.ttl_days)
        expired_hashes = []

        for user_hash, profile in self.user_profiles.items():
            if profile.last_updated < cutoff_date:
                expired_hashes.append(user_hash)

        for user_hash in expired_hashes:
            del self.user_profiles[user_hash]

        if expired_hashes:
            logger.info(f"Cleaned up {len(expired_hashes)} expired user profiles")

        self.last_cleanup = datetime.now()

    def _document_has_citations(self, doc: Any) -> bool:
        """
        Determine if document has citations.

        Simple heuristic: check for common citation patterns.
        In production, this would use more sophisticated detection.
        """
        if not hasattr(doc, 'content'):
            return False

        content = doc.content.lower()

        # Look for citation patterns
        citation_indicators = [
            '[', ']', '(', ')', 'et al', 'ibid', 'op. cit',
            'according to', 'source:', 'reference:', 'cited in'
        ]

        citation_score = sum(1 for indicator in citation_indicators if indicator in content)
        return citation_score >= 2  # Require multiple indicators

    def get_stats(self) -> Dict:
        """Get personalization engine statistics."""
        total_users = len(self.user_profiles)
        active_users = sum(1 for p in self.user_profiles.values()
                          if p.total_interactions >= self.min_interactions and not p.opt_out)
        opted_out_users = sum(1 for p in self.user_profiles.values() if p.opt_out)
        total_interactions = sum(p.total_interactions for p in self.user_profiles.values())

        return {
            'total_users': total_users,
            'active_users': active_users,
            'opted_out_users': opted_out_users,
            'total_interactions': total_interactions,
            'avg_interactions_per_active_user': total_interactions / max(active_users, 1),
            'last_cleanup': self.last_cleanup.isoformat()
        }

    def save_state(self, filepath: str):
        """Save personalization state to JSON file."""
        # Convert defaultdicts to regular dicts for serialization
        serializable_profiles = {}
        for user_hash, profile in self.user_profiles.items():
            profile_dict = {
                'user_hash': profile.user_hash,
                'preferred_length': dict(profile.preferred_length),
                'preferred_tone': dict(profile.preferred_tone),
                'citation_preference': dict(profile.citation_preference),
                'total_interactions': profile.total_interactions,
                'last_updated': profile.last_updated.isoformat(),
                'opt_out': profile.opt_out
            }
            serializable_profiles[user_hash] = profile_dict

        state = {
            'config': {
                'salt': self.salt,
                'ttl_days': self.ttl_days,
                'min_interactions': self.min_interactions,
                'bias_strength': self.bias_strength
            },
            'profiles': serializable_profiles,
            'last_cleanup': self.last_cleanup.isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, filepath: str):
        """Load personalization state from JSON file."""
        with open(filepath, 'r') as f:
            state = json.load(f)

        # Load configuration
        config = state.get('config', {})
        self.salt = config.get('salt', self.salt)
        self.ttl_days = config.get('ttl_days', self.ttl_days)
        self.min_interactions = config.get('min_interactions', self.min_interactions)
        self.bias_strength = config.get('bias_strength', self.bias_strength)

        # Load profiles
        self.user_profiles = {}
        for user_hash, profile_data in state.get('profiles', {}).items():
            profile = UserProfile(
                user_hash=user_hash,
                preferred_length=defaultdict(int, profile_data['preferred_length']),
                preferred_tone=defaultdict(int, profile_data['preferred_tone']),
                citation_preference=defaultdict(int, profile_data['citation_preference']),
                total_interactions=profile_data['total_interactions'],
                last_updated=datetime.fromisoformat(profile_data['last_updated']),
                opt_out=profile_data['opt_out']
            )
            self.user_profiles[user_hash] = profile

        self.last_cleanup = datetime.fromisoformat(state['last_cleanup'])
        logger.info(f"Loaded personalization state with {len(self.user_profiles)} user profiles")


# Global personalization engine instance
_personalization = None

def get_personalization_engine() -> PersonalizationEngine:
    """Get or create global personalization engine instance."""
    global _personalization
    if _personalization is None:
        _personalization = PersonalizationEngine()
    return _personalization
