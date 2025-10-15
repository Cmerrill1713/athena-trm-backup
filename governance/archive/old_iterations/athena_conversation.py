#!/usr/bin/env python3
"""
Athena Conversational Interface
==============================

Natural language interface for AI Republic operations with conversational memory.
Supports contextual commands, command chaining, and fluid back-and-forth interaction.

Features:
- Conversational memory and context threading
- Natural language command parsing
- Multi-step operation chaining
- Persistent conversation state
- Intelligent command suggestions

Usage:
    python3 athena_conversation.py          # Interactive conversational mode
    python3 athena_conversation.py "status" # Direct command
    python3 athena_conversation.py --reset  # Clear conversation memory
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import argparse
import os
import sys

# Add system paths
sys.path.insert(0, '/opt/ai-republic')
sys.path.insert(0, os.path.dirname(__file__))

from ai_republic_cli import AIRepublicDashboard, Colors
from athena_notifications import AthenaNotifications

class ConversationMemory:
    """Manages conversational context and command history with persistence"""

    def __init__(self, memory_file: str = None):
        self.memory_file = memory_file or './conversation_memory.json'
        self.archive_file = self.memory_file.replace('.json', '_archive.json')
        self.memory = self.load_memory()
        self.max_history = 200  # Extended: Keep last 200 interactions
        self.context_timeout = 14400  # Extended: 4 hour context window
        self.max_archive_size = 1000  # Archive up to 1000 old interactions
        self.compression_enabled = True

    def load_memory(self) -> Dict:
        """Load conversation memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Could not load conversation memory: {e}{Colors.END}")

        return {
            'conversation_history': [],
            'current_context': {},
            'user_preferences': {},
            'last_interaction': None
        }

    def save_memory(self):
        """Save conversation memory to file with archiving"""
        try:
            current_history = self.memory['conversation_history']

            # Archive old interactions if we exceed max_history
            if len(current_history) > self.max_history:
                # Split into current and archive
                current_interactions = current_history[-self.max_history:]
                archive_interactions = current_history[:-self.max_history]

                # Compress/archive old interactions
                if self.compression_enabled and archive_interactions:
                    self._archive_old_interactions(archive_interactions)

                # Keep only current interactions
                self.memory['conversation_history'] = current_interactions

            # Save current memory
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Failed to save memory: {e}")
            print(f"{Colors.YELLOW}Warning: Could not save conversation memory: {e}{Colors.END}")

    def _archive_old_interactions(self, old_interactions: List[Dict]):
        """Archive old interactions to separate file"""
        try:
            # Load existing archive
            archive = {}
            if os.path.exists(self.archive_file):
                with open(self.archive_file, 'r') as f:
                    archive = json.load(f)

            # Add new archived interactions
            if 'archived_interactions' not in archive:
                archive['archived_interactions'] = []

            # Compress interactions (keep essential data only)
            compressed = []
            for interaction in old_interactions:
                compressed.append({
                    'timestamp': interaction['timestamp'],
                    'user_input': interaction['user_input'][:100],  # Truncate long inputs
                    'command': interaction.get('context', {}).get('last_command', 'unknown'),
                    'outcome': 'success' if '✅' in interaction.get('athena_response', '') else 'other'
                })

            archive['archived_interactions'].extend(compressed)

            # Limit archive size
            archive['archived_interactions'] = archive['archived_interactions'][-self.max_archive_size:]

            # Add metadata
            archive['last_archived'] = datetime.now().isoformat()
            archive['total_archived'] = len(archive['archived_interactions'])

            # Save archive
            with open(self.archive_file, 'w') as f:
                json.dump(archive, f, indent=2, default=str)

        except Exception as e:
            logging.error(f"Failed to archive interactions: {e}")

    def load_archived_memory(self) -> Dict:
        """Load archived memory for analysis and learning"""
        try:
            if os.path.exists(self.archive_file):
                with open(self.archive_file, 'r') as f:
                    archive = json.load(f)

                # Extract learning patterns from archive
                archived_patterns = self._analyze_archived_patterns(archive.get('archived_interactions', []))
                return archived_patterns
        except Exception as e:
            logging.error(f"Failed to load archived memory: {e}")

        return {}

    def _analyze_archived_patterns(self, archived_interactions: List[Dict]) -> Dict:
        """Analyze archived interactions for long-term learning"""
        patterns = {
            'command_frequency': {},
            'time_patterns': {},
            'success_patterns': {},
            'conversation_themes': {}
        }

        for interaction in archived_interactions:
            # Command frequency
            command = interaction.get('command', 'unknown')
            patterns['command_frequency'][command] = patterns['command_frequency'].get(command, 0) + 1

            # Time patterns (extract hour from timestamp)
            timestamp = interaction.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour_slot = f"{dt.hour//4}h"
                    patterns['time_patterns'][hour_slot] = patterns['time_patterns'].get(hour_slot, 0) + 1
                except:
                    pass

            # Success patterns
            outcome = interaction.get('outcome', 'unknown')
            patterns['success_patterns'][outcome] = patterns['success_patterns'].get(outcome, 0) + 1

        return patterns

    def get_persistent_insights(self) -> Dict:
        """Get insights from both current and archived memory"""
        current_insights = self.memory.get('learning', {})
        archived_insights = self.load_archived_memory()

        # Merge insights
        persistent_insights = {
            'current_session': current_insights,
            'historical_patterns': archived_insights,
            'combined_preferences': {}
        }

        # Combine command patterns
        current_commands = current_insights.get('command_patterns', {})
        archived_commands = archived_insights.get('command_frequency', {})

        combined_commands = {}
        for cmd in set(current_commands.keys()) | set(archived_commands.keys()):
            combined_commands[cmd] = current_commands.get(cmd, 0) + archived_commands.get(cmd, 0)

        persistent_insights['combined_preferences']['command_patterns'] = combined_commands

        return persistent_insights

    def recover_from_archive(self, query: str) -> List[Dict]:
        """Search archived memory for relevant past interactions"""
        try:
            if os.path.exists(self.archive_file):
                with open(self.archive_file, 'r') as f:
                    archive = json.load(f)

                relevant_interactions = []
                query_lower = query.lower()

                for interaction in archive.get('archived_interactions', []):
                    # Search in user input and command
                    if (query_lower in interaction.get('user_input', '').lower() or
                        query_lower in interaction.get('command', '').lower()):
                        relevant_interactions.append(interaction)

                return relevant_interactions[-10:]  # Return up to 10 most recent matches

        except Exception as e:
            logging.error(f"Failed to search archive: {e}")

        return []

    def add_interaction(self, user_input: str, athena_response: str, context: Dict = None):
        """Add an interaction to memory"""
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'athena_response': athena_response,
            'context': context or {}
        }

        self.memory['conversation_history'].append(interaction)
        self.memory['last_interaction'] = interaction['timestamp']

        # Update current context
        if context:
            self.memory['current_context'].update(context)

        self.save_memory()

    def get_recent_context(self, max_age_seconds: int = 3600) -> Dict:
        """Get recent conversation context"""
        cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
        recent_interactions = []

        for interaction in reversed(self.memory['conversation_history']):
            interaction_time = datetime.fromisoformat(interaction['timestamp'])
            if interaction_time > cutoff_time:
                recent_interactions.append(interaction)
            else:
                break

        return {
            'recent_interactions': recent_interactions,
            'current_context': self.memory.get('current_context', {}),
            'user_preferences': self.memory.get('user_preferences', {})
        }

    def set_context(self, key: str, value: Any):
        """Set a context variable"""
        self.memory['current_context'][key] = value
        self.save_memory()

    def get_context(self, key: str, default=None):
        """Get a context variable"""
        return self.memory.get('current_context', {}).get(key, default)

    def clear_context(self):
        """Clear current conversation context"""
        self.memory['current_context'] = {}
        self.save_memory()

    def get_command_suggestions(self) -> List[str]:
        """Get command suggestions based on recent context"""
        context = self.get_recent_context()
        suggestions = []

        # Suggest follow-ups based on recent commands
        recent_commands = [i['user_input'].lower() for i in context['recent_interactions'][-3:]]

        if any('status' in cmd for cmd in recent_commands):
            suggestions.extend(['show details', 'check tribunals', 'view metrics'])

        if any('tribunal' in cmd for cmd in recent_commands):
            suggestions.extend(['handle first one', 'show details', 'filter by severity'])

        if any('quarantine' in cmd for cmd in recent_commands):
            suggestions.extend(['release low severity', 'show active', 'check reasons'])

        # Add learned preferences
        learning = self.memory.memory.get('learning', {})
        command_patterns = learning.get('command_patterns', {})
        input_preferences = learning.get('input_preferences', {})

        if command_patterns:
            # Sort commands by frequency and suggest top ones
            top_commands = sorted(command_patterns.items(), key=lambda x: x[1], reverse=True)
            learned_suggestions = [cmd for cmd, count in top_commands[:3] if cmd not in ['help', 'converse']]
            suggestions.extend(learned_suggestions)

        # Conversation flow awareness
        conversation_flow = self._track_conversation_flow(context)
        if conversation_flow == 'tribunal_processing':
            suggestions.extend(['uphold tribunal', 'release tribunal', 'show details'])
        elif conversation_flow == 'information_gathering':
            suggestions.extend(['explain severity', 'what happened overnight', 'show logs'])
        elif conversation_flow == 'handling_issues':
            suggestions.extend(['status', 'check tribunals', 'restart services'])

        # Style-based suggestions
        preferred_style = max(input_preferences.items(), key=lambda x: x[1])[0] if input_preferences else 'brief'

        if preferred_style == 'brief':
            suggestions.extend(['status', 'briefing', 'tribunals'])
        else:
            suggestions.extend(['show me the system status', 'give me a briefing', 'check tribunal cases'])

        # Remove duplicates and common commands if no recent context
        suggestions = list(dict.fromkeys(suggestions))  # Remove duplicates

        if not suggestions:
            suggestions = ['status', 'briefing', 'tribunals', 'quarantines', 'help']

        return suggestions[:6]  # Return top 6 suggestions

class NaturalLanguageParser:
    """Parse natural language commands into structured actions"""

    def __init__(self):
        self.command_patterns = {
            # Status and monitoring
            r'(?:show me |give me |what.?s |check )?(?:the )?(?:system |overall )?status': 'status',
            r'(?:show |check |list )?(?:active )?tribunals?': 'tribunals',
            r'(?:show |check |list )?(?:active )?quarantines?': 'quarantines',
            r'(?:run |give me |show )?(?:a |the )?(?:daily |morning )?briefing': 'briefing',
            r'(?:show |check |list )?(?:system )?logs?': 'logs',

            # Tribunal operations
            r'handle (?:the |this )?tribunal(?: case)?': 'handle_tribunal',
            r'(?:uphold|confirm) (?:the |this )?tribunal': 'uphold_tribunal',
            r'release (?:the |this )?(?:quarantine|tribunal)': 'release_tribunal',
            r'block (?:the |this )?(?:actor|tribunal)': 'block_tribunal',

            # Quarantine operations
            r'release (?:all |the )?quarantines? (?:under|below) ([\d.]+)': 'release_low_severity',
            r'check quarantine reasons': 'quarantine_details',

            # System operations
            r'restart (?:the )?(judicial|constitutional) service': 'restart_service',
            r'clear (?:all )?quarantines': 'clear_quarantines',

            # Information requests
            r'what happened (?:overnight|today|recently)': 'recent_activity',
            r'explain (?:the |this )?severity': 'explain_severity',
            r'show (?:me )?details': 'show_details',

            # Archive and memory commands
            r'(?:search |find )(?:in )?archive (?:for )?(.+)': 'search_archive',
            r'recall (?:about )?(.+)': 'recall',
            r'(?:what |show )?(?:are )?my (.+)?': 'memory_stats',
            r'memory (?:stats?|statistics?)': 'memory_stats',

            # Meta commands
            r'(?:do |repeat )?(?:the |that )?again': 'repeat_last',
            r'clear (?:the )?context': 'clear_context',
            r'help|what can you do': 'help'
        }

    def parse_command(self, user_input: str) -> Tuple[str, Dict]:
        """Parse natural language input into command and parameters"""
        input_lower = user_input.lower().strip()

        # Check for direct commands first
        if input_lower in ['status', 'briefing', 'tribunals', 'quarantines', 'logs', 'help']:
            return input_lower, {}

        # Check pattern matches
        for pattern, command in self.command_patterns.items():
            match = re.search(pattern, input_lower)
            if match:
                params = {}
                groups = match.groups()

                if 'release_low_severity' in command and groups:
                    params['threshold'] = float(groups[0])
                elif 'restart_service' in command and groups:
                    params['service'] = groups[0]
                elif 'search_archive' in command and groups:
                    params['query'] = groups[0]
                elif 'recall' in command and groups:
                    params['topic'] = groups[0]

                return command, params

        # Context-dependent commands
        if any(word in input_lower for word in ['first', 'one', 'that']):
            return 'handle_first', {}
        elif any(word in input_lower for word in ['all', 'everything', 'rest']):
            return 'handle_all', {}
        elif 'details' in input_lower or 'more' in input_lower:
            return 'show_details', {}
        elif 'same' in input_lower or 'similar' in input_lower:
            return 'repeat_action', {}

        # Fallback to conversational response
        return 'converse', {'input': user_input}

class AthenaConversational:
    """Main conversational interface for Athena"""

    def __init__(self):
        self.dashboard = AIRepublicDashboard()
        self.notifications = AthenaNotifications()
        self.memory = ConversationMemory()
        self.parser = NaturalLanguageParser()

        # Internal state
        self.last_command = None
        self.last_result = None
        self.pending_actions = []

        # Extended conversation memory
        self.extended_memory = True
        self.max_history = 200  # Extended from 50 to 200 interactions
        self.context_timeout = 14400  # Extended from 3600 (1h) to 14400 (4h)

        # Enhanced memory features
        self.pattern_memory = {}  # Track user command patterns
        self.topic_tracking = {}  # Track conversation topics
        self.preference_learning = True

        # Load persistent insights on startup
        self._load_persistent_insights()

    def _load_persistent_insights(self):
        """Load persistent insights from archived memory on startup"""
        try:
            persistent_insights = self.memory.get_persistent_insights()

            # Merge archived patterns with current learning data
            if 'combined_preferences' in persistent_insights:
                combined_commands = persistent_insights['combined_preferences'].get('command_patterns', {})

                # Update current learning data with historical patterns
                if 'learning' not in self.memory.memory:
                    self.memory.memory['learning'] = {
                        'command_patterns': {},
                        'input_preferences': {},
                        'time_patterns': {}
                    }

                # Boost historical patterns (but don't overwhelm current session)
                learning = self.memory.memory['learning']
                for cmd, historical_count in combined_commands.items():
                    # Add historical weight (scaled down)
                    historical_boost = min(historical_count // 10, 5)  # Max 5 boost
                    learning['command_patterns'][cmd] = learning['command_patterns'].get(cmd, 0) + historical_boost

                print(f"{Colors.BLUE}🤖 Athena: Loaded {len(combined_commands)} historical patterns{Colors.END}")

        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Could not load persistent insights: {e}{Colors.END}")

    def process_command(self, user_input: str) -> str:
        """Process a natural language command and return response"""

        # Parse the command
        command, params = self.parser.parse_command(user_input)

        # Get extended conversation context (4-hour window)
        context = self.memory.get_recent_context(self.context_timeout)

        # Learn from user patterns
        if self.preference_learning:
            self._learn_user_patterns(user_input, command)

        # Process the command
        response, new_context = self.execute_command(command, params, context)

        # Add enhanced context tracking
        new_context.update({
            'input_type': self._detect_input_type(user_input),
            'command_pattern': self._analyze_command_pattern(user_input),
            'conversation_flow': self._track_conversation_flow(context)
        })

        # Update memory with enhanced context
        self.memory.add_interaction(user_input, response, new_context)

        # Store for potential follow-ups
        self.last_command = command
        self.last_result = response

        return response

    def _learn_user_patterns(self, user_input: str, command: str):
        """Learn from user command patterns for better suggestions"""
        # Track command frequency
        if command not in self.pattern_memory:
            self.pattern_memory[command] = 0
        self.pattern_memory[command] += 1

        # Track input style preferences
        input_length = len(user_input.split())
        time_of_day = datetime.now().hour

        # Store learning data in memory
        if 'learning' not in self.memory.memory:
            self.memory.memory['learning'] = {
                'command_patterns': {},
                'input_preferences': {},
                'time_patterns': {}
            }

        # Update learning data
        learning = self.memory.memory['learning']
        learning['command_patterns'][command] = learning['command_patterns'].get(command, 0) + 1

        # Track input style (brief vs detailed)
        style = 'brief' if input_length <= 3 else 'detailed'
        learning['input_preferences'][style] = learning['input_preferences'].get(style, 0) + 1

        # Track time preferences
        time_slot = f"{time_of_day//4}h"  # 4-hour time slots
        learning['time_patterns'][time_slot] = learning['time_patterns'].get(time_slot, 0) + 1

    def _detect_input_type(self, user_input: str) -> str:
        """Detect if input is likely voice or text based on patterns"""
        input_lower = user_input.lower()

        # Voice indicators
        voice_indicators = [
            'hey athena', 'athena', 'can you', 'please', 'would you',
            'i want', 'let me', 'show me', 'tell me', 'give me'
        ]

        # Text indicators (more direct commands)
        text_indicators = [
            'status', 'tribunals', 'logs', 'briefing', 'restart', 'clear'
        ]

        voice_score = sum(1 for indicator in voice_indicators if indicator in input_lower)
        text_score = sum(1 for indicator in text_indicators if indicator in input_lower)

        # Also check for question marks (more voice-like)
        has_question = '?' in user_input

        if voice_score > text_score or has_question or len(user_input.split()) > 8:
            return 'voice'
        else:
            return 'text'

    def _analyze_command_pattern(self, user_input: str) -> str:
        """Analyze the pattern/structure of the command"""
        words = user_input.lower().split()
        word_count = len(words)

        if word_count <= 2:
            return 'direct_command'
        elif word_count <= 5:
            return 'brief_request'
        elif any(word in words for word in ['show', 'give', 'tell', 'what']):
            return 'information_request'
        elif any(word in words for word in ['handle', 'release', 'clear', 'restart']):
            return 'action_command'
        elif '?' in user_input:
            return 'question'
        else:
            return 'conversational'

    def _track_conversation_flow(self, context: Dict) -> str:
        """Track the flow of conversation for context awareness"""
        recent_interactions = context.get('recent_interactions', [])

        if len(recent_interactions) < 2:
            return 'starting_conversation'

        # Analyze recent command sequence
        recent_commands = [i.get('athena_response', '').split()[0].lower() for i in recent_interactions[-3:]]

        # Detect patterns
        if recent_commands.count('✅') > 1:
            return 'successful_operation_sequence'
        elif any('⚠️' in cmd or '🚨' in cmd for cmd in recent_commands):
            return 'handling_issues'
        elif any('show' in cmd or 'details' in cmd for cmd in recent_commands):
            return 'information_gathering'
        elif any('handle' in cmd or 'uphold' in cmd for cmd in recent_commands):
            return 'tribunal_processing'
        else:
            return 'general_operations'

    def execute_command(self, command: str, params: Dict, context: Dict) -> Tuple[str, Dict]:
        """Execute a parsed command and return response"""

        new_context = {}

        # Status commands
        if command == 'status':
            status = self.dashboard.perform_health_check()
            response = self.format_status_response(status)
            new_context['last_status'] = status

        elif command == 'briefing':
            status = self.dashboard.perform_health_check()
            response = self.generate_conversational_briefing(status)
            new_context['last_briefing'] = status

        elif command == 'tribunals':
            tribunals = self.get_tribunal_status()
            response = self.format_tribunal_response(tribunals)
            new_context['last_tribunals'] = tribunals

        elif command == 'quarantines':
            quarantines = self.get_quarantine_status()
            response = self.format_quarantine_response(quarantines)
            new_context['last_quarantines'] = quarantines

        elif command == 'logs':
            logs = self.get_recent_logs()
            response = self.format_logs_response(logs)
            new_context['last_logs'] = logs

        # Tribunal operations
        elif command == 'handle_tribunal':
            response = self.handle_pending_tribunal(context)
            new_context['last_action'] = 'handle_tribunal'

        elif command == 'uphold_tribunal':
            response = self.uphold_tribunal(context)
            new_context['last_action'] = 'uphold_tribunal'

        elif command == 'release_tribunal':
            response = self.release_tribunal(context)
            new_context['last_action'] = 'release_tribunal'

        elif command == 'block_tribunal':
            response = self.block_tribunal(context)
            new_context['last_action'] = 'block_tribunal'

        elif command == 'handle_first':
            response = self.handle_first_tribunal(context)
            new_context['last_action'] = 'handle_first'

        elif command == 'handle_all':
            response = self.handle_all_tribunals(context)
            new_context['last_action'] = 'handle_all'

        # Quarantine operations
        elif command == 'release_low_severity':
            threshold = params.get('threshold', 0.8)
            response = self.release_low_severity_quarantines(threshold)
            new_context['last_action'] = f'release_threshold_{threshold}'

        elif command == 'clear_quarantines':
            response = self.clear_all_quarantines()
            new_context['last_action'] = 'clear_quarantines'

        # System operations
        elif command == 'restart_service':
            service = params.get('service', 'judicial')
            response = self.restart_service(service)
            new_context['last_action'] = f'restart_{service}'

        # Information requests
        elif command == 'recent_activity':
            response = self.get_recent_activity_summary()
            new_context['last_activity_check'] = datetime.now().isoformat()

        elif command == 'explain_severity':
            response = self.explain_severity_levels()
            new_context['last_explanation'] = 'severity'

        elif command == 'show_details':
            response = self.show_last_details(context)

        # Meta commands
        elif command == 'repeat_last':
            if self.last_command:
                return self.execute_command(self.last_command, params, context)
            else:
                response = "I don't have a previous command to repeat. What would you like me to do?"

        elif command == 'clear_context':
            self.memory.clear_context()
            response = "Conversation context cleared. Starting fresh!"

        elif command == 'help':
            response = self.get_help_text()

        # Archive and memory commands
        elif command == 'search_archive':
            query = params.get('query', user_input)
            archived_results = self.memory.recover_from_archive(query)
            response = self.format_archive_search_results(archived_results, query)

        elif command == 'recall':
            topic = params.get('topic', user_input.replace('recall', '').strip())
            relevant_history = self.memory.recover_from_archive(topic)
            response = self.format_recall_results(relevant_history, topic)

        elif command == 'memory_stats':
            insights = self.memory.get_persistent_insights()
            response = self.format_memory_stats(insights)

        # Conversational fallback
        elif command == 'converse':
            response = self.handle_conversation(params.get('input', ''), context)

        else:
            response = f"I'm not sure how to handle '{command}'. Try 'help' for available commands."

        return response, new_context

    def format_archive_search_results(self, results: List[Dict], query: str) -> str:
        """Format archived search results conversationally"""
        if not results:
            return f"🤔 I searched my archived memory but couldn't find anything about '{query}'. This might be from before I started archiving conversations."

        response = f"📚 **Archived Memory Search Results for '{query}':**\n\n"
        response += f"Found {len(results)} relevant past interactions:\n\n"

        for i, result in enumerate(results, 1):
            timestamp = result.get('timestamp', 'Unknown')
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%m/%d %H:%M')
            except:
                time_str = timestamp[:16] if timestamp else 'Unknown'

            user_input = result.get('user_input', 'Unknown')[:60]
            command = result.get('command', 'unknown')
            outcome = result.get('outcome', 'unknown')

            response += f"**{i}.** {time_str} - *{command}*\n"
            response += f"   \"{user_input}{'...' if len(user_input) > 60 else ''}\"\n"
            response += f"   Outcome: {outcome}\n\n"

        response += "💡 **Tip:** You can say 'recall [topic]' to search for more details about any topic."

        return response

    def format_recall_results(self, results: List[Dict], topic: str) -> str:
        """Format recall results conversationally"""
        if not results:
            return f"🤔 I don't have any archived memories about '{topic}'. We might not have discussed that before, or it could be from before my archiving began."

        response = f"🧠 **Recalling past discussions about '{topic}':**\n\n"

        # Group by date for better readability
        by_date = {}
        for result in results:
            timestamp = result.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_key = dt.strftime('%Y-%m-%d')
            except:
                date_key = 'Unknown'

            if date_key not in by_date:
                by_date[date_key] = []
            by_date[date_key].append(result)

        for date in sorted(by_date.keys(), reverse=True):
            response += f"**{date}:**\n"
            for result in by_date[date]:
                time_str = result.get('timestamp', '')[11:16] if len(result.get('timestamp', '')) > 16 else '??:??'
                command = result.get('command', 'unknown')
                outcome = result.get('outcome', 'unknown')
                response += f"   {time_str} - {command} ({outcome})\n"
            response += "\n"

        response += "💭 **Context:** These are compressed memories from past conversations. For full details from recent interactions, check the current session history."

        return response

    def format_memory_stats(self, insights: Dict) -> str:
        """Format memory statistics conversationally"""
        response = "🧠 **Athena Memory Statistics:**\n\n"

        # Current session
        current = insights.get('current_session', {})
        response += "**Current Session:**\n"
        response += f"   Interactions remembered: {len(self.memory.memory.get('conversation_history', []))}\n"

        if current.get('command_patterns'):
            top_commands = sorted(current['command_patterns'].items(), key=lambda x: x[1], reverse=True)[:5]
            response += f"   Top commands: {', '.join([f'{cmd}({count})' for cmd, count in top_commands])}\n"

        if current.get('input_preferences'):
            pref = max(current['input_preferences'].items(), key=lambda x: x[1])
            response += f"   Preferred style: {pref[0]} ({pref[1]} times)\n"

        # Historical patterns
        historical = insights.get('historical_patterns', {})
        if historical:
            response += "\n**Historical Patterns:**\n"
            if historical.get('command_frequency'):
                archived_commands = len(historical['command_frequency'])
                response += f"   Archived command patterns: {archived_commands}\n"

            if historical.get('time_patterns'):
                peak_time = max(historical['time_patterns'].items(), key=lambda x: x[1])
                response += f"   Peak interaction time: {peak_time[0]} ({peak_time[1]} interactions)\n"

            if historical.get('success_patterns'):
                success_rate = historical['success_patterns'].get('success', 0)
                total_outcomes = sum(historical['success_patterns'].values())
                if total_outcomes > 0:
                    rate = (success_rate / total_outcomes) * 100
                    response += f"   Historical success rate: {rate:.1f}%\n"

        # Combined preferences
        combined = insights.get('combined_preferences', {})
        if combined.get('command_patterns'):
            total_patterns = len(combined['command_patterns'])
            response += f"\n**Combined Learning:** {total_patterns} total command patterns learned\n"

        response += "\n💡 **Memory Management:** Recent interactions stay in active memory, older ones are compressed and archived for pattern learning."

        return response

    def format_status_response(self, status: Dict) -> str:
        """Format status information conversationally"""
        overall = status.get('overall_status', 'UNKNOWN')

        if overall == 'HEALTHY':
            response = "✅ **System Status: HEALTHY** - Everything is operating normally."
        elif overall == 'WARNING':
            response = "⚠️ **System Status: WARNING** - Some minor issues detected."
        else:
            response = "🚨 **System Status: CRITICAL** - Immediate attention required."

        # Add service details
        services = status.get('services', {})
        if services:
            response += "\n\n🔧 **Services:**"
            for name, info in services.items():
                status_icon = "✅" if info.get('status') == 'running' else "❌"
                response += f"\n   {status_icon} {name.capitalize()}: {info.get('status', 'unknown')}"

        return response

    def generate_conversational_briefing(self, status: Dict) -> str:
        """Generate a conversational daily briefing"""
        # Similar to the scheduler but more conversational
        overall = status.get('overall_status', 'UNKNOWN')

        greeting = self.get_time_based_greeting()
        briefing = f"🤖 {greeting}! Here's your AI Republic status briefing:\n\n"

        if overall == 'HEALTHY':
            briefing += "✅ **Overall Status: HEALTHY** - All systems operating normally"
        elif overall == 'WARNING':
            briefing += "⚠️ **Overall Status: WARNING** - Minor issues detected, monitoring closely"
        else:
            briefing += "🚨 **Overall Status: CRITICAL** - Immediate attention required"

        # Add key metrics and recommendations
        briefing += "\n\n🎯 **Recommendations:** "
        if overall == 'HEALTHY':
            briefing += "No action needed - have a great day!"
        else:
            briefing += "Check tribunals and review system status for details."

        return briefing

    def get_time_based_greeting(self) -> str:
        """Get time-appropriate greeting"""
        hour = datetime.now().hour
        if hour < 12:
            return "Good morning"
        elif hour < 17:
            return "Good afternoon"
        else:
            return "Good evening"

    def get_tribunal_status(self) -> List[Dict]:
        """Get current tribunal status"""
        # This would integrate with the actual tribunal system
        # For now, return mock data
        return [
            {
                'id': 'tribunal_001',
                'actor': 'rogue_agent_12',
                'severity': 0.86,
                'article': 'II',
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
        ]

    def format_tribunal_response(self, tribunals: List[Dict]) -> str:
        """Format tribunal information conversationally"""
        if not tribunals:
            return "✅ No active tribunal cases found. The system is running cleanly!"

        response = f"⚖️ Found {len(tribunals)} tribunal case(s) requiring attention:\n"

        for i, tribunal in enumerate(tribunals[:3], 1):
            severity_emoji = "🔴" if tribunal['severity'] > 0.8 else "🟡"
            response += f"\n{i}. {severity_emoji} **{tribunal['actor']}** - Severity {tribunal['severity']}"
            response += f"\n   Article {tribunal['article']} violation"
            response += f"\n   Status: {tribunal['status']}"

        if len(tribunals) > 3:
            response += f"\n\n...and {len(tribunals) - 3} more cases."

        response += "\n\n💡 **Ready to handle:** Say 'handle first one' or 'show details'"

        return response

    def get_quarantine_status(self) -> List[Dict]:
        """Get current quarantine status"""
        # Mock data - would integrate with actual system
        return [
            {
                'actor': 'suspicious_agent_45',
                'severity': 0.72,
                'reason': 'Article II breach',
                'duration': 14400,
                'time_remaining': 7200
            }
        ]

    def format_quarantine_response(self, quarantines: List[Dict]) -> str:
        """Format quarantine information conversationally"""
        if not quarantines:
            return "✅ No active quarantines. All actors are operating normally!"

        response = f"🔒 Found {len(quarantines)} active quarantine(s):\n"

        for quarantine in quarantines:
            hours_remaining = quarantine['time_remaining'] // 3600
            response += f"\n• **{quarantine['actor']}** - Severity {quarantine['severity']}"
            response += f"\n  Reason: {quarantine['reason']}"
            response += f"\n  Time remaining: {hours_remaining} hours"

        return response

    def get_recent_logs(self) -> List[str]:
        """Get recent log entries"""
        # Mock data - would integrate with actual logs
        return [
            "10:23:15 - ALLOW: user_session_123",
            "10:15:42 - WARN: api_client_456 (rate limit)",
            "09:47:33 - TRIBUNAL: rogue_agent_12 (Article II breach)",
        ]

    def format_logs_response(self, logs: List[str]) -> str:
        """Format log information conversationally"""
        if not logs:
            return "📋 No recent log activity to show."

        response = f"📋 Recent activity (last {len(logs)} entries):\n"

        for log in logs[-5:]:  # Show last 5
            response += f"\n• {log}"

        return response

    def handle_pending_tribunal(self, context: Dict) -> str:
        """Handle the most recent tribunal case"""
        tribunals = context.get('last_tribunals', [])
        if tribunals:
            tribunal = tribunals[0]
            return f"⚖️ Handling tribunal for **{tribunal['actor']}** (severity {tribunal['severity']})...\n\nRecommended action: UPHOLD tribunal and maintain quarantine.\n\nConfirm with 'uphold tribunal' or suggest alternative action."
        else:
            return "No tribunal cases found to handle. Check status first with 'tribunals'."

    def uphold_tribunal(self, context: Dict) -> str:
        """Uphold a tribunal decision"""
        # This would integrate with actual tribunal system
        return "✅ Tribunal upheld. Quarantine maintained for the violating actor. Case logged and escalated to oversight council."

    def handle_first_tribunal(self, context: Dict) -> str:
        """Handle the first tribunal in the list"""
        tribunals = context.get('last_tribunals', [])
        if tribunals:
            tribunal = tribunals[0]
            # Simulate handling
            return f"✅ Handled tribunal for **{tribunal['actor']}**. Applied standard quarantine protocol. Case resolved."
        else:
            return "No tribunals to handle. Check status with 'tribunals'."

    def release_low_severity_quarantines(self, threshold: float) -> str:
        """Release quarantines below severity threshold"""
        # This would integrate with actual quarantine system
        return f"✅ Released all quarantines with severity below {threshold}. {3} actors restored to normal operation."

    def restart_service(self, service: str) -> str:
        """Restart a system service"""
        # This would use systemctl or similar
        return f"✅ Restarted {service} service. System health restored."

    def get_recent_activity_summary(self) -> str:
        """Get summary of recent activity"""
        return "📊 **Overnight Summary:**\n• 47 ALLOW decisions (normal operations)\n• 3 WARN events (minor rate limiting)\n• 1 TRIBUNAL case (handled automatically)\n• All services maintained 99.9% uptime\n• No critical incidents detected"

    def explain_severity_levels(self) -> str:
        """Explain severity level meanings"""
        return """📖 **Severity Levels:**
• **0.0-0.3**: Routine monitoring, no action needed
• **0.3-0.6**: Minor warnings, logged for review
• **0.6-0.8**: Moderate violations, quarantine recommended
• **0.8-1.0**: Critical violations, tribunal required

Higher severity = more serious constitutional breach."""

    def show_last_details(self, context: Dict) -> str:
        """Show details from last command"""
        last_cmd = context.get('last_action', 'none')
        if last_cmd.startswith('release_threshold_'):
            threshold = last_cmd.split('_')[-1]
            return f"Last action: Released quarantines below severity {threshold}"
        elif last_cmd == 'handle_first':
            return "Last action: Handled first tribunal case with standard quarantine"
        else:
            return "No recent action details available. Try checking status or tribunals."

    def get_help_text(self) -> str:
        """Get help text with available commands"""
        return """🤖 **Available Commands:**

**Status & Monitoring:**
• "status" - Show system health
• "briefing" - Full daily briefing
• "tribunals" - Check tribunal cases
• "quarantines" - View active quarantines
• "logs" - Recent system activity

**Actions:**
• "handle tribunal" - Process tribunal case
• "uphold tribunal" - Confirm tribunal decision
• "release quarantines under 0.8" - Auto-release low severity
• "restart judicial service" - Restart system service

**Information:**
• "what happened overnight" - Activity summary
• "explain severity" - Severity level guide
• "show details" - More info on last command

**Archive & Memory:**
• "search archive for [topic]" - Search past conversations
• "recall [topic]" - Remember past discussions
• "memory stats" - View learning statistics

**Context:**
• "do that again" - Repeat last action
• "clear context" - Reset conversation

Just type naturally - I'll understand! 💬"""

    def handle_conversation(self, user_input: str, context: Dict) -> str:
        """Handle conversational input that's not a direct command"""
        input_lower = user_input.lower()

        # Greetings
        if any(word in input_lower for word in ['hello', 'hi', 'hey', 'good morning']):
            greeting = self.get_time_based_greeting()
            return f"🤖 {greeting}! I'm Athena, your AI Republic operations partner. How can I help you today?"

        # Gratitude
        elif any(word in input_lower for word in ['thanks', 'thank you', 'good job']):
            return "🤖 You're welcome! Happy to help keep the AI Republic running smoothly."

        # Status questions
        elif any(word in input_lower for word in ['how are you', 'how is everything']):
            return "🤖 I'm operating optimally! All systems are under my watchful eye. Would you like a status update?"

        # Contextual follow-ups
        elif 'same' in input_lower or 'similar' in input_lower:
            return "🤖 I'll apply the same action. " + self.process_command(self.last_command or "status")

        # Unknown input
        else:
            suggestions = self.memory.get_command_suggestions()
            suggestion_text = "Try: " + ", ".join(f"'{s}'" for s in suggestions[:3])
            return f"🤖 I'm not sure what you mean by '{user_input}'. {suggestion_text}, or say 'help' for all options."

    def run_interactive_mode(self):
        """Run interactive conversational mode"""
        print(f"{Colors.BOLD}{Colors.BLUE}🤖 Athena Conversational Interface{Colors.END}")
        print("Type 'help' for commands or just chat naturally!")
        print("Type 'quit' to exit.\n")

        while True:
            try:
                # Show command suggestions
                suggestions = self.memory.get_command_suggestions()
                if suggestions:
                    print(f"{Colors.BLUE}💡 Suggestions: {', '.join(suggestions)}{Colors.END}")

                # Get user input
                user_input = input(f"\n{Colors.GREEN}You>{Colors.END} ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print(f"{Colors.BLUE}👋 Goodbye! Athena signing off.{Colors.END}")
                    break

                # Process the command
                response = self.process_command(user_input)

                # Print response
                print(f"\n{Colors.BLUE}🤖 Athena:{Colors.END}")
                print(response)

            except KeyboardInterrupt:
                print(f"\n{Colors.BLUE}👋 Athena signing off.{Colors.END}")
                break
            except Exception as e:
                print(f"{Colors.RED}❌ Error: {e}{Colors.END}")

def main():
    parser = argparse.ArgumentParser(description='Athena Conversational Interface')
    parser.add_argument('command', nargs='?', help='Direct command to execute')
    parser.add_argument('--reset', action='store_true', help='Reset conversation memory')
    parser.add_argument('--context', action='store_true', help='Show current conversation context')

    args = parser.parse_args()

    athena = AthenaConversational()

    if args.reset:
        athena.memory.clear_context()
        print("🧹 Conversation memory and context cleared.")

    elif args.context:
        context = athena.memory.get_recent_context()
        print("🧠 Current Context:")
        print(json.dumps(context, indent=2, default=str))

    elif args.command:
        # Execute direct command
        response = athena.process_command(args.command)
        print(f"🤖 Athena: {response}")

    else:
        # Interactive mode
        athena.run_interactive_mode()

if __name__ == '__main__':
    main()
