#!/usr/bin/env python3
"""
Action Ledger Verification Tool

Verifies the action ledger for:
- Duplicate entries (idempotence violations)
- Hash consistency
- Temporal ordering
- Action validity
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime

LEDGER_PATH = Path("artifacts/ledger/actions.log")


def load_ledger() -> List[Dict[str, Any]]:
    """Load ledger entries"""
    if not LEDGER_PATH.exists():
        print(f"❌ Ledger not found: {LEDGER_PATH}")
        return []
    
    entries = []
    with LEDGER_PATH.open("r") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                entry = json.loads(line)
                entry["_line_no"] = line_no
                entries.append(entry)
            except json.JSONDecodeError as e:
                print(f"⚠️  Line {line_no}: Invalid JSON - {e}")
    
    return entries


def verify_hashes(entries: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Verify hash integrity"""
    valid = 0
    invalid = 0
    
    for entry in entries:
        if "hash" not in entry:
            print(f"⚠️  Entry missing hash: task_id={entry.get('task_id', 'unknown')}")
            invalid += 1
            continue
        
        # Recalculate hash
        entry_copy = entry.copy()
        stored_hash = entry_copy.pop("hash")
        entry_copy.pop("_line_no", None)
        
        calculated_hash = hashlib.sha256(
            json.dumps(entry_copy, sort_keys=True).encode()
        ).hexdigest()
        
        if stored_hash == calculated_hash:
            valid += 1
        else:
            print(f"❌ Hash mismatch: task_id={entry.get('task_id')}")
            invalid += 1
    
    return valid, invalid


def check_duplicates(entries: List[Dict[str, Any]]) -> Tuple[int, List[Dict[str, Any]]]:
    """Check for duplicate task_id + action combinations"""
    seen = defaultdict(list)
    
    for entry in entries:
        task_id = entry.get("task_id", "unknown")
        actions = tuple(sorted(entry.get("actions_taken", [])))
        key = (task_id, actions)
        seen[key].append(entry)
    
    duplicates = [(k, v) for k, v in seen.items() if len(v) > 1]
    
    return len(duplicates), duplicates


def check_temporal_order(entries: List[Dict[str, Any]]) -> bool:
    """Verify entries are in temporal order"""
    prev_ts = 0
    out_of_order = []
    
    for entry in entries:
        ts = entry.get("ts", 0)
        if ts < prev_ts:
            out_of_order.append(entry)
        prev_ts = ts
    
    if out_of_order:
        print(f"⚠️  {len(out_of_order)} entries out of temporal order")
        return False
    
    return True


def validate_actions(entries: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Validate actions are from known set"""
    valid_actions = {
        "ROLLBACK", "PROMOTE", "HOLD", "QUARANTINE",
        "AUTOHEAL_ATTEMPT", "RETRY_OR_HUMAN", "FREEZE_PROMOTIONS"
    }
    
    valid = 0
    invalid = 0
    
    for entry in entries:
        actions = entry.get("actions_taken", [])
        for action in actions:
            if action in valid_actions:
                valid += 1
            else:
                print(f"⚠️  Unknown action: {action} in task {entry.get('task_id')}")
                invalid += 1
    
    return valid, invalid


def main():
    """Run verification"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify action ledger integrity")
    parser.add_argument("--verify", action="store_true", help="Run all verification checks")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    parser.add_argument("--ledger", type=Path, default=LEDGER_PATH, help="Ledger file path")
    
    args = parser.parse_args()
    
    global LEDGER_PATH
    LEDGER_PATH = args.ledger
    
    print("=" * 80)
    print("Action Ledger Verification")
    print("=" * 80)
    print(f"Ledger: {LEDGER_PATH}")
    print()
    
    # Load ledger
    entries = load_ledger()
    
    if not entries:
        print("❌ No entries in ledger or ledger not found")
        return 1
    
    print(f"✓ Loaded {len(entries)} entries")
    print()
    
    # Statistics
    if args.stats or args.verify:
        print("Statistics")
        print("-" * 80)
        
        verdicts = defaultdict(int)
        actions = defaultdict(int)
        
        for entry in entries:
            verdict = entry.get("verdict", "unknown")
            verdicts[verdict] += 1
            
            for action in entry.get("actions_taken", []):
                actions[action] += 1
        
        print(f"Total entries: {len(entries)}")
        print(f"Date range: {datetime.fromtimestamp(entries[0].get('ts', 0)).isoformat()} → {datetime.fromtimestamp(entries[-1].get('ts', 0)).isoformat()}")
        print()
        print("Verdicts:")
        for verdict, count in sorted(verdicts.items()):
            print(f"  {verdict}: {count}")
        print()
        print("Actions:")
        for action, count in sorted(actions.items()):
            print(f"  {action}: {count}")
        print()
    
    # Verification
    if args.verify:
        print("Verification Checks")
        print("-" * 80)
        
        # Hash integrity
        valid_hashes, invalid_hashes = verify_hashes(entries)
        if invalid_hashes == 0:
            print(f"✓ Hash integrity: {valid_hashes}/{len(entries)} valid")
        else:
            print(f"❌ Hash integrity: {invalid_hashes} invalid hashes")
        
        # Duplicates
        dup_count, duplicates = check_duplicates(entries)
        if dup_count == 0:
            print(f"✓ Idempotence: 0 duplicates found")
        else:
            print(f"❌ Idempotence: {dup_count} duplicate(s) found")
            for (task_id, actions), entries_list in duplicates[:5]:
                print(f"  Task {task_id}: {len(entries_list)} entries")
        
        # Temporal order
        if check_temporal_order(entries):
            print(f"✓ Temporal order: entries are ordered by timestamp")
        else:
            print(f"❌ Temporal order: some entries out of sequence")
        
        # Action validity
        valid_actions, invalid_actions = validate_actions(entries)
        if invalid_actions == 0:
            print(f"✓ Action validity: all {valid_actions} actions are known")
        else:
            print(f"❌ Action validity: {invalid_actions} unknown actions")
        
        print()
        
        # Overall result
        if invalid_hashes == 0 and dup_count == 0 and invalid_actions == 0:
            print("✅ LEDGER VERIFICATION PASSED")
            return 0
        else:
            print("❌ LEDGER VERIFICATION FAILED")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

