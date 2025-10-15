#!/usr/bin/env python3
"""
ATHENA MEMORY MAINTENANCE SYSTEM
Automated weekly optimization and cleanup of persistent memory

Performs scheduled maintenance tasks:
- Memory optimization and defragmentation
- Old conversation cleanup (90+ days)
- Pattern optimization and deduplication
- Performance monitoring and reporting
- Automatic backup before maintenance
"""

import time
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging

from athena_memory_system import AthenaMemorySystem
from athena_alert_system import AthenaAlertSystem

class AthenaMemoryMaintenance:
    """Automated maintenance system for Athena's persistent memory"""

    def __init__(self, memory_dir: str = None):
        # Use demo path for testing/development, production path for deployment
        if memory_dir is None:
            memory_dir = "/tmp/athena_memory_demo"  # Use demo path for testing

        self.memory_dir = Path(memory_dir)
        self.backup_dir = self.memory_dir / "backups"
        self.log_file = self.memory_dir / "maintenance.log"

        # Setup logging (create directory if needed)
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(
                filename=str(self.log_file),
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
        except Exception:
            # Fallback to console logging if file logging fails
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
        self.logger = logging.getLogger('athena_memory_maintenance')

        # Initialize alert system
        self.alert_system = AthenaAlertSystem()

        # Maintenance settings
        self.retention_days = 90
        self.backup_retention_days = 30
        self.max_patterns_per_intent = 50
        self.optimization_threshold = 1000  # Optimize when patterns exceed this

        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def run_full_maintenance(self) -> dict:
        """Run complete memory maintenance cycle"""
        self.logger.info("Starting full memory maintenance cycle")

        start_time = time.time()
        results = {
            'timestamp': datetime.now().isoformat(),
            'backup_created': False,
            'conversations_cleaned': 0,
            'patterns_optimized': 0,
            'memory_compacted': False,
            'errors': [],
            'duration_seconds': 0
        }

        try:
            # 1. Create backup before maintenance
            results['backup_created'] = self._create_backup()

            # 2. Clean old conversations
            results['conversations_cleaned'] = self._cleanup_old_conversations()

            # 3. Optimize memory patterns
            results['patterns_optimized'] = self._optimize_memory_patterns()

            # 4. Compact and defragment memory
            results['memory_compacted'] = self._compact_memory()

            # 5. Clean old backups
            self._cleanup_old_backups()

            # 6. Generate maintenance report
            self._generate_maintenance_report(results)

            results['duration_seconds'] = time.time() - start_time
            self.logger.info(f"Maintenance completed successfully in {results['duration_seconds']:.2f} seconds")

            # Send success alert
            self.alert_system.send_alert(
                'maintenance_success',
                'Automated memory maintenance completed successfully',
                details={
                    'duration_seconds': results['duration_seconds'],
                    'conversations_cleaned': results['conversations_cleaned'],
                    'patterns_optimized': results['patterns_optimized'],
                    'backup_created': results['backup_created']
                },
                severity='info'
            )

        except Exception as e:
            error_msg = f"Maintenance failed: {e}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)

            # Send critical alert for maintenance failure
            self.alert_system.send_alert(
                'maintenance_failure',
                'Automated memory maintenance cycle failed',
                details={
                    'error': str(e),
                    'partial_results': results,
                    'maintenance_type': 'full_cycle'
                },
                severity='critical'
            )

        return results

    def _create_backup(self) -> bool:
        """Create backup of current memory state"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"memory_backup_{timestamp}.json.gz"

            # Use the memory system's export function
            memory_system = AthenaMemorySystem(str(self.memory_dir))
            success = memory_system.export_memory_data(str(backup_file))

            if success:
                self.logger.info(f"Memory backup created: {backup_file}")
                return True
            else:
                self.logger.error("Failed to create memory backup")
                # Send warning alert for backup failure
                self.alert_system.send_alert(
                    'backup_failure',
                    'Memory backup creation failed during maintenance',
                    details={'backup_file': str(backup_file)},
                    severity='warning'
                )
                return False

        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            # Send critical alert for backup system failure
            self.alert_system.send_alert(
                'backup_system_failure',
                'Memory backup system encountered critical error',
                details={'error': str(e), 'backup_location': str(backup_file.parent)},
                severity='critical'
            )
            return False

    def _cleanup_old_conversations(self) -> int:
        """Clean up conversations older than retention period"""
        conversations_dir = self.memory_dir / "conversations"
        if not conversations_dir.exists():
            return 0

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        cleaned_count = 0

        # Iterate through date directories
        for date_dir in conversations_dir.iterdir():
            if not date_dir.is_dir():
                continue

            try:
                # Parse directory name as date
                dir_date = datetime.strptime(date_dir.name, "%Y%m%d")

                if dir_date < cutoff_date:
                    # Remove old directory
                    shutil.rmtree(date_dir)
                    cleaned_count += 1
                    self.logger.info(f"Cleaned old conversation directory: {date_dir.name}")

            except ValueError:
                # Skip invalid date directories
                continue

        self.logger.info(f"Cleaned {cleaned_count} old conversation directories")
        return cleaned_count

    def _optimize_memory_patterns(self) -> int:
        """Optimize and deduplicate memory patterns"""
        memory_system = AthenaMemorySystem(str(self.memory_dir))

        optimized_count = 0

        # Optimize command frequencies
        for intent, patterns in memory_system.long_term_memory.get('command_frequencies', {}).items():
            if len(patterns) > self.max_patterns_per_intent:
                # Keep only most frequent patterns
                sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
                memory_system.long_term_memory['command_frequencies'][intent] = dict(
                    sorted_patterns[:self.max_patterns_per_intent]
                )
                optimized_count += len(patterns) - self.max_patterns_per_intent

        # Optimize successful commands
        for intent, patterns in memory_system.long_term_memory.get('successful_commands', {}).items():
            if len(patterns) > self.max_patterns_per_intent:
                sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
                memory_system.long_term_memory['successful_commands'][intent] = dict(
                    sorted_patterns[:self.max_patterns_per_intent]
                )
                optimized_count += len(patterns) - self.max_patterns_per_intent

        # Optimize failed commands
        for intent, patterns in memory_system.long_term_memory.get('failed_commands', {}).items():
            if len(patterns) > self.max_patterns_per_intent:
                # Keep recent failures for learning (sort by recency)
                sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
                memory_system.long_term_memory['failed_commands'][intent] = dict(
                    sorted_patterns[:self.max_patterns_per_intent // 2]  # Keep fewer failures
                )
                optimized_count += len(patterns) - (self.max_patterns_per_intent // 2)

        # Clean up user command patterns (remove very old or infrequent ones)
        user_patterns = memory_system.long_term_memory.get('user_command_patterns', {})
        cleaned_patterns = {}

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        for pattern_hash, pattern_data in user_patterns.items():
            last_used = datetime.fromisoformat(pattern_data.get('last_used', '2000-01-01T00:00:00'))
            frequency = pattern_data.get('frequency', 0)

            # Keep if recently used OR frequently used
            if last_used > cutoff_date or frequency > 5:
                cleaned_patterns[pattern_hash] = pattern_data
            else:
                optimized_count += 1

        memory_system.long_term_memory['user_command_patterns'] = cleaned_patterns

        # Save optimized memory
        memory_system._save_long_term_memory()

        self.logger.info(f"Optimized {optimized_count} memory patterns")
        return optimized_count

    def _compact_memory(self) -> bool:
        """Compact and defragment memory files"""
        try:
            memory_system = AthenaMemorySystem(str(self.memory_dir))

            # Recompress long-term memory with maximum compression
            memory_system._save_long_term_memory()

            # Compact user preferences
            memory_system._save_user_preferences()

            # Compact session memory
            memory_system._save_session_memory()

            self.logger.info("Memory files compacted successfully")
            return True

        except Exception as e:
            self.logger.error(f"Memory compaction failed: {e}")
            # Send warning alert for compaction failure
            self.alert_system.send_alert(
                'memory_compaction_failure',
                'Memory compaction failed during maintenance',
                details={'error': str(e)},
                severity='warning'
            )
            return False

    def _cleanup_old_backups(self):
        """Clean up backups older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)

        cleaned_count = 0
        for backup_file in self.backup_dir.glob("memory_backup_*.json.gz"):
            try:
                # Extract timestamp from filename
                timestamp_str = backup_file.stem.split('_')[2]  # memory_backup_YYYYMMDD_HHMMSS
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                if file_date < cutoff_date:
                    backup_file.unlink()
                    cleaned_count += 1
                    self.logger.info(f"Cleaned old backup: {backup_file.name}")

            except (ValueError, IndexError):
                continue

        self.logger.info(f"Cleaned {cleaned_count} old backup files")

    def _generate_maintenance_report(self, results: dict):
        """Generate maintenance report"""
        report_file = self.memory_dir / f"maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Get current memory stats
        memory_system = AthenaMemorySystem(str(self.memory_dir))
        current_stats = memory_system.get_memory_stats()

        report = {
            'maintenance_results': results,
            'memory_stats_after': current_stats,
            'recommendations': self._generate_recommendations(results, current_stats)
        }

        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.logger.info(f"Maintenance report generated: {report_file}")
        except Exception as e:
            self.logger.error(f"Failed to generate maintenance report: {e}")

    def _generate_recommendations(self, results: dict, stats: dict) -> list:
        """Generate maintenance recommendations based on results"""
        recommendations = []

        if not results.get('backup_created'):
            recommendations.append("Consider manual backup - automatic backup failed")

        conversations_cleaned = results.get('conversations_cleaned', 0)
        if conversations_cleaned > 10:
            recommendations.append(f"High cleanup activity ({conversations_cleaned} directories) - consider adjusting retention policy")

        patterns_optimized = results.get('patterns_optimized', 0)
        if patterns_optimized > 100:
            recommendations.append(f"Significant pattern optimization ({patterns_optimized} patterns) - memory was heavily fragmented")

        # Check memory size
        memory_size = stats.get('long_term_memory_size', 0)
        if memory_size > 50 * 1024 * 1024:  # 50MB
            recommendations.append(f"Large memory footprint ({memory_size/1024/1024:.1f}MB) - consider more aggressive optimization")

        # Check conversation archive count
        archive_count = stats.get('conversation_archives', 0)
        if archive_count > 100:
            recommendations.append(f"Many conversation archives ({archive_count}) - consider shorter retention period")

        return recommendations if recommendations else ["Memory maintenance completed successfully - no action needed"]

    def get_maintenance_status(self) -> dict:
        """Get current maintenance status and schedule"""
        last_report = None
        report_files = sorted(self.memory_dir.glob("maintenance_report_*.json"))

        if report_files:
            try:
                with open(report_files[-1], 'r') as f:
                    last_report = json.load(f)
            except Exception:
                pass

        return {
            'last_maintenance': last_report['maintenance_results']['timestamp'] if last_report else None,
            'next_scheduled': (datetime.now() + timedelta(days=7)).isoformat(),
            'backup_count': len(list(self.backup_dir.glob("memory_backup_*.json.gz"))),
            'log_size': self.log_file.stat().st_size if self.log_file.exists() else 0,
            'last_report': last_report
        }

def main():
    """Main entry point for memory maintenance"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena Memory Maintenance System')
    parser.add_argument('action', choices=['run', 'status', 'backup', 'cleanup', 'report'],
                       help='Maintenance action to perform')
    parser.add_argument('--memory-dir', default=None,
                       help='Memory directory path (default: auto-detect)')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode - less output')

    args = parser.parse_args()

    maintenance = AthenaMemoryMaintenance(args.memory_dir)

    if args.action == 'run':
        if not args.quiet:
            print("🧹 Starting Athena memory maintenance...")

        results = maintenance.run_full_maintenance()

        if not args.quiet:
            print("✅ Maintenance completed!")
            print(f"   Duration: {results['duration_seconds']:.1f} seconds")
            print(f"   Backups created: {results['backup_created']}")
            print(f"   Conversations cleaned: {results['conversations_cleaned']}")
            print(f"   Patterns optimized: {results['patterns_optimized']}")
            print(f"   Memory compacted: {results['memory_compacted']}")

            if results['errors']:
                print("⚠️  Errors encountered:")
                for error in results['errors']:
                    print(f"   • {error}")

    elif args.action == 'status':
        status = maintenance.get_maintenance_status()
        print("🧠 Athena Memory Maintenance Status")
        print("=" * 40)
        print(f"Last maintenance: {status['last_maintenance'] or 'Never'}")
        print(f"Next scheduled: {status['next_scheduled'][:10]}")
        print(f"Backup files: {status['backup_count']}")
        print(f"Log file size: {status['log_size']/1024:.1f} KB")

    elif args.action == 'backup':
        success = maintenance._create_backup()
        if success:
            print("✅ Memory backup created successfully")
        else:
            print("❌ Memory backup failed")

    elif args.action == 'cleanup':
        cleaned = maintenance._cleanup_old_conversations()
        print(f"🧹 Cleaned {cleaned} old conversation directories")

    elif args.action == 'report':
        status = maintenance.get_maintenance_status()
        if status['last_report']:
            print(json.dumps(status['last_report'], indent=2, default=str))
        else:
            print("No maintenance reports found")

if __name__ == '__main__':
    main()
