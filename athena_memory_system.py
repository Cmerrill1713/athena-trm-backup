#!/usr/bin/env python3
"""
ATHENA PERSISTENT MEMORY SYSTEM
Long-term memory and learning capabilities for conversational AI governance

Maintains conversation history, learned patterns, user preferences, and operational insights
across sessions and system restarts.
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
import hashlib
import gzip

from athena_conversation_engine import ConversationContext

class AthenaMemorySystem:
    """Persistent memory system for Athena's learning and context"""

    def __init__(self, memory_dir: str = "/var/lib/ai-republic/athena_memory"):
        self.memory_dir = memory_dir
        self.session_memory_file = os.path.join(memory_dir, "session_memory.json")
        self.long_term_memory_file = os.path.join(memory_dir, "long_term_memory.json.gz")
        self.user_preferences_file = os.path.join(memory_dir, "user_preferences.json")
        self.conversation_archive_dir = os.path.join(memory_dir, "conversations")

        # Create directories
        os.makedirs(memory_dir, exist_ok=True)
        os.makedirs(self.conversation_archive_dir, exist_ok=True)

        # Load existing memory
        self.long_term_memory = self._load_long_term_memory()
        self.user_preferences = self._load_user_preferences()
        self.session_memory = self._load_session_memory()

        # Memory limits
        self.max_conversation_history = 1000  # conversations
        self.max_patterns_per_intent = 50
        self.max_user_preferences = 100
        self.memory_retention_days = 90  # days to keep detailed conversation logs

    def _load_session_memory(self) -> Dict[str, Any]:
        """Load current session memory"""
        try:
            if os.path.exists(self.session_memory_file):
                with open(self.session_memory_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load session memory: {e}")

        return {
            'current_session_id': f"session_{int(time.time())}",
            'active_context': {},
            'recent_conversations': [],
            'pending_actions': [],
            'session_start': datetime.now().isoformat()
        }

    def _save_session_memory(self):
        """Save current session memory"""
        try:
            with open(self.session_memory_file, 'w') as f:
                json.dump(self.session_memory, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save session memory: {e}")

    def _load_long_term_memory(self) -> Dict[str, Any]:
        """Load long-term memory patterns and learning"""
        try:
            if os.path.exists(self.long_term_memory_file):
                with gzip.open(self.long_term_memory_file, 'rt') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load long-term memory: {e}")

        return {
            'learned_patterns': {},
            'command_frequencies': {},
            'successful_commands': {},
            'failed_commands': {},
            'user_command_patterns': {},
            'context_transitions': {},
            'last_updated': datetime.now().isoformat()
        }

    def _save_long_term_memory(self):
        """Save long-term memory patterns"""
        try:
            self.long_term_memory['last_updated'] = datetime.now().isoformat()
            with gzip.open(self.long_term_memory_file, 'wt') as f:
                json.dump(self.long_term_memory, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save long-term memory: {e}")

    def _load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences and settings"""
        try:
            if os.path.exists(self.user_preferences_file):
                with open(self.user_preferences_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load user preferences: {e}")

        return {
            'preferred_modality': 'hybrid',  # voice, text, or hybrid
            'voice_sensitivity': 'medium',
            'notification_preferences': {
                'tribunal_alerts': True,
                'system_warnings': True,
                'daily_briefings': True
            },
            'command_shortcuts': {},
            'learned_favorites': [],
            'communication_style': 'professional'  # professional, casual, technical
        }

    def _save_user_preferences(self):
        """Save user preferences"""
        try:
            with open(self.user_preferences_file, 'w') as f:
                json.dump(self.user_preferences, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save user preferences: {e}")

    def save_conversation(self, context: ConversationContext, conversation_log: List[Dict[str, Any]]):
        """Save a complete conversation for archival"""
        conversation_data = {
            'session_id': context.session_id,
            'user_id': context.user_id,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - datetime.fromisoformat(context.last_interaction.isoformat())).total_seconds(),
            'message_count': len(conversation_log),
            'context_memory': dict(context.context_memory),
            'command_history': context.command_history[-50:],  # Last 50 commands
            'conversation_log': conversation_log,
            'summary': self._generate_conversation_summary(conversation_log)
        }

        # Save to dated file
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"conversation_{context.session_id}_{int(time.time())}.json.gz"
        filepath = os.path.join(self.conversation_archive_dir, date_str, filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        try:
            with gzip.open(filepath, 'wt') as f:
                json.dump(conversation_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save conversation: {e}")

    def _generate_conversation_summary(self, conversation_log: List[Dict[str, Any]]) -> str:
        """Generate a summary of the conversation"""
        if not conversation_log:
            return "Empty conversation"

        user_messages = [msg for msg in conversation_log if msg.get('role') == 'user']
        assistant_messages = [msg for msg in conversation_log if msg.get('role') == 'assistant']

        intents = [msg.get('intent', 'unknown') for msg in assistant_messages if 'intent' in msg]
        intent_counts = Counter(intents)

        summary_parts = [
            f"{len(user_messages)} user inputs",
            f"{len(assistant_messages)} assistant responses",
            f"Primary intents: {', '.join([f'{intent}({count})' for intent, count in intent_counts.most_common(3)])}"
        ]

        return " | ".join(summary_parts)

    def learn_from_interaction(self, user_input: str, intent: str, success: bool, response: str):
        """Learn patterns from user interactions"""
        # Update command frequencies
        if intent not in self.long_term_memory['command_frequencies']:
            self.long_term_memory['command_frequencies'][intent] = {}
        self.long_term_memory['command_frequencies'][intent][user_input] = \
            self.long_term_memory['command_frequencies'][intent].get(user_input, 0) + 1

        # Track successful vs failed commands
        if success:
            if intent not in self.long_term_memory['successful_commands']:
                self.long_term_memory['successful_commands'][intent] = {}
            self.long_term_memory['successful_commands'][intent][user_input] = \
                self.long_term_memory['successful_commands'][intent].get(user_input, 0) + 1
        else:
            if intent not in self.long_term_memory['failed_commands']:
                self.long_term_memory['failed_commands'][intent] = {}
            self.long_term_memory['failed_commands'][intent][user_input] = \
                self.long_term_memory['failed_commands'][intent].get(user_input, 0) + 1

        # Learn user patterns (what commands they use most)
        user_hash = hashlib.md5(user_input.lower().encode()).hexdigest()[:8]
        if user_hash not in self.long_term_memory['user_command_patterns']:
            self.long_term_memory['user_command_patterns'][user_hash] = {
                'pattern': user_input.lower(),
                'frequency': 0,
                'last_used': None,
                'successful': success
            }
        self.long_term_memory['user_command_patterns'][user_hash]['frequency'] += 1
        self.long_term_memory['user_command_patterns'][user_hash]['last_used'] = datetime.now().isoformat()
        self.long_term_memory['user_command_patterns'][user_hash]['successful'] = success

        # Learn context transitions (what follows what)
        if 'last_intent' in self.session_memory.get('active_context', {}):
            last_intent = self.session_memory['active_context']['last_intent']
            transition_key = f"{last_intent}->{intent}"
            if 'context_transitions' not in self.long_term_memory:
                self.long_term_memory['context_transitions'] = {}
            self.long_term_memory['context_transitions'][transition_key] = \
                self.long_term_memory['context_transitions'].get(transition_key, 0) + 1

        # Update session context
        if 'active_context' not in self.session_memory:
            self.session_memory['active_context'] = {}
        self.session_memory['active_context']['last_intent'] = intent
        self.session_memory['active_context']['last_success'] = success

        # Save learning periodically
        self._save_long_term_memory()

    def get_personalized_suggestions(self, current_context: str = "") -> List[str]:
        """Get personalized command suggestions based on learned patterns"""
        suggestions = []

        # Get most frequent successful commands
        successful_commands = self.long_term_memory.get('successful_commands', {})

        # Find commands similar to current context
        if current_context:
            context_words = set(current_context.lower().split())
            for intent, commands in successful_commands.items():
                for cmd in commands.keys():
                    cmd_words = set(cmd.lower().split())
                    if context_words & cmd_words:  # Has common words
                        suggestions.append(cmd)

        # Add frequently used commands
        all_commands = []
        for intent_commands in successful_commands.values():
            all_commands.extend(intent_commands.keys())

        command_counts = Counter(all_commands)
        suggestions.extend([cmd for cmd, count in command_counts.most_common(5)])

        # Remove duplicates and limit
        return list(dict.fromkeys(suggestions))[:5]

    def predict_next_intent(self, current_intent: str) -> Optional[str]:
        """Predict next likely intent based on learned transitions"""
        transitions = self.long_term_memory.get('context_transitions', {})
        possible_transitions = {k: v for k, v in transitions.items() if k.startswith(f"{current_intent}->")}

        if not possible_transitions:
            return None

        # Return most likely transition
        most_likely = max(possible_transitions.items(), key=lambda x: x[1])
        return most_likely[0].split('->')[1]

    def get_user_favorites(self) -> List[str]:
        """Get user's most frequently used successful commands"""
        successful_commands = self.long_term_memory.get('successful_commands', {})

        favorites = []
        for intent_commands in successful_commands.values():
            favorites.extend([(cmd, count) for cmd, count in intent_commands.items()])

        # Sort by frequency
        favorites.sort(key=lambda x: x[1], reverse=True)
        return [cmd for cmd, count in favorites[:10]]

    def update_user_preference(self, preference: str, value: Any):
        """Update a user preference"""
        self.user_preferences[preference] = value
        self._save_user_preferences()

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            'session_memory_size': len(json.dumps(self.session_memory)),
            'long_term_memory_size': len(json.dumps(self.long_term_memory)),
            'user_preferences_count': len(self.user_preferences),
            'learned_patterns_count': len(self.long_term_memory.get('learned_patterns', {})),
            'conversation_archives': len([f for f in os.listdir(self.conversation_archive_dir)
                                        if os.path.isdir(os.path.join(self.conversation_archive_dir, f))]),
            'command_frequencies': sum(len(cmds) for cmds in self.long_term_memory.get('command_frequencies', {}).values()),
            'successful_commands': sum(len(cmds) for cmds in self.long_term_memory.get('successful_commands', {}).values()),
            'memory_retention_days': self.memory_retention_days
        }

    def cleanup_old_memories(self):
        """Clean up old conversation archives and optimize memory"""
        cutoff_date = datetime.now() - timedelta(days=self.memory_retention_days)

        # Clean up old conversation archives
        for date_dir in os.listdir(self.conversation_archive_dir):
            if not os.path.isdir(os.path.join(self.conversation_archive_dir, date_dir)):
                continue

            try:
                dir_date = datetime.strptime(date_dir, "%Y%m%d")
                if dir_date < cutoff_date:
                    # Remove old directory
                    import shutil
                    shutil.rmtree(os.path.join(self.conversation_archive_dir, date_dir))
            except ValueError:
                continue  # Skip invalid date directories

        # Optimize long-term memory (keep only most frequent patterns)
        self._optimize_long_term_memory()

    def _optimize_long_term_memory(self):
        """Optimize long-term memory by removing infrequent patterns"""
        # Keep only top patterns per intent
        for intent, patterns in self.long_term_memory.get('command_frequencies', {}).items():
            if len(patterns) > self.max_patterns_per_intent:
                # Sort by frequency and keep top N
                sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
                self.long_term_memory['command_frequencies'][intent] = dict(sorted_patterns[:self.max_patterns_per_intent])

        # Similar optimization for other memory structures
        for memory_type in ['successful_commands', 'failed_commands']:
            if memory_type in self.long_term_memory:
                for intent, patterns in self.long_term_memory[memory_type].items():
                    if len(patterns) > self.max_patterns_per_intent:
                        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
                        self.long_term_memory[memory_type][intent] = dict(sorted_patterns[:self.max_patterns_per_intent])

        self._save_long_term_memory()

    def export_memory_data(self, filepath: str):
        """Export all memory data for backup or analysis"""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'session_memory': self.session_memory,
            'long_term_memory': self.long_term_memory,
            'user_preferences': self.user_preferences,
            'memory_stats': self.get_memory_stats()
        }

        try:
            with gzip.open(filepath, 'wt') as f:
                json.dump(export_data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False

    def import_memory_data(self, filepath: str) -> bool:
        """Import memory data from backup"""
        try:
            with gzip.open(filepath, 'rt') as f:
                import_data = json.load(f)

            # Merge imported data
            if 'long_term_memory' in import_data:
                self.long_term_memory.update(import_data['long_term_memory'])
            if 'user_preferences' in import_data:
                self.user_preferences.update(import_data['user_preferences'])

            self._save_long_term_memory()
            self._save_user_preferences()
            return True
        except Exception as e:
            print(f"Import failed: {e}")
            return False

    def reset_memory(self, memory_type: str = 'all'):
        """Reset memory (use with caution)"""
        if memory_type in ['all', 'session']:
            self.session_memory = self._load_session_memory()
            self._save_session_memory()

        if memory_type in ['all', 'long_term']:
            self.long_term_memory = self._load_long_term_memory()
            self._save_long_term_memory()

        if memory_type in ['all', 'preferences']:
            self.user_preferences = self._load_user_preferences()
            self._save_user_preferences()

        print(f"Memory reset: {memory_type}")

    def shutdown(self):
        """Clean shutdown of memory system"""
        self._save_session_memory()
        self._save_long_term_memory()
        self._save_user_preferences()

# Convenience functions for integration
def get_memory_system() -> AthenaMemorySystem:
    """Get the global memory system instance"""
    if not hasattr(get_memory_system, '_instance'):
        get_memory_system._instance = AthenaMemorySystem()
    return get_memory_system._instance

def learn_from_interaction(user_input: str, intent: str, success: bool, response: str):
    """Convenience function to learn from interactions"""
    memory = get_memory_system()
    memory.learn_from_interaction(user_input, intent, success, response)

def get_personalized_suggestions(context: str = "") -> List[str]:
    """Get personalized suggestions"""
    memory = get_memory_system()
    return memory.get_personalized_suggestions(context)

if __name__ == '__main__':
    # Test the memory system
    memory = AthenaMemorySystem()

    print("Athena Memory System Stats:")
    stats = memory.get_memory_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nMemory system initialized successfully!")
