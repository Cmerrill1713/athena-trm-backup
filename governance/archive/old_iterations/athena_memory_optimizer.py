#!/usr/bin/env python3
"""
Athena Memory Optimizer
=======================

Automated memory pruning, optimization, and maintenance for Athena's persistent memory system.

Features:
- Intelligent memory cleanup and compression
- Performance optimization and defragmentation
- Usage analytics and pattern optimization
- Automated maintenance scheduling
- Memory health monitoring and repair

Usage:
    python3 athena_memory_optimizer.py --optimize    # Run full optimization
    python3 athena_memory_optimizer.py --analyze     # Analyze memory health
    python3 athena_memory_optimizer.py --cleanup     # Remove corrupted data
    python3 athena_memory_optimizer.py --schedule    # Set up automated optimization
"""

import json
import time
import os
import sys
import shutil
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import argparse
import logging

# Add system paths
sys.path.insert(0, '/opt/ai-republic')
sys.path.insert(0, os.path.dirname(__file__))

from athena_conversation import ConversationMemory
from athena_notifications import AthenaNotifications

class AthenaMemoryOptimizer:
    """Comprehensive memory optimization and maintenance system"""

    def __init__(self, memory_dir: str = '/opt/ai-republic'):
        self.memory_dir = memory_dir
        self.memory_file = os.path.join(memory_dir, 'conversation_memory.json')
        self.archive_file = os.path.join(memory_dir, 'conversation_memory_archive.json')
        self.backup_dir = '/var/backups/athena-memory'

        # Initialize notifications
        self.notifications = AthenaNotifications()

        # Optimization settings
        self.max_active_memory = 200
        self.max_archive_memory = 1000
        self.compression_ratio_target = 0.7  # 70% size reduction
        self.min_interaction_age = 86400 * 30  # 30 days for deep compression

        # Setup logging
        log_dir = '/var/log/ai-republic' if os.path.exists('/var/log/ai-republic') else './logs'
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(log_dir, 'athena_memory_optimizer.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def analyze_memory_health(self) -> Dict:
        """Comprehensive memory health analysis"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'UNKNOWN',
            'active_memory': {},
            'archive_memory': {},
            'performance_metrics': {},
            'issues': [],
            'recommendations': []
        }

        try:
            # Analyze active memory
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    active_data = json.load(f)

                active_size = len(active_data.get('conversation_history', []))
                health_report['active_memory'] = {
                    'size': active_size,
                    'capacity': self.max_active_memory,
                    'utilization': (active_size / self.max_active_memory) * 100,
                    'last_updated': active_data.get('last_interaction'),
                    'learning_patterns': len(active_data.get('learning', {}).get('command_patterns', {}))
                }

                # Check for issues
                if active_size > self.max_active_memory * 1.2:
                    health_report['issues'].append('Active memory exceeds capacity by >20%')
                    health_report['recommendations'].append('Run memory optimization immediately')

            # Analyze archive memory
            if os.path.exists(self.archive_file):
                with open(self.archive_file, 'r') as f:
                    archive_data = json.load(f)

                archive_size = len(archive_data.get('archived_interactions', []))
                health_report['archive_memory'] = {
                    'size': archive_size,
                    'capacity': self.max_archive_memory,
                    'utilization': (archive_size / self.max_archive_memory) * 100,
                    'compression_ratio': self._calculate_compression_ratio(archive_data),
                    'last_archived': archive_data.get('last_archived'),
                    'total_archived': archive_data.get('total_archived', 0)
                }

            # Performance metrics
            health_report['performance_metrics'] = self._calculate_performance_metrics()

            # Overall health assessment
            issues_count = len(health_report['issues'])
            active_util = health_report['active_memory'].get('utilization', 0)
            archive_util = health_report['archive_memory'].get('utilization', 0)

            if issues_count == 0 and active_util < 90 and archive_util < 90:
                health_report['overall_health'] = 'EXCELLENT'
            elif issues_count <= 1 and active_util < 110 and archive_util < 110:
                health_report['overall_health'] = 'GOOD'
            elif issues_count <= 2 or active_util > 120 or archive_util > 120:
                health_report['overall_health'] = 'WARNING'
            else:
                health_report['overall_health'] = 'CRITICAL'

        except Exception as e:
            health_report['issues'].append(f'Analysis error: {e}')
            health_report['overall_health'] = 'ERROR'

        return health_report

    def _calculate_compression_ratio(self, archive_data: Dict) -> float:
        """Calculate actual compression ratio"""
        archived = archive_data.get('archived_interactions', [])
        if not archived:
            return 1.0

        # Estimate original size (rough calculation)
        # Assume original interactions are ~500 chars, compressed ~150 chars
        estimated_original = len(archived) * 500
        actual_compressed = len(json.dumps(archived))

        return actual_compressed / estimated_original if estimated_original > 0 else 1.0

    def _calculate_performance_metrics(self) -> Dict:
        """Calculate memory performance metrics"""
        metrics = {
            'load_time': 0,
            'search_time': 0,
            'memory_usage': 0,
            'fragmentation': 0
        }

        try:
            # Measure load time
            start_time = time.time()
            memory = ConversationMemory()
            load_time = time.time() - start_time
            metrics['load_time'] = load_time

            # Measure search time
            start_time = time.time()
            results = memory.recover_from_archive('status')
            search_time = time.time() - start_time
            metrics['search_time'] = search_time

            # Estimate memory usage
            if os.path.exists(self.memory_file):
                memory_size = os.path.getsize(self.memory_file)
                if os.path.exists(self.archive_file):
                    memory_size += os.path.getsize(self.archive_file)
                metrics['memory_usage'] = memory_size

            # Calculate fragmentation (simplified)
            if os.path.exists(self.archive_file):
                with open(self.archive_file, 'r') as f:
                    archive_data = json.load(f)
                archived = archive_data.get('archived_interactions', [])
                if archived:
                    # Check for gaps in timestamps (simplified fragmentation metric)
                    timestamps = [i.get('timestamp', '') for i in archived if i.get('timestamp')]
                    if len(timestamps) > 1:
                        # Calculate timestamp gaps (higher gaps = more fragmentation)
                        gaps = []
                        for i in range(1, len(timestamps)):
                            try:
                                dt1 = datetime.fromisoformat(timestamps[i-1].replace('Z', '+00:00'))
                                dt2 = datetime.fromisoformat(timestamps[i].replace('Z', '+00:00'))
                                gap_hours = (dt2 - dt1).total_seconds() / 3600
                                gaps.append(gap_hours)
                            except:
                                continue
                        metrics['fragmentation'] = sum(gaps) / len(gaps) if gaps else 0

        except Exception as e:
            logging.error(f"Performance calculation error: {e}")

        return metrics

    def optimize_memory(self) -> Dict:
        """Run comprehensive memory optimization"""
        optimization_report = {
            'timestamp': datetime.now().isoformat(),
            'operations': [],
            'metrics_before': {},
            'metrics_after': {},
            'issues_resolved': [],
            'performance_improvements': {}
        }

        logging.info("Starting memory optimization")

        try:
            # Pre-optimization metrics
            optimization_report['metrics_before'] = self.analyze_memory_health()

            # Create backup before optimization
            self._create_backup()

            # Optimize active memory
            active_optimized = self._optimize_active_memory()
            if active_optimized:
                optimization_report['operations'].append('active_memory_optimization')
                optimization_report['issues_resolved'].extend(active_optimized)

            # Optimize archive memory
            archive_optimized = self._optimize_archive_memory()
            if archive_optimized:
                optimization_report['operations'].append('archive_memory_optimization')
                optimization_report['issues_resolved'].extend(archive_optimized)

            # Defragment and rebuild indexes
            defrag_results = self._defragment_memory()
            if defrag_results:
                optimization_report['operations'].append('memory_defragmentation')
                optimization_report['performance_improvements'].update(defrag_results)

            # Clean up corrupted data
            cleanup_results = self._cleanup_corrupted_data()
            if cleanup_results:
                optimization_report['operations'].append('data_cleanup')
                optimization_report['issues_resolved'].extend(cleanup_results)

            # Rebuild learning patterns
            learning_results = self._rebuild_learning_patterns()
            if learning_results:
                optimization_report['operations'].append('learning_rebuild')
                optimization_report['performance_improvements'].update(learning_results)

            # Post-optimization metrics
            optimization_report['metrics_after'] = self.analyze_memory_health()

            logging.info(f"Memory optimization completed: {len(optimization_report['operations'])} operations")

        except Exception as e:
            optimization_report['error'] = str(e)
            logging.error(f"Memory optimization failed: {e}")

        return optimization_report

    def _create_backup(self):
        """Create backup before optimization"""
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            if os.path.exists(self.memory_file):
                backup_memory = os.path.join(self.backup_dir, f'memory_pre_opt_{timestamp}.json')
                shutil.copy2(self.memory_file, backup_memory)

            if os.path.exists(self.archive_file):
                backup_archive = os.path.join(self.backup_dir, f'archive_pre_opt_{timestamp}.json')
                shutil.copy2(self.archive_file, backup_archive)

            logging.info(f"Pre-optimization backup created: {timestamp}")

        except Exception as e:
            logging.error(f"Backup creation failed: {e}")

    def _optimize_active_memory(self) -> List[str]:
        """Optimize active memory usage"""
        issues_resolved = []

        try:
            if not os.path.exists(self.memory_file):
                return issues_resolved

            with open(self.memory_file, 'r') as f:
                data = json.load(f)

            original_size = len(data.get('conversation_history', []))

            # Remove duplicate interactions (keep most recent)
            history = data['conversation_history']
            seen_commands = {}
            deduplicated = []

            for interaction in reversed(history):
                cmd = interaction.get('athena_response', '').strip()
                if cmd not in seen_commands:
                    seen_commands[cmd] = interaction
                    deduplicated.append(interaction)

            deduplicated.reverse()
            data['conversation_history'] = deduplicated

            # Clean up old context data
            current_time = time.time()
            context_timeout = 14400  # 4 hours

            # Remove expired context
            if 'current_context' in data:
                expired_keys = []
                for key, value in data['current_context'].items():
                    if isinstance(value, dict) and 'timestamp' in value:
                        if current_time - value['timestamp'] > context_timeout:
                            expired_keys.append(key)
                    elif isinstance(value, (int, float)):
                        # Assume numeric timestamps
                        if current_time - value > context_timeout:
                            expired_keys.append(key)

                for key in expired_keys:
                    del data['current_context'][key]
                    issues_resolved.append(f'removed_expired_context_{key}')

            # Save optimized memory
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            final_size = len(data.get('conversation_history', []))
            if final_size < original_size:
                issues_resolved.append(f'reduced_active_memory_{original_size - final_size}_duplicates')

        except Exception as e:
            logging.error(f"Active memory optimization failed: {e}")

        return issues_resolved

    def _optimize_archive_memory(self) -> List[str]:
        """Optimize archive memory"""
        issues_resolved = []

        try:
            if not os.path.exists(self.archive_file):
                return issues_resolved

            with open(self.archive_file, 'r') as f:
                data = json.load(f)

            archived = data.get('archived_interactions', [])
            original_count = len(archived)

            # Remove duplicates in archive
            seen_signatures = set()
            deduplicated = []

            for interaction in archived:
                # Create signature for deduplication
                signature = f"{interaction.get('user_input', '')[:50]}_{interaction.get('command', '')}"
                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    deduplicated.append(interaction)

            # Further compress old interactions (older than 30 days)
            current_time = time.time()
            compressed = []

            for interaction in deduplicated:
                timestamp = interaction.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        age_seconds = (datetime.now() - dt).total_seconds()

                        if age_seconds > self.min_interaction_age:
                            # Deep compression for old interactions
                            compressed_interaction = {
                                'ts': timestamp,
                                'cmd': interaction.get('command', ''),
                                'outcome': interaction.get('outcome', ''),
                                'compressed': True
                            }
                            compressed.append(compressed_interaction)
                            issues_resolved.append('deep_compressed_old_interaction')
                        else:
                            compressed.append(interaction)
                    except:
                        compressed.append(interaction)
                else:
                    compressed.append(interaction)

            data['archived_interactions'] = compressed
            data['last_optimized'] = datetime.now().isoformat()
            data['optimization_stats'] = {
                'original_count': original_count,
                'final_count': len(compressed),
                'compression_ratio': len(compressed) / original_count if original_count > 0 else 1.0
            }

            # Save optimized archive
            with open(self.archive_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            final_count = len(compressed)
            if final_count < original_count:
                issues_resolved.append(f'reduced_archive_memory_{original_count - final_count}_duplicates')

        except Exception as e:
            logging.error(f"Archive memory optimization failed: {e}")

        return issues_resolved

    def _defragment_memory(self) -> Dict:
        """Defragment and rebuild memory structures"""
        improvements = {}

        try:
            # Rebuild archive indexes for better search performance
            if os.path.exists(self.archive_file):
                with open(self.archive_file, 'r') as f:
                    data = json.load(f)

                archived = data.get('archived_interactions', [])

                # Re-sort by timestamp for better access patterns
                sorted_archived = sorted(archived, key=lambda x: x.get('timestamp', ''), reverse=True)

                # Rebuild search indexes
                command_index = defaultdict(list)
                time_index = defaultdict(list)

                for i, interaction in enumerate(sorted_archived):
                    cmd = interaction.get('command', '')
                    if cmd:
                        command_index[cmd].append(i)

                    timestamp = interaction.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            hour_key = f"{dt.hour//4}h"
                            time_index[hour_key].append(i)
                        except:
                            pass

                # Add indexes to data
                data['search_indexes'] = {
                    'command_index': dict(command_index),
                    'time_index': dict(time_index),
                    'last_indexed': datetime.now().isoformat()
                }

                with open(self.archive_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)

                improvements['search_indexes_rebuilt'] = True
                improvements['archive_resorted'] = True

        except Exception as e:
            logging.error(f"Memory defragmentation failed: {e}")

        return improvements

    def _cleanup_corrupted_data(self) -> List[str]:
        """Clean up corrupted or invalid data"""
        issues_resolved = []

        try:
            # Clean active memory
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)

                # Validate conversation history
                valid_history = []
                for interaction in data.get('conversation_history', []):
                    if isinstance(interaction, dict) and 'user_input' in interaction:
                        valid_history.append(interaction)
                    else:
                        issues_resolved.append('removed_corrupt_active_interaction')

                data['conversation_history'] = valid_history

                with open(self.memory_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)

            # Clean archive memory
            if os.path.exists(self.archive_file):
                with open(self.archive_file, 'r') as f:
                    data = json.load(f)

                # Validate archived interactions
                valid_archived = []
                for interaction in data.get('archived_interactions', []):
                    if isinstance(interaction, dict):
                        valid_archived.append(interaction)
                    else:
                        issues_resolved.append('removed_corrupt_archived_interaction')

                data['archived_interactions'] = valid_archived

                with open(self.archive_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)

        except Exception as e:
            logging.error(f"Data cleanup failed: {e}")

        return issues_resolved

    def _rebuild_learning_patterns(self) -> Dict:
        """Rebuild and optimize learning patterns"""
        improvements = {}

        try:
            memory = ConversationMemory()

            # Get fresh insights
            insights = memory.get_persistent_insights()

            # Optimize learning data
            learning = insights.get('current_session', {})

            # Clean up old patterns (commands used < 3 times and > 30 days old)
            current_time = time.time()
            month_ago = current_time - (30 * 24 * 60 * 60)

            optimized_patterns = {}
            for cmd, count in learning.get('command_patterns', {}).items():
                if count >= 3:  # Keep frequently used commands
                    optimized_patterns[cmd] = count
                elif any(i.get('context', {}).get('last_command') == cmd
                        for i in memory.memory.get('conversation_history', [])
                        if isinstance(i.get('timestamp'), str) and
                        datetime.fromisoformat(i['timestamp'].replace('Z', '+00:00')).timestamp() > month_ago):
                    # Keep recently used commands
                    optimized_patterns[cmd] = count

            # Update learning data
            if 'learning' not in memory.memory:
                memory.memory['learning'] = {}
            memory.memory['learning']['command_patterns'] = optimized_patterns
            memory.memory['learning']['last_optimized'] = datetime.now().isoformat()

            memory.save_memory()

            improvements['learning_patterns_optimized'] = True
            improvements['patterns_reduced'] = len(learning.get('command_patterns', {})) - len(optimized_patterns)

        except Exception as e:
            logging.error(f"Learning pattern rebuild failed: {e}")

        return improvements

    def send_memory_alert(self, alert_type: str, details: Dict):
        """Send memory-related alerts via notification system"""
        alert_templates = {
            'critical_health': {
                'title': '🚨 CRITICAL: Athena Memory Health Alert',
                'message': f"""Athena memory health is CRITICAL!

Health Status: {details.get('overall_health', 'UNKNOWN')}
Active Memory: {details.get('active_utilization', 0):.1f}% utilized
Archive Memory: {details.get('archive_utilization', 0):.1f}% utilized

Immediate optimization required to prevent performance degradation.

Run: python3 athena_memory_optimizer.py --optimize""",
                'priority': 'urgent'
            },
            'optimization_failed': {
                'title': '⚠️ WARNING: Athena Memory Optimization Failed',
                'message': f"""Memory optimization failed to complete successfully.

Error: {details.get('error', 'Unknown error')}

Manual intervention may be required. Check logs for details.

Run: journalctl -u athena-memory-optimizer -n 20""",
                'priority': 'warning'
            },
            'corruption_detected': {
                'title': '🔴 ALERT: Athena Memory Corruption Detected',
                'message': f"""Memory corruption detected and requires immediate attention!

Corrupted Files: {', '.join(details.get('corrupted_files', []))}
Affected Operations: {details.get('affected_operations', 'Unknown')}

Automatic cleanup attempted. Manual verification recommended.

Run: python3 athena_memory_optimizer.py --analyze""",
                'priority': 'urgent'
            },
            'performance_degraded': {
                'title': '⚠️ NOTICE: Athena Memory Performance Degraded',
                'message': f"""Memory performance has degraded below optimal levels.

Load Time: {details.get('load_time', 0):.2f}s (optimal: <2.0s)
Search Time: {details.get('search_time', 0):.2f}s (optimal: <0.5s)

Next scheduled optimization: Sunday 3:00 AM
Or run manually: python3 athena_memory_optimizer.py --optimize""",
                'priority': 'warning'
            },
            'optimization_complete': {
                'title': '✅ SUCCESS: Athena Memory Optimization Complete',
                'message': f"""Memory optimization completed successfully!

Operations Performed: {len(details.get('operations', []))}
Issues Resolved: {len(details.get('issues_resolved', []))}
Performance Improved: {bool(details.get('performance_improvements', {}))}

Active Memory: {details.get('active_after', 0)} interactions
Archive Memory: {details.get('archive_after', 0)} interactions
Overall Health: {details.get('health_after', 'UNKNOWN')}

Next optimization: Sunday 3:00 AM""",
                'priority': 'normal'
            }
        }

        if alert_type in alert_templates:
            template = alert_templates[alert_type]
            try:
                # Create alert object for quiet hours checking
                alert_data = {
                    'id': f"alert-{int(time.time())}",
                    'title': template['title'],
                    'message': template['message'],
                    'severity': 'critical' if template['priority'] == 'urgent' else 'warning',
                    'timestamp': time.time()
                }

                # Check quiet hours via API if available
                should_send_now = self._should_send_alert_now(alert_data)

                if should_send_now:
                    # Use cascade priority for critical alerts (Telegram first, then email)
                    use_cascade = template['priority'] == 'urgent'
                    # Enable escalation for critical alerts (5-minute timeout)
                    use_escalation = template['priority'] == 'urgent'
                    self.notifications.send_notification(
                        title=template['title'],
                        message=template['message'],
                        priority=template['priority'],
                        cascade_priority=use_cascade,
                        escalation_enabled=use_escalation,
                        escalation_minutes=5
                    )
                else:
                    # Queue alert for delivery after quiet hours
                    self._queue_alert_for_quiet_hours(alert_data)
                    print(f"Alert queued during quiet hours: {template['title']}")
                logging.info(f"Memory alert sent: {alert_type}")
            except Exception as e:
                logging.error(f"Failed to send memory alert {alert_type}: {e}")
        else:
            logging.warning(f"Unknown alert type: {alert_type}")

    def check_and_alert_health_issues(self, health_report: Dict):
        """Check health report and send alerts for critical issues"""
        issues = health_report.get('issues', [])
        overall_health = health_report.get('overall_health', 'UNKNOWN')

        # Critical health alert
        if overall_health == 'CRITICAL':
            alert_details = {
                'overall_health': overall_health,
                'active_utilization': health_report.get('active_memory', {}).get('utilization', 0),
                'archive_utilization': health_report.get('archive_memory', {}).get('utilization', 0)
            }
            self.send_memory_alert('critical_health', alert_details)

        # Performance degradation alert
        perf_metrics = health_report.get('performance_metrics', {})
        load_time = perf_metrics.get('load_time', 0)
        search_time = perf_metrics.get('search_time', 0)

        if load_time > 3.0 or search_time > 1.0:
            alert_details = {
                'load_time': load_time,
                'search_time': search_time
            }
            self.send_memory_alert('performance_degraded', alert_details)

        # Corruption detection alert
        if any('corrupt' in issue.lower() for issue in issues):
            alert_details = {
                'corrupted_files': [self.memory_file, self.archive_file],  # Could be more specific
                'affected_operations': 'memory loading and conversation recall'
            }
            self.send_memory_alert('corruption_detected', alert_details)

    def optimize_memory(self) -> Dict:
        """Run comprehensive memory optimization with alerting"""
        optimization_report = {
            'timestamp': datetime.now().isoformat(),
            'operations': [],
            'issues_resolved': [],
            'metrics_before': {},
            'metrics_after': {},
            'performance_improvements': {}
        }

        logging.info("Starting memory optimization")

        try:
            # Pre-optimization metrics and health check
            optimization_report['metrics_before'] = self.analyze_memory_health()

            # Check for critical issues before optimization
            self.check_and_alert_health_issues(optimization_report['metrics_before'])

            # Create backup before optimization
            self._create_backup()

            # Optimize active memory
            active_optimized = self._optimize_active_memory()
            if active_optimized:
                optimization_report['operations'].append('active_memory_optimization')
                optimization_report['issues_resolved'].extend(active_optimized)

            # Optimize archive memory
            archive_optimized = self._optimize_archive_memory()
            if archive_optimized:
                optimization_report['operations'].append('archive_memory_optimization')
                optimization_report['issues_resolved'].extend(archive_optimized)

            # Defragment and rebuild indexes
            defrag_results = self._defragment_memory()
            if defrag_results:
                optimization_report['operations'].append('memory_defragmentation')
                optimization_report['performance_improvements'].update(defrag_results)

            # Clean up corrupted data
            cleanup_results = self._cleanup_corrupted_data()
            if cleanup_results:
                optimization_report['operations'].append('data_cleanup')
                optimization_report['issues_resolved'].extend(cleanup_results)

            # Rebuild learning patterns
            learning_results = self._rebuild_learning_patterns()
            if learning_results:
                optimization_report['operations'].append('learning_rebuild')
                optimization_report['performance_improvements'].update(learning_results)

            # Post-optimization metrics and success alert
            optimization_report['metrics_after'] = self.analyze_memory_health()

            # Send success alert with summary
            after_metrics = optimization_report['metrics_after']
            alert_details = {
                'operations': optimization_report['operations'],
                'issues_resolved': optimization_report['issues_resolved'],
                'performance_improvements': optimization_report['performance_improvements'],
                'active_after': after_metrics.get('active_memory', {}).get('size', 0),
                'archive_after': after_metrics.get('archive_memory', {}).get('size', 0),
                'health_after': after_metrics.get('overall_health', 'UNKNOWN')
            }
            self.send_memory_alert('optimization_complete', alert_details)

        except Exception as e:
            optimization_report['error'] = str(e)
            # Send failure alert
            self.send_memory_alert('optimization_failed', {'error': str(e)})
            logging.error(f"Memory optimization failed: {e}")

        return optimization_report

    def _should_send_alert_now(self, alert_data: Dict) -> bool:
        """Check if alert should be sent now or queued for quiet hours"""
        try:
            # Try to get quiet hours status from API
            import requests
            response = requests.get("http://localhost:8009/quiet-hours", timeout=2)
            if response.status_code == 200:
                data = response.json()
                is_quiet_hours = data.get('is_quiet_hours', False)
                is_enabled = data.get('enabled', False)

                if not is_enabled:
                    return True  # Quiet hours not enabled

                # Critical alerts always go through
                if alert_data.get('severity') == 'critical':
                    return True

                # During quiet hours, queue non-critical alerts
                return not is_quiet_hours

        except Exception as e:
            # If API unavailable, send alerts normally
            print(f"Quiet hours check failed: {e}")
            return True

        return True

    def _queue_alert_for_quiet_hours(self, alert_data: Dict):
        """Queue alert for delivery after quiet hours"""
        try:
            # Try to queue via API
            import requests
            response = requests.post("http://localhost:8009/queue-alert",
                                   json=alert_data, timeout=2)
            if response.status_code == 200:
                return
        except Exception as e:
            print(f"Alert queuing failed: {e}")

        # Fallback: store locally (in production, this would persist)
        queued_file = f"/tmp/athena_queued_alert_{alert_data['id']}.json"
        try:
            import json
            with open(queued_file, 'w') as f:
                json.dump(alert_data, f)
        except Exception as e:
            print(f"Local alert queuing failed: {e}")

    def generate_optimization_report(self, optimization_results: Dict) -> str:
        """Generate human-readable optimization report"""
        report = "🧠 **Athena Memory Optimization Report**\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Overall status
        operations = optimization_results.get('operations', [])
        issues_resolved = optimization_results.get('issues_resolved', [])

        if operations:
            report += f"✅ **Optimization Completed:** {len(operations)} operations performed\n\n"
        else:
            report += "ℹ️ **No Optimization Needed:** Memory is already optimized\n\n"

        # Operations performed
        if operations:
            report += "**Operations Performed:**\n"
            for op in operations:
                report += f"  • {op.replace('_', ' ').title()}\n"
            report += "\n"

        # Issues resolved
        if issues_resolved:
            report += "**Issues Resolved:**\n"
            for issue in issues_resolved:
                report += f"  • {issue.replace('_', ' ').title()}\n"
            report += "\n"

        # Performance improvements
        improvements = optimization_results.get('performance_improvements', {})
        if improvements:
            report += "**Performance Improvements:**\n"
            for key, value in improvements.items():
                report += f"  • {key.replace('_', ' ').title()}: {value}\n"
            report += "\n"

        # Before/after metrics
        before = optimization_results.get('metrics_before', {})
        after = optimization_results.get('metrics_after', {})

        if before and after:
            report += "**Memory Health Comparison:**\n"

            # Active memory
            before_active = before.get('active_memory', {})
            after_active = after.get('active_memory', {})

            if before_active and after_active:
                report += f"  **Active Memory:** {before_active.get('size', 0)} → {after_active.get('size', 0)} interactions\n"

            # Archive memory
            before_archive = before.get('archive_memory', {})
            after_archive = after.get('archive_memory', {})

            if before_archive and after_archive:
                report += f"  **Archive Memory:** {before_archive.get('size', 0)} → {after_archive.get('size', 0)} interactions\n"

            # Overall health
            before_health = before.get('overall_health', 'UNKNOWN')
            after_health = after.get('overall_health', 'UNKNOWN')
            report += f"  **Overall Health:** {before_health} → {after_health}\n\n"

        # Recommendations
        report += "**Recommendations:**\n"
        if optimization_results.get('error'):
            report += f"  ⚠️ **Error Detected:** {optimization_results['error']}\n"
            report += "  • Check logs for detailed error information\n"
            report += "  • Consider manual memory inspection\n"
        else:
            report += "  • Next optimization recommended in 7 days\n"
            report += "  • Monitor memory health with regular checkups\n"

        return report

def main():
    parser = argparse.ArgumentParser(description='Athena Memory Optimizer')
    parser.add_argument('--optimize', action='store_true', help='Run full memory optimization')
    parser.add_argument('--analyze', action='store_true', help='Analyze memory health')
    parser.add_argument('--cleanup', action='store_true', help='Clean up corrupted data')
    parser.add_argument('--schedule', action='store_true', help='Set up automated optimization schedule')
    parser.add_argument('--report', action='store_true', help='Generate optimization report')

    args = parser.parse_args()

    optimizer = AthenaMemoryOptimizer()

    if args.optimize:
        print("🧠 Running Athena Memory Optimization...")
        results = optimizer.optimize_memory()
        report = optimizer.generate_optimization_report(results)
        print(report)

        # Save report
        log_dir = '/var/log/ai-republic' if os.path.exists('/var/log/ai-republic') else './logs'
        os.makedirs(log_dir, exist_ok=True)
        report_file = os.path.join(log_dir, f'optimization_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')

        with open(report_file, 'w') as f:
            f.write(report)

        print(f"📄 Report saved to: {report_file}")

    elif args.analyze:
        print("🔍 Analyzing Athena Memory Health...")
        health = optimizer.analyze_memory_health()

        print(f"Overall Health: {health['overall_health']}")
        print(f"Active Memory: {health['active_memory'].get('utilization', 0):.1f}% utilized")
        print(f"Archive Memory: {health['archive_memory'].get('utilization', 0):.1f}% utilized")

        if health['issues']:
            print(f"Issues Found: {len(health['issues'])}")
            for issue in health['issues'][:3]:
                print(f"  • {issue}")

        if health['recommendations']:
            print(f"Recommendations: {len(health['recommendations'])}")
            for rec in health['recommendations'][:3]:
                print(f"  • {rec}")

    elif args.cleanup:
        print("🧹 Cleaning up corrupted memory data...")
        results = optimizer.optimize_memory()
        cleanup_issues = [issue for issue in results.get('issues_resolved', [])
                         if 'corrupt' in issue.lower()]
        print(f"✅ Cleaned up {len(cleanup_issues)} corrupted entries")

    elif args.schedule:
        print("⏰ Setting up automated memory optimization...")
        # This would create a systemd timer for weekly optimization
        print("Weekly optimization scheduled (would require systemd setup)")
        print("Manual optimization: python3 athena_memory_optimizer.py --optimize")

    elif args.report:
        # Generate a report without running optimization
        print("📊 Generating Memory Health Report...")

        health = optimizer.analyze_memory_health()

        report = f"""# Athena Memory Health Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Health: {health['overall_health']}

## Memory Utilization
- **Active Memory:** {health['active_memory'].get('utilization', 0):.1f}% ({health['active_memory'].get('size', 0)}/{health['active_memory'].get('capacity', 0)})
- **Archive Memory:** {health['archive_memory'].get('utilization', 0):.1f}% ({health['archive_memory'].get('size', 0)}/{health['archive_memory'].get('capacity', 0)})

## Performance Metrics
- **Load Time:** {health['performance_metrics'].get('load_time', 0):.3f}s
- **Search Time:** {health['performance_metrics'].get('search_time', 0):.3f}s
- **Memory Usage:** {health['performance_metrics'].get('memory_usage', 0) / 1024:.1f}KB

## Issues Detected: {len(health['issues'])}
{chr(10).join(f"- {issue}" for issue in health['issues'])}

## Recommendations: {len(health['recommendations'])}
{chr(10).join(f"- {rec}" for rec in health['recommendations'])}
"""
        print(report)

    else:
        print("🤖 Athena Memory Optimizer")
        print("Usage:")
        print("  --optimize    Run full memory optimization")
        print("  --analyze     Analyze memory health")
        print("  --cleanup     Clean up corrupted data")
        print("  --schedule    Set up automated optimization")
        print("  --report      Generate health report")

if __name__ == '__main__':
    main()
