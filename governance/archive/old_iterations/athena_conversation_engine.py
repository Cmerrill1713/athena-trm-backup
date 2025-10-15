#!/usr/bin/env python3
"""
ATHENA CONVERSATION ENGINE
Natural Language Processing for AI Republic Operations

Enables conversational interaction with the AI Republic through natural language commands,
context awareness, and intelligent command routing.
"""

import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import difflib

from athena_ops_copilot import AthenaOpsCopilot

@dataclass
class ConversationContext:
    """Tracks conversation state and context"""
    user_id: str = "default_user"
    session_id: str = ""
    last_interaction: Optional[datetime] = None
    context_memory: Dict[str, Any] = field(default_factory=dict)
    command_history: List[Dict[str, Any]] = field(default_factory=list)
    pending_confirmations: Dict[str, Any] = field(default_factory=dict)
    active_topics: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.session_id:
            self.session_id = f"session_{int(time.time())}"
        if not self.last_interaction:
            self.last_interaction = datetime.now()

    def update_context(self, topic: str, data: Any):
        """Update conversation context"""
        self.context_memory[topic] = data
        self.last_interaction = datetime.now()

        # Keep active topics list updated
        if topic not in self.active_topics:
            self.active_topics.append(topic)
            # Limit to last 5 topics
            if len(self.active_topics) > 5:
                self.active_topics.pop(0)

    def get_context(self, topic: str) -> Any:
        """Retrieve context data"""
        return self.context_memory.get(topic)

    def add_command_history(self, command: str, intent: str, result: str):
        """Add command to history"""
        self.command_history.append({
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'intent': intent,
            'result': result
        })
        # Keep last 20 commands
        if len(self.command_history) > 20:
            self.command_history.pop(0)

    def add_pending_confirmation(self, action_id: str, action_type: str, details: Dict[str, Any]):
        """Add pending confirmation requiring user approval"""
        self.pending_confirmations[action_id] = {
            'action_type': action_type,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(minutes=5)).isoformat()
        }

    def get_pending_confirmations(self) -> List[Dict[str, Any]]:
        """Get active pending confirmations"""
        now = datetime.now()
        active = []
        expired = []

        for action_id, confirmation in self.pending_confirmations.items():
            expiry = datetime.fromisoformat(confirmation['expires'])
            if now < expiry:
                active.append({**confirmation, 'action_id': action_id})
            else:
                expired.append(action_id)

        # Clean up expired confirmations
        for action_id in expired:
            del self.pending_confirmations[action_id]

        return active

class IntentClassifier:
    """Classifies user intent from natural language input"""

    def __init__(self):
        # Intent patterns with associated actions
        self.intent_patterns = {
            'status_check': {
                'patterns': [
                    r'how.*(?:are|is).*system',
                    r'(?:what|how).*(?:status|doing|running)',
                    r'system.*status',
                    r'everything.*ok',
                    r'how.*things',
                    r'what.*happening'
                ],
                'action': 'check_status',
                'confidence_threshold': 0.6
            },
            'health_check': {
                'patterns': [
                    r'health.*check',
                    r'run.*diagnostic',
                    r'check.*health',
                    r'system.*health'
                ],
                'action': 'health_check',
                'confidence_threshold': 0.7
            },
            'show_logs': {
                'patterns': [
                    r'show.*logs',
                    r'view.*logs',
                    r'see.*logs',
                    r'recent.*activity',
                    r'what.*happened'
                ],
                'action': 'show_logs',
                'confidence_threshold': 0.6
            },
            'show_metrics': {
                'patterns': [
                    r'show.*metrics',
                    r'performance.*metrics',
                    r'what.*(?:compliance|tribunals|uptime)',
                    r'metrics',
                    r'stats'
                ],
                'action': 'show_metrics',
                'confidence_threshold': 0.6
            },
            'tribunal_check': {
                'patterns': [
                    r'(?:check|show|see).*(?:tribunals?|alerts?)',
                    r'any.*tribunals?',
                    r'tribunal.*alerts?',
                    r'pending.*cases'
                ],
                'action': 'check_tribunals',
                'confidence_threshold': 0.7
            },
            'tribunal_action': {
                'patterns': [
                    r'(?:approve|uphold|confirm).*(?:tribunal|tribunals?)',
                    r'(?:release|clear).*(?:tribunal|tribunals?)',
                    r'(?:override|deny).*(?:tribunal|tribunals?)',
                    r'(?:escalate).*(?:tribunal|tribunals?)'
                ],
                'action': 'handle_tribunal',
                'confidence_threshold': 0.7
            },
            'service_restart': {
                'patterns': [
                    r'restart.*(?:services?|system|all)',
                    r'(?:start|stop).*(?:services?|system)',
                    r'reboot.*system'
                ],
                'action': 'restart_services',
                'confidence_threshold': 0.8
            },
            'confirmation': {
                'patterns': [
                    r'(?:yes|confirm|approve|do it|go ahead|proceed)',
                    r'(?:no|cancel|deny|stop|abort)',
                    r'(?:tell me more|explain|details)'
                ],
                'action': 'handle_confirmation',
                'confidence_threshold': 0.5
            },
            'context_recall': {
                'patterns': [
                    r'(?:do that|repeat|again)',
                    r'what.*last',
                    r'previous.*(?:command|action)',
                    r'go back'
                ],
                'action': 'recall_context',
                'confidence_threshold': 0.6
            },
            'help': {
                'patterns': [
                    r'help',
                    r'what.*can.*do',
                    r'commands',
                    r'options'
                ],
                'action': 'show_help',
                'confidence_threshold': 0.5
            },
            'memory_recall': {
                'patterns': [
                    r'memory.*stats',
                    r'memory.*status',
                    r'what.*remember',
                    r'learning.*stats'
                ],
                'action': 'memory_stats',
                'confidence_threshold': 0.6
            },
            'recall_topics': {
                'patterns': [
                    r'recall.*topics',
                    r'what.*talk.*about',
                    r'previous.*topics',
                    r'what.*we.*discuss',
                    r'remember.*asking'
                ],
                'action': 'recall_topics',
                'confidence_threshold': 0.6
            }
        }

        # Action confirmation requirements
        self.confirmation_required = {
            'restart_services': True,
            'handle_tribunal': True,
            'override_tribunal': True,
            'escalate_tribunal': True
        }

    def classify_intent(self, text: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Classify user intent from text input

        Returns: (intent_action, confidence_score, extracted_data)
        """
        text = text.lower().strip()

        best_match = None
        best_score = 0.0
        best_data = {}

        for intent_name, intent_config in self.intent_patterns.items():
            for pattern in intent_config['patterns']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Calculate confidence based on pattern match and context
                    confidence = self._calculate_confidence(text, pattern, match)

                    if confidence > best_score and confidence >= intent_config['confidence_threshold']:
                        best_match = intent_config['action']
                        best_score = confidence
                        best_data = self._extract_data(text, intent_name, match)

        return (best_match or 'unknown', best_score, best_data)

    def _calculate_confidence(self, text: str, pattern: str, match: re.Match) -> float:
        """Calculate confidence score for intent match"""
        # Base confidence from regex match
        confidence = 0.7

        # Boost for exact phrase matches
        if match.group(0).strip() == text.strip():
            confidence += 0.2

        # Boost for longer matches
        match_length = len(match.group(0))
        if match_length > 10:
            confidence += 0.1

        # Penalize for very short inputs that match broadly
        if len(text.split()) < 3 and confidence < 0.8:
            confidence -= 0.2

        return min(confidence, 1.0)

    def _extract_data(self, text: str, intent_name: str, match: re.Match) -> Dict[str, Any]:
        """Extract relevant data from the matched text"""
        data = {}

        if intent_name == 'tribunal_action':
            if 'approve' in text or 'uphold' in text or 'confirm' in text:
                data['tribunal_action'] = 'approve'
            elif 'release' in text or 'clear' in text:
                data['tribunal_action'] = 'release'
            elif 'override' in text or 'deny' in text:
                data['tribunal_action'] = 'override'
            elif 'escalate' in text:
                data['tribunal_action'] = 'escalate'

        elif intent_name == 'confirmation':
            if any(word in text for word in ['yes', 'confirm', 'approve', 'do it', 'go ahead', 'proceed']):
                data['confirmation'] = 'yes'
            elif any(word in text for word in ['no', 'cancel', 'deny', 'stop', 'abort']):
                data['confirmation'] = 'no'
            elif any(word in text for word in ['tell me more', 'explain', 'details']):
                data['confirmation'] = 'details'

        return data

class AthenaConversationEngine:
    """Main conversational engine for Athena"""

    def __init__(self):
        self.copilot = AthenaOpsCopilot()
        self.intent_classifier = IntentClassifier()
        self.context = ConversationContext()
        # Import memory system locally to avoid circular imports
        from athena_memory_system import AthenaMemorySystem
        self.memory_system = AthenaMemorySystem()
        self.conversation_log = []  # Track current conversation
        self.personality = {
            'greeting': "Hello! I'm Athena, your AI Republic operations assistant. How can I help you today?",
            'farewell': "Goodbye! The AI Republic continues operating autonomously.",
            'unknown_command': "I'm not sure I understand that command. Try asking about system status, logs, metrics, or tribunals.",
            'confirmation_request': "Are you sure you want to {action}? This will {consequence}.",
            'action_confirmed': "Confirmed. {action} executed successfully.",
            'action_cancelled': "Action cancelled.",
            'need_more_info': "I need more information to complete that request. Could you clarify?",
            'context_recall': "Referring to your previous request: {previous_action}",
            'error': "I encountered an error: {error}",
            'learned_suggestion': "Based on your past usage, you might also want to: {suggestion}",
            'memory_recall': "I remember you previously asked about: {previous_topic}"
        }

    def process_input(self, user_input: str) -> str:
        """Process user input and return conversational response"""

        # Log user input
        self.conversation_log.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })

        # Classify intent
        intent, confidence, data = self.intent_classifier.classify_intent(user_input)

        # Get memory-based enhancements
        memory_suggestions = self.memory_system.get_personalized_suggestions(user_input)
        predicted_next = self.memory_system.predict_next_intent(intent) if intent != 'unknown' else None

        # Update context
        self.context.add_command_history(user_input, intent, "processing")

        # Handle intent
        success = True
        try:
            if intent == 'unknown':
                response = self._handle_unknown_command(user_input)
                success = False
            elif intent in ['status_check', 'health_check', 'show_logs', 'show_metrics']:
                response = self._handle_informational_command(intent, data)
            elif intent == 'check_tribunals':
                response = self._handle_tribunal_check()
            elif intent in ['handle_tribunal', 'tribunal_action']:
                response = self._handle_tribunal_action(data)
            elif intent == 'restart_services':
                response = self._handle_service_restart()
            elif intent == 'handle_confirmation':
                response = self._handle_confirmation(data)
            elif intent == 'recall_context':
                response = self._handle_context_recall()
            elif intent == 'show_help':
                response = self._handle_help()
            elif intent in ['memory_stats', 'memory_status']:
                response = self.get_memory_stats()
            elif intent in ['recall_topics', 'what_did_we_talk_about', 'previous_topics']:
                response = self.recall_previous_topics()
            else:
                response = self._handle_unknown_command(user_input)
                success = False

            # Add memory-based enhancements
            if success and memory_suggestions:
                # Add a subtle suggestion based on learned patterns
                top_suggestion = memory_suggestions[0]
                if top_suggestion.lower() not in user_input.lower():
                    suggestion_text = self.personality['learned_suggestion'].format(suggestion=top_suggestion)
                    response += f"\n\n{suggestion_text}"

            # Add next action prediction if confident
            if predicted_next and predicted_next != intent:
                response += f"\n\nNext, you might want to check {predicted_next.replace('_', ' ')}."

        except Exception as e:
            response = self.personality['error'].format(error=str(e))
            success = False

        # Learn from this interaction
        from athena_memory_system import learn_from_interaction
        learn_from_interaction(user_input, intent, success, response)

        # Log response
        self.conversation_log.append({
            'role': 'assistant',
            'content': response,
            'intent': intent,
            'confidence': confidence,
            'success': success,
            'timestamp': datetime.now().isoformat()
        })

        # Update context with response
        self.context.add_command_history(user_input, intent, response)

        return response

    def save_conversation(self):
        """Save the current conversation to long-term memory"""
        if self.conversation_log:
            self.memory_system.save_conversation(self.context, self.conversation_log)
            self.conversation_log = []  # Clear for next conversation

    def get_memory_stats(self) -> str:
        """Get memory system statistics"""
        stats = self.memory_system.get_memory_stats()
        return f"""Memory System Status:
• Learned patterns: {stats['learned_patterns_count']}
• Command frequencies: {stats['command_frequencies']}
• Successful commands: {stats['successful_commands']}
• Conversation archives: {stats['conversation_archives']}
• Retention period: {stats['memory_retention_days']} days"""

    def recall_previous_topics(self) -> str:
        """Recall previously discussed topics"""
        favorites = self.memory_system.get_user_favorites()
        if favorites:
            top_topics = favorites[:5]
            return f"I remember you've frequently asked about: {', '.join(top_topics)}"
        return "I don't have enough conversation history to recall previous topics yet."

    def shutdown(self):
        """Clean shutdown - save conversation and memory"""
        self.save_conversation()
        self.memory_system.shutdown()

    def _handle_unknown_command(self, user_input: str) -> str:
        """Handle unrecognized commands with helpful suggestions"""
        # Try fuzzy matching for common typos
        suggestions = self._get_command_suggestions(user_input)

        if suggestions:
            return f"{self.personality['unknown_command']} Did you mean: {', '.join(suggestions[:3])}?"
        else:
            return self.personality['unknown_command']

    def _get_command_suggestions(self, user_input: str) -> List[str]:
        """Get command suggestions based on fuzzy matching"""
        common_commands = [
            "check status", "show logs", "system health", "view metrics",
            "check tribunals", "restart services", "show help"
        ]

        suggestions = []
        for cmd in common_commands:
            ratio = difflib.SequenceMatcher(None, user_input.lower(), cmd.lower()).ratio()
            if ratio > 0.6:
                suggestions.append(cmd)

        return suggestions

    def _handle_informational_command(self, intent: str, data: Dict[str, Any]) -> str:
        """Handle informational commands (status, logs, metrics)"""
        if intent == 'status_check':
            status = self.copilot.perform_health_check()
            if 'error' in status:
                return f"Status check failed: {status['error']}"

            briefing = self.copilot.analyze_status(status)
            response = self.copilot.generate_briefing_message(briefing)

            # Update context with current status
            self.context.update_context('last_status', status)
            self.context.update_context('last_briefing', briefing)

            return response

        elif intent == 'health_check':
            status = self.copilot.perform_health_check()
            if 'error' in status:
                return f"Health check failed: {status['error']}"

            overall = status.get('overall_status', 'UNKNOWN')
            compliance = status.get('metrics', {}).get('compliance_rate', 0) * 100

            if overall == 'HEALTHY':
                return f"System health is excellent. All services running, compliance at {compliance:.1f}%."
            elif overall == 'WARNING':
                return f"System health needs attention. Compliance at {compliance:.1f}%. Some services may need review."
            else:
                return "System health is critical. Immediate attention required."

        elif intent == 'show_logs':
            activity = self.copilot.check_recent_activity()
            if activity:
                log_lines = activity[-5:]  # Last 5 entries
                log_text = "\n".join(f"• {line}" for line in log_lines)
                return f"Recent system activity:\n{log_text}"
            else:
                return "No recent activity found in logs."

        elif intent == 'show_metrics':
            status = self.copilot.perform_health_check()
            if 'error' in status:
                return f"Metrics check failed: {status['error']}"

            metrics = status.get('metrics', {})
            compliance = metrics.get('compliance_rate', 0) * 100
            tribunals = metrics.get('tribunals_today', 0)
            uptime = metrics.get('system_uptime', 'Unknown')

            return f"Current metrics:\n• Compliance: {compliance:.1f}%\n• Tribunals Today: {tribunals}\n• System Uptime: {uptime}"

    def _handle_tribunal_check(self) -> str:
        """Handle tribunal checking commands"""
        alerts = self.copilot.check_tribunal_alerts()

        if not alerts:
            return "No tribunal alerts currently active. System is operating within normal parameters."

        alert_count = len(alerts)
        if alert_count == 1:
            alert = alerts[0]
            severity = alert.get('severity', 'UNKNOWN')
            return f"One tribunal alert active: {alert['message']} (Severity: {severity})"
        else:
            return f"{alert_count} tribunal alerts active. Use 'show tribunal details' for more information."

    def _handle_tribunal_action(self, data: Dict[str, Any]) -> str:
        """Handle tribunal action commands"""
        action = data.get('tribunal_action', 'unknown')

        if action not in ['approve', 'release', 'override', 'escalate']:
            return "Please specify the tribunal action: approve, release, override, or escalate."

        # Check if confirmation is required
        if self.intent_classifier.confirmation_required.get('handle_tribunal', True):
            action_id = f"tribunal_{int(time.time())}"
            self.context.add_pending_confirmation(action_id, 'tribunal_action', {
                'action': action,
                'description': f"{action} tribunal decision"
            })

            consequence = {
                'approve': 'uphold the automated tribunal decision',
                'release': 'release the agent from quarantine',
                'override': 'override the tribunal with human judgment',
                'escalate': 'send to oversight council for review'
            }.get(action, 'perform this tribunal action')

            return self.personality['confirmation_request'].format(
                action=f"{action} tribunal",
                consequence=consequence
            )
        else:
            # Execute directly (for low-risk actions)
            return self._execute_tribunal_action(action)

    def _handle_service_restart(self) -> str:
        """Handle service restart commands"""
        # Always require confirmation for restarts
        action_id = f"restart_{int(time.time())}"
        self.context.add_pending_confirmation(action_id, 'service_restart', {
            'action': 'restart',
            'description': 'restart all AI Republic services'
        })

        return self.personality['confirmation_request'].format(
            action="restart AI Republic services",
            consequence="temporarily interrupt system operations"
        )

    def _handle_confirmation(self, data: Dict[str, Any]) -> str:
        """Handle confirmation responses"""
        confirmation = data.get('confirmation', 'unknown')

        if confirmation == 'yes':
            # Execute the most recent pending confirmation
            pending = self.context.get_pending_confirmations()
            if pending:
                latest = pending[-1]  # Most recent
                action_id = latest['action_id']
                action_type = latest['action_type']

                # Remove from pending
                if action_id in self.context.pending_confirmations:
                    del self.context.pending_confirmations[action_id]

                # Execute action
                if action_type == 'tribunal_action':
                    action = latest['details']['action']
                    result = self._execute_tribunal_action(action)
                elif action_type == 'service_restart':
                    result = self._execute_service_restart()
                else:
                    result = "Action executed successfully."

                return self.personality['action_confirmed'].format(action=result)
            else:
                return "No pending actions to confirm."

        elif confirmation == 'no':
            # Cancel pending confirmations
            self.context.pending_confirmations.clear()
            return self.personality['action_cancelled']

        elif confirmation == 'details':
            pending = self.context.get_pending_confirmations()
            if pending:
                latest = pending[-1]
                return f"Pending action: {latest['details']['description']}. Type 'yes' to confirm or 'no' to cancel."
            else:
                return "No pending actions."

        return "Confirmation response not recognized."

    def _handle_context_recall(self) -> str:
        """Handle context recall commands"""
        if self.context.command_history:
            last_command = self.context.command_history[-1]
            return self.personality['context_recall'].format(
                previous_action=f"'{last_command['command']}' which resulted in: {last_command['result'][:100]}..."
            )
        else:
            return "No previous commands found in this session."

    def _handle_help(self) -> str:
        """Handle help commands"""
        help_text = """
I can help you with AI Republic operations. Try asking:

• Status & Health
  - "how is the system running?"
  - "check system health"
  - "what's the current status?"

• Logs & Activity
  - "show me the logs"
  - "recent activity"
  - "what happened today?"

• Metrics & Performance
  - "show metrics"
  - "compliance status"
  - "performance stats"

• Tribunal Management
  - "check tribunals"
  - "approve tribunal"
  - "release quarantines"

• System Control
  - "restart services"
  - "system diagnostics"

• Memory & Learning
  - "what do you remember?"
  - "recall previous topics"
  - "memory stats"

• General
  - "help" or "what can you do?"
  - "quit" to exit

Just ask in plain English - I learn from our conversations!
        """
        return help_text.strip()

    def _execute_tribunal_action(self, action: str) -> str:
        """Execute tribunal action (placeholder for actual implementation)"""
        # In real implementation, this would call the tribunal system
        action_descriptions = {
            'approve': 'Tribunal decision upheld. Agent remains under automated management.',
            'release': 'Agent released from quarantine. Monitoring continued.',
            'override': 'Tribunal overridden with human judgment. Manual review initiated.',
            'escalate': 'Case escalated to oversight council. Awaiting human review.'
        }
        return action_descriptions.get(action, f"Tribunal {action} action completed.")

    def _execute_service_restart(self) -> str:
        """Execute service restart (placeholder for actual implementation)"""
        # In real implementation, this would call systemctl
        return "All AI Republic services restarted successfully."

    def start_conversation(self):
        """Start interactive conversation session"""
        print("🤖 Athena Ops Co-Pilot - Conversational Mode")
        print("=" * 50)
        print(self.personality['greeting'])
        print("\n(Type 'help' for available commands, 'quit' to exit)")
        print()

        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print(f"🤖 {self.personality['farewell']}")
                    break

                response = self.process_input(user_input)
                print(f"🤖 {response}")

            except KeyboardInterrupt:
                print(f"\n🤖 {self.personality['farewell']}")
                break
            except Exception as e:
                error_msg = self.personality['error'].format(error=str(e))
                print(f"🤖 {error_msg}")

def main():
    """Main entry point for conversational Athena"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena Conversational AI Assistant')
    parser.add_argument('--mode', choices=['chat', 'single'], default='chat',
                       help='Interaction mode')
    parser.add_argument('--input', help='Single input for processing (when mode=single)')

    args = parser.parse_args()

    engine = AthenaConversationEngine()

    if args.mode == 'single' and args.input:
        response = engine.process_input(args.input)
        print(f"🤖 {response}")
    else:
        engine.start_conversation()

if __name__ == '__main__':
    main()
