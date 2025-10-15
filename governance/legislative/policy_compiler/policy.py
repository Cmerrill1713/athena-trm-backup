# Bandit Prompt Optimization Policy
# Thompson Sampling implementation for prompt variant selection

import os
from contextlib import contextmanager
from typing import Dict, List, Optional

import numpy as np
import psycopg2
import psycopg2.extras

# Database connection string
DSN = os.getenv(
    "DATABASE_URL",
    "dbname=universal_ai_tools user=postgres password=postgres host=athena-postgres port=5432"
)


class BanditPolicy:
    """
    Thompson Sampling bandit for prompt variant optimization.

    Selects prompt variants based on historical performance and updates
    statistics based on user feedback.
    """

    def __init__(self, dsn: str = DSN):
        self.dsn = dsn
        self._ensure_connection()

    def _ensure_connection(self):
        """Ensure database connection is available."""
        try:
            self.conn = psycopg2.connect(self.dsn)
            self.conn.autocommit = True
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            self.conn = None

    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursors."""
        if not self.conn:
            self._ensure_connection()
        if not self.conn:
            raise RuntimeError("Database connection unavailable")

        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cursor
        finally:
            cursor.close()

    def fetch_stats(self) -> List[Dict]:
        """Fetch current bandit statistics for active variants."""
        with self._get_cursor() as cur:
            cur.execute("""
                SELECT
                    bs.variant_name,
                    bs.trials,
                    bs.wins,
                    pv.template,
                    pv.active
                FROM bandit_stats bs
                JOIN prompt_variants pv ON pv.name = bs.variant_name
                WHERE pv.active = TRUE
                ORDER BY bs.variant_name
            """)
            return [dict(row) for row in cur.fetchall()]

    def choose_variant(self) -> str:
        """
        Select a prompt variant using Thompson Sampling.

        Returns the name of the selected variant.
        """
        try:
            stats = self.fetch_stats()
            if not stats:
                return "v1_baseline"  # Safe fallback

            # Thompson Sampling: sample from Beta distributions
            samples = []
            names = []

            for stat in stats:
                trials = max(1, int(stat['trials']))  # Avoid division by zero
                wins = max(0, int(stat['wins']))

                # Beta distribution parameters (add smoothing)
                alpha = 1 + wins
                beta_param = 1 + (trials - wins)

                # Sample from Beta distribution
                sample = np.random.beta(alpha, beta_param)
                samples.append(sample)
                names.append(stat['variant_name'])

            # Return variant with highest sample
            best_idx = int(np.argmax(samples))
            return names[best_idx]

        except Exception as e:
            print(f"Bandit selection error: {e}")
            return "v1_baseline"  # Safe fallback

    def record_outcome(self, variant: str, reward: float):
        """
        Record the outcome of a variant selection.

        Args:
            variant: Name of the prompt variant used
            reward: Reward value between -1 and 1
        """
        try:
            # Convert reward to binary win/loss for bandit
            # Positive reward = win, negative/zero = loss
            is_win = 1 if reward > 0 else 0

            with self._get_cursor() as cur:
                cur.execute("""
                    UPDATE bandit_stats
                    SET trials = trials + 1,
                        wins = wins + %s,
                        last_update = CURRENT_TIMESTAMP
                    WHERE variant_name = %s
                """, (is_win, variant))

        except Exception as e:
            print(f"Bandit record error: {e}")

    def get_variant_template(self, variant_name: str) -> Optional[str]:
        """Get the template for a specific variant."""
        try:
            with self._get_cursor() as cur:
                cur.execute("""
                    SELECT template FROM prompt_variants
                    WHERE name = %s AND active = TRUE
                """, (variant_name,))
                row = cur.fetchone()
                return row['template'] if row else None
        except Exception as e:
            print(f"Template fetch error: {e}")
            return None

    def get_leaderboard(self) -> List[Dict]:
        """Get current performance leaderboard."""
        try:
            stats = self.fetch_stats()
            leaderboard = []

            for stat in stats:
                trials = stat['trials']
                wins = stat['wins']
                win_rate = wins / trials if trials > 0 else 0.0

                leaderboard.append({
                    'variant': stat['variant_name'],
                    'trials': trials,
                    'wins': wins,
                    'win_rate': win_rate,
                    'template_preview': stat['template'][:100] + "..." if len(stat['template']) > 100 else stat['template']
                })

            # Sort by win rate (descending)
            return sorted(leaderboard, key=lambda x: x['win_rate'], reverse=True)

        except Exception as e:
            print(f"Leaderboard error: {e}")
            return []


# Global bandit policy instance
bandit_policy = BanditPolicy()


def choose_prompt_variant() -> str:
    """Convenience function for variant selection."""
    return bandit_policy.choose_variant()


def record_feedback(variant: str, reward: float):
    """Convenience function for recording outcomes."""
    bandit_policy.record_outcome(variant, reward)


def get_prompt_template(variant_name: str) -> Optional[str]:
    """Convenience function for template retrieval."""
    return bandit_policy.get_variant_template(variant_name)
