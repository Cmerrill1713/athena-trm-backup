#!/usr/bin/env python3
"""
Personalization v1: Lightweight user preference learning
Learns and applies user preferences for response length, tone, and evidence level.
"""

import os
from typing import Any, Dict

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "dbname=universal_ai_tools user=postgres password=postgres host=athena-postgres port=5432")

class UserPersonalization:
    """Lightweight user preference management."""

    def __init__(self):
        self.db_available = self._check_db_connection()

    def _check_db_connection(self) -> bool:
        """Check if database is available."""
        try:
            import psycopg2
            psycopg2.connect(DATABASE_URL)
            return True
        except:
            return False

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user preference profile, creating default if needed."""
        if not self.db_available:
            return self._default_profile()

        try:
            import psycopg2
            with psycopg2.connect(DATABASE_URL) as conn, conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_profiles (user_id) VALUES (%s)
                    ON CONFLICT (user_id) DO NOTHING
                """, (user_id,))

                cur.execute("""
                    SELECT preferred_length, preferred_tone, evidence_appetite,
                           interaction_count, last_updated
                    FROM user_profiles WHERE user_id = %s
                """, (user_id,))

                row = cur.fetchone()
                if row:
                    return {
                        "preferred_length": row[0],
                        "preferred_tone": row[1],
                        "evidence_appetite": row[2],
                        "interaction_count": row[3],
                        "last_updated": row[4].isoformat() if row[4] else None
                    }
        except Exception as e:
            print(f"Failed to get user profile: {e}")

        return self._default_profile()

    def _default_profile(self) -> Dict[str, Any]:
        """Return default user profile."""
        return {
            "preferred_length": "medium",
            "preferred_tone": "balanced",
            "evidence_appetite": "moderate",
            "interaction_count": 0,
            "last_updated": None
        }

    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences based on explicit or implicit feedback."""
        if not self.db_available:
            return False

        try:
            import psycopg2
            with psycopg2.connect(DATABASE_URL) as conn, conn.cursor() as cur:
                # Update profile
                cur.execute("""
                    UPDATE user_profiles SET
                        preferred_length = COALESCE(%s, preferred_length),
                        preferred_tone = COALESCE(%s, preferred_tone),
                        evidence_appetite = COALESCE(%s, evidence_appetite),
                        interaction_count = interaction_count + 1,
                        last_updated = now()
                    WHERE user_id = %s
                """, (
                    preferences.get("preferred_length"),
                    preferences.get("preferred_tone"),
                    preferences.get("evidence_appetite"),
                    user_id
                ))

                conn.commit()
                return True
        except Exception as e:
            print(f"Failed to update user preferences: {e}")
            return False

    def record_preference_signal(self, user_id: str, interaction_id: str,
                               signal_type: str, signal_value: str,
                               confidence: float = 1.0) -> bool:
        """Record a preference learning signal."""
        if not self.db_available:
            return False

        try:
            import psycopg2
            with psycopg2.connect(DATABASE_URL) as conn, conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO preference_signals
                    (user_id, interaction_id, signal_type, signal_value, confidence)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, interaction_id, signal_type, signal_value, confidence))

                conn.commit()
                return True
        except Exception as e:
            print(f"Failed to record preference signal: {e}")
            return False

    def learn_from_feedback(self, user_id: str, interaction_id: str,
                          feedback: Dict[str, Any]) -> None:
        """Learn user preferences from feedback signals."""
        signals = []

        # Length preference learning
        if "response_length" in feedback:
            length = feedback["response_length"]
            if length == "too_short":
                signals.append(("length_feedback", "long"))
            elif length == "too_long":
                signals.append(("length_feedback", "short"))
            elif length == "just_right":
                signals.append(("length_feedback", "medium"))

        # Tone preference learning
        if "response_tone" in feedback:
            tone = feedback["response_tone"]
            if tone in ["too_direct", "too_formal", "too_casual"]:
                # Map to preferred tone
                tone_map = {
                    "too_direct": "empathetic",
                    "too_formal": "casual",
                    "too_casual": "formal"
                }
                signals.append(("tone_feedback", tone_map.get(tone, "balanced")))
            elif tone == "perfect":
                signals.append(("tone_feedback", "balanced"))

        # Evidence appetite learning
        if "evidence_level" in feedback:
            evidence = feedback["evidence_level"]
            if evidence == "too_much":
                signals.append(("evidence_feedback", "minimal"))
            elif evidence == "too_little":
                signals.append(("evidence_feedback", "comprehensive"))
            elif evidence == "just_right":
                signals.append(("evidence_feedback", "moderate"))

        # Record signals and update profile
        for signal_type, signal_value in signals:
            self.record_preference_signal(user_id, interaction_id, signal_type, signal_value)

        # Update profile with learned preferences
        if signals:
            preferences = self._aggregate_recent_signals(user_id)
            self.update_user_preferences(user_id, preferences)

    def _aggregate_recent_signals(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Aggregate recent preference signals into profile updates."""
        if not self.db_available:
            return {}

        try:
            from collections import defaultdict

            import psycopg2

            with psycopg2.connect(DATABASE_URL) as conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT signal_type, signal_value, confidence
                    FROM preference_signals
                    WHERE user_id = %s AND ts > now() - interval '%s days'
                    ORDER BY ts DESC
                    LIMIT 50
                """, (user_id, days))

                signals = defaultdict(list)
                for signal_type, signal_value, confidence in cur.fetchall():
                    signals[signal_type].append((signal_value, confidence))

                # Aggregate by taking weighted mode
                preferences = {}
                for signal_type, values in signals.items():
                    if signal_type == "length_feedback":
                        preferences["preferred_length"] = self._weighted_mode(values)
                    elif signal_type == "tone_feedback":
                        preferences["preferred_tone"] = self._weighted_mode(values)
                    elif signal_type == "evidence_feedback":
                        preferences["evidence_appetite"] = self._weighted_mode(values)

                return preferences
        except Exception as e:
            print(f"Failed to aggregate signals: {e}")
            return {}

    def _weighted_mode(self, values: list) -> str:
        """Find weighted mode from (value, weight) pairs."""
        from collections import Counter
        weighted_counts = Counter()

        for value, weight in values:
            weighted_counts[value] += weight

        return weighted_counts.most_common(1)[0][0] if weighted_counts else "medium"

# Global personalization instance
personalization = UserPersonalization()

def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """Get user preferences for response personalization."""
    return personalization.get_user_profile(user_id)

def apply_personalization_to_prompt(base_prompt: str, user_preferences: Dict[str, Any]) -> str:
    """Apply user preferences to prompt."""
    preferences = user_preferences or {}

    # Length preference
    length_pref = preferences.get("preferred_length", "medium")
    if length_pref == "short":
        length_instruction = "Keep the response concise and to the point."
    elif length_pref == "long":
        length_instruction = "Provide a comprehensive, detailed response."
    else:  # medium
        length_instruction = "Provide a balanced, moderately detailed response."

    # Tone preference
    tone_pref = preferences.get("preferred_tone", "balanced")
    if tone_pref == "direct":
        tone_instruction = "Be direct and straightforward."
    elif tone_pref == "empathetic":
        tone_instruction = "Be empathetic and understanding."
    elif tone_pref == "formal":
        tone_instruction = "Use formal, professional language."
    elif tone_pref == "casual":
        tone_instruction = "Use casual, conversational language."
    else:  # balanced
        tone_instruction = "Use balanced, natural language."

    # Evidence appetite
    evidence_pref = preferences.get("evidence_appetite", "moderate")
    if evidence_pref == "minimal":
        evidence_instruction = "Minimize citations and references."
    elif evidence_pref == "comprehensive":
        evidence_instruction = "Include extensive citations and evidence."
    else:  # moderate
        evidence_instruction = "Include relevant citations and evidence as appropriate."

    # Combine instructions
    personalization_prompt = f"""
User preferences for this response:
- Length: {length_instruction}
- Tone: {tone_instruction}
- Evidence: {evidence_instruction}

Please adapt your response accordingly.
"""

    return base_prompt + personalization_prompt

def personalize_rag_selection(candidates: list, user_preferences: Dict[str, Any]) -> list:
    """Apply soft personalization to RAG document selection."""
    if not user_preferences or not candidates:
        return candidates

    evidence_pref = user_preferences.get("evidence_appetite", "moderate")

    # Soft preference for document types based on evidence appetite
    if evidence_pref == "minimal":
        # Slightly prefer shorter, more direct documents
        for candidate in candidates:
            text = candidate.get("text", "")
            # Small scoring boost for concise documents
            if len(text.split()) < 200:
                candidate["personalization_boost"] = 0.05
            else:
                candidate["personalization_boost"] = 0.0

    elif evidence_pref == "comprehensive":
        # Slightly prefer longer, more detailed documents
        for candidate in candidates:
            text = candidate.get("text", "")
            # Small scoring boost for detailed documents
            if len(text.split()) > 400:
                candidate["personalization_boost"] = 0.05
            else:
                candidate["personalization_boost"] = 0.0

    # Apply boosts to rerank scores (very soft influence)
    for candidate in candidates:
        boost = candidate.get("personalization_boost", 0.0)
        if "rerank" in candidate:
            candidate["rerank"] = candidate["rerank"] * (1 + boost)

    return candidates

if __name__ == "__main__":
    # Test personalization
    print("🧪 Testing Personalization v1")

    # Test default profile
    profile = get_user_preferences("test_user")
    print(f"Default profile: {profile}")

    # Test prompt personalization
    base_prompt = "Answer this question:"
    personalized_prompt = apply_personalization_to_prompt(base_prompt, profile)
    print(f"Personalized prompt length: {len(personalized_prompt)} chars")

    print("✅ Personalization v1 ready!")
