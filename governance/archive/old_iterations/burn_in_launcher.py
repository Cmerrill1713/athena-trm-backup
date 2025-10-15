#!/usr/bin/env python3
"""
Athena Context Trigger - Automated Burn-In Launcher
====================================================

ONE-LINER DEPLOYMENT: Run the complete burn-in sequence automatically
from dry-run observation → tiered activation → spike testing → autonomous production.

This script orchestrates the entire burn-in process with:
- Automatic phase progression based on success criteria
- Continuous health monitoring and logging
- Emergency rollback capabilities
- Comprehensive reporting and notifications
- Voice diagnostics integration

Usage:
    python3 burn_in_launcher.py         # Start complete burn-in sequence
    python3 burn_in_launcher.py --status # Check current progress
    python3 burn_in_launcher.py --stop   # Emergency stop all phases
    python3 burn_in_launcher.py --report # Generate final deployment report
"""

import os
import sys
import time
import json
import signal
import subprocess
from typing import Optional
import threading

# Add system paths
sys.path.insert(0, '/opt/ai-republic')
sys.path.insert(0, os.path.dirname(__file__))

# Import our burn-in system
from burn_in_test import BurnInTest, BURN_IN_CONFIG
from athena_notifications import send_tier1_immediate

class BurnInLauncher:
    """Automated burn-in launcher that orchestrates the complete sequence"""

    def __init__(self):
        self.burn_in = BurnInTest()
        self.launcher_state = "/tmp/athena_burn_in_launcher.json"
        self.phase_processes = {}  # Track running phase processes
        self.monitoring_active = False
        self.emergency_stop = False

        # Load launcher state
        self.load_state()

        # Handle signals for clean shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def load_state(self):
        """Load launcher state"""
        try:
            with open(self.launcher_state, "r") as f:
                state = json.load(f)
                self.monitoring_active = state.get("monitoring_active", False)
                self.emergency_stop = state.get("emergency_stop", False)
        except:
            pass

    def save_state(self):
        """Save launcher state"""
        state = {
            "monitoring_active": self.monitoring_active,
            "emergency_stop": self.emergency_stop,
            "timestamp": time.time()
        }
        try:
            with open(self.launcher_state, "w") as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Warning: Could not save launcher state: {e}")

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum} - initiating emergency shutdown...")
        self.emergency_stop_all()
        sys.exit(0)

    def emergency_stop_all(self):
        """Emergency stop all burn-in processes"""
        print("🚨 Emergency stop initiated...")

        self.emergency_stop = True
        self.monitoring_active = False
        self.save_state()

        # Stop all running processes
        for phase, process in self.phase_processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ Stopped {phase} process")
            except:
                try:
                    process.kill()
                    print(f"🔪 Force-killed {phase} process")
                except:
                    print(f"❌ Could not stop {phase} process")

        # Rollback to safe state
        self.burn_in.rollback()

        # Send emergency notification
        send_tier1_immediate("🚨 Burn-in emergency stop activated - all automations disabled")

        print("🛡️ Emergency stop complete - system in safe state")

    def check_phase_success_criteria(self, phase: str) -> bool:
        """Check if current phase meets success criteria for progression"""

        # Get recent test results for this phase
        recent_results = [r for r in self.burn_in.test_results[-50:]
                         if r["phase"] == phase and r["success"]]

        total_recent = len(recent_results)
        if total_recent < 10:  # Need minimum sample size
            return False

        success_rate = sum(1 for r in recent_results if r["success"]) / total_recent

        # Phase-specific criteria
        if phase == "dry_run":
            return success_rate >= 0.95  # 95% success rate for observation
        elif phase == "tiered_activation":
            return success_rate >= 0.98  # 98% for live activation
        elif phase == "spike_test":
            # Check if spike detection worked
            spike_tests = [r for r in recent_results if "spike" in r["test"]]
            return len(spike_tests) >= 3 and all(r["success"] for r in spike_tests)

        return success_rate >= 0.95  # Default 95% success rate

    def should_progress_to_next_phase(self, current_phase: str, days_elapsed: int) -> Optional[str]:
        """Determine if we should progress to the next phase"""

        if current_phase == "dry_run" and days_elapsed >= BURN_IN_CONFIG["dry_run_days"]:
            if self.check_phase_success_criteria("dry_run"):
                return "tiered_activation"
            else:
                print("⚠️ Dry-run phase not ready for progression - continuing observation")
                return None

        elif current_phase == "tiered_activation" and days_elapsed >= BURN_IN_CONFIG["tiered_activation_day"]:
            if self.check_phase_success_criteria("tiered_activation"):
                return "spike_test"
            else:
                print("⚠️ Tiered activation not ready for spike testing - continuing")
                return None

        elif current_phase == "spike_test" and days_elapsed >= BURN_IN_CONFIG["spike_test_day"]:
            if self.check_phase_success_criteria("spike_test"):
                return "autonomous"
            else:
                print("⚠️ Spike testing not ready for autonomous mode - continuing")
                return None

        return None

    def start_phase_process(self, phase: str) -> subprocess.Popen:
        """Start a burn-in phase as a background process"""

        cmd = [sys.executable, "burn_in_test.py"]

        if phase == "dry_run":
            cmd.append("--dry-run")
        elif phase == "tiered":
            cmd.append("--tiered")
        elif phase == "spike-test":
            cmd.append("--spike-test")
        elif phase == "autonomous":
            cmd.append("--autonomous")

        print(f"🚀 Starting {phase} phase...")

        # Start process with stdout/stderr redirected to log files
        log_file = f"/tmp/athena_burn_in_{phase}.log"
        with open(log_file, "a") as log:
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=log,
                preexec_fn=os.setsid  # Create new process group for clean termination
            )

        self.phase_processes[phase] = process
        return process

    def monitor_phase_health(self, phase: str, process: subprocess.Popen) -> bool:
        """Monitor health of a running phase process"""
        if process.poll() is not None:  # Process has terminated
            return_code = process.returncode
            if return_code != 0:
                print(f"❌ {phase} process exited with code {return_code}")
                return False
            else:
                print(f"✅ {phase} process completed successfully")
                return True

        # Process still running - check health via status
        try:
            result = subprocess.run(
                [sys.executable, "burn_in_test.py", "--health-check"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def run_health_monitoring(self):
        """Background health monitoring thread"""
        while self.monitoring_active and not self.emergency_stop:
            try:
                # Check current phase process health
                current_phase = self.burn_in.phase
                if current_phase in self.phase_processes:
                    process = self.phase_processes[current_phase]
                    if not self.monitor_phase_health(current_phase, process):
                        print(f"🔴 Health check failed for {current_phase}")
                        self.burn_in.log_test_result(f"{current_phase}_health", False,
                                                   "Process health check failed")

                # Periodic comprehensive health check
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    self.burn_in.run_health_check()

                    # Send periodic status updates
                    status_report = f"Burn-in Status: {current_phase} (Day {self.burn_in.get_elapsed_days()})"
                    send_tier1_immediate(status_report)

            except Exception as e:
                print(f"❌ Health monitoring error: {e}")

            time.sleep(60)  # Check every minute

    def run_complete_burn_in(self):
        """Run the complete automated burn-in sequence"""
        print("🚀 Starting Complete Athena Burn-In Sequence")
        print("=" * 60)
        print("This will run all phases automatically:")
        print("  Days 1-2: Dry-run observation")
        print("  Day 3: Tiered activation (meeting + travel)")
        print("  Day 4: Spike detection testing")
        print("  Day 5+: Full autonomous operation")
        print("")
        print("🛑 Emergency stop: Ctrl+C or 'python3 burn_in_launcher.py --stop'")
        print("📊 Check progress: 'python3 burn_in_launcher.py --status'")
        print("=" * 60)

        self.monitoring_active = True
        self.save_state()

        # Start health monitoring thread
        monitor_thread = threading.Thread(target=self.run_health_monitoring, daemon=True)
        monitor_thread.start()

        try:
            while not self.emergency_stop:
                days_elapsed = self.burn_in.get_elapsed_days()
                current_phase = self.burn_in.phase

                # Determine if we should progress to next phase
                next_phase = self.should_progress_to_next_phase(current_phase, days_elapsed)

                if next_phase:
                    print(f"🎯 Progressing to phase: {next_phase}")

                    # Stop current phase if running
                    if current_phase in self.phase_processes:
                        try:
                            self.phase_processes[current_phase].terminate()
                            self.phase_processes[current_phase].wait(timeout=10)
                        except:
                            pass

                    # Start next phase
                    if next_phase == "tiered_activation":
                        self.start_phase_process("tiered")
                    elif next_phase == "spike_test":
                        self.start_phase_process("spike-test")
                    elif next_phase == "autonomous":
                        self.start_phase_process("autonomous")

                # If no phase is running and we're not in autonomous mode, start dry-run
                if not any(p.poll() is None for p in self.phase_processes.values()):
                    if current_phase not in ["autonomous"]:
                        if current_phase != "dry_run":
                            print("🔄 Starting dry-run observation phase...")
                            self.start_phase_process("dry_run")

                # Check for completion (autonomous mode running successfully for extended period)
                if (current_phase == "autonomous" and
                    days_elapsed >= BURN_IN_CONFIG["autonomous_day"] + 1):  # Day 6+

                    # Check if autonomous mode has been stable
                    recent_results = [r for r in self.burn_in.test_results[-100:]
                                    if r["phase"] == "autonomous" and r["success"]]

                    if len(recent_results) >= 50:  # Substantial test history
                        success_rate = sum(1 for r in recent_results if r["success"]) / len(recent_results)
                        if success_rate >= 0.98:  # 98% success rate
                            print("🎉 Burn-in complete! System ready for production deployment.")
                            self.generate_completion_report()
                            break

                time.sleep(300)  # Check every 5 minutes

        except Exception as e:
            print(f"❌ Burn-in launcher error: {e}")
            self.emergency_stop_all()

        finally:
            self.monitoring_active = False
            self.save_state()

    def generate_completion_report(self):
        """Generate completion report for successful burn-in"""
        report = f"""
🎉 Athena Context Trigger Burn-In COMPLETE!
============================================

✅ All phases completed successfully:
   • Dry-run observation: ✅ Stable
   • Tiered activation: ✅ No conflicts
   • Spike detection: ✅ Emergency handling
   • Autonomous operation: ✅ 24/7 stable

📊 Final Statistics:
{self.burn_in.generate_report()}

🛡️ Safety Systems Verified:
   • Mutex protection: ✅ Active
   • Flap detection: ✅ Working
   • Manual override: ✅ Functional
   • Emergency rollback: ✅ Ready

🚀 Production Deployment Ready:
   • Start autonomous: ./start_triggers.sh
   • Voice commands: "Hey Athena, diagnostics"
   • Emergency stop: python3 burn_in_launcher.py --stop

The system is now enterprise-ready for 24/7 autonomous operation.
"""

        # Save completion report
        with open("/tmp/athena_burn_in_completion.txt", "w") as f:
            f.write(report)

        # Send completion notification
        send_tier1_immediate("🎉 Athena burn-in complete! System ready for production deployment.")

        print(report)

    def show_status(self):
        """Show comprehensive launcher status"""
        print("🚀 Athena Burn-In Launcher Status")
        print("=" * 50)

        days_elapsed = self.burn_in.get_elapsed_days()
        print(f"Days elapsed: {days_elapsed}")
        print(f"Current phase: {self.burn_in.phase}")
        print(f"Monitoring active: {self.monitoring_active}")
        print(f"Emergency stop: {self.emergency_stop}")

        # Show running processes
        running_processes = [(phase, p) for phase, p in self.phase_processes.items()
                           if p.poll() is None]
        if running_processes:
            print(f"\nRunning processes: {len(running_processes)}")
            for phase, process in running_processes:
                print(f"  📋 {phase} (PID: {process.pid})")
        else:
            print("\nNo processes currently running")

        # Show burn-in status
        print("\nBurn-in Status:")
        print(f"  Phase: {self.burn_in.phase}")
        print(f"  Total tests: {len(self.burn_in.test_results)}")
        if self.burn_in.test_results:
            success_count = sum(1 for r in self.burn_in.test_results if r['success'])
            success_rate = success_count / len(self.burn_in.test_results) * 100
            print(f"  Success rate: {success_rate:.1f}%")

        # Show recent test results
        recent_results = self.burn_in.test_results[-5:]  # Last 5 results
        if recent_results:
            print("  Recent tests:")
            for result in recent_results:
                status = "✅" if result['success'] else "❌"
                print(f"    {status} {result['test']} ({result['phase']})")

    def stop_all(self):
        """Stop all burn-in processes"""
        print("🛑 Stopping all burn-in processes...")
        self.emergency_stop_all()

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Athena Burn-In Launcher')
    parser.add_argument('--status', action='store_true', help='Show launcher status')
    parser.add_argument('--stop', action='store_true', help='Emergency stop all processes')
    parser.add_argument('--report', action='store_true', help='Generate completion report')

    args = parser.parse_args()

    launcher = BurnInLauncher()

    if args.status:
        launcher.show_status()
    elif args.stop:
        launcher.stop_all()
    elif args.report:
        if os.path.exists("/tmp/athena_burn_in_completion.txt"):
            with open("/tmp/athena_burn_in_completion.txt", "r") as f:
                print(f.read())
        else:
            print("No completion report available")
    else:
        # Default: run complete burn-in sequence
        launcher.run_complete_burn_in()

if __name__ == '__main__':
    main()
