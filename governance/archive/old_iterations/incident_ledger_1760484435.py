#!/usr/bin/env python3
"""
Immutable Incident Ledger for Constitutional Governance
======================================================

Implements an immutable, cryptographically-verifiable ledger of governance
incidents, violations, quarantines, amendments, and constitutional events.

Key Features:
- Cryptographic hashing for immutability
- Merkle tree structure for efficient verification
- Comprehensive audit trail of all governance events
- Tamper-evident logging of constitutional changes
- Query and verification APIs for compliance and auditing

Usage:
    from scripts.incident_ledger import get_incident_ledger
    ledger = get_incident_ledger()
    await ledger.record_incident(incident_data)
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid
import os

logger = logging.getLogger(__name__)

class IncidentType(Enum):
    """Types of incidents that can be recorded."""
    GOVERNANCE_VIOLATION = "governance_violation"
    DRIFT_DETECTED = "drift_detected"
    QUARANTINE_INITIATED = "quarantine_initiated"
    QUARANTINE_RELEASED = "quarantine_released"
    CONSTITUTIONAL_ROLLBACK = "constitutional_rollback"
    AMENDMENT_PROPOSED = "amendment_proposed"
    AMENDMENT_APPROVED = "amendment_approved"
    AMENDMENT_IMPLEMENTED = "amendment_implemented"
    AMENDMENT_ROLLED_BACK = "amendment_rolled_back"
    SYSTEM_HEALTH_CHECK = "system_health_check"
    PEER_INTERACTION = "peer_interaction"

class IncidentSeverity(Enum):
    """Severity levels for incidents."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    INFO = "info"

@dataclass
class LedgerEntry:
    """An immutable entry in the incident ledger."""
    entry_id: str
    incident_type: IncidentType
    severity: IncidentSeverity
    timestamp: datetime

    # Incident data
    title: str
    description: str
    details: Dict[str, Any]

    # Cryptographic integrity
    content_hash: str = ""
    previous_hash: str = ""
    merkle_root: str = ""

    # Metadata
    instance_id: str = ""
    sequence_number: int = 0
    block_hash: str = ""

    def __post_init__(self):
        """Generate content hash after initialization."""
        if not self.content_hash:
            content = {
                'entry_id': self.entry_id,
                'incident_type': self.incident_type.value,
                'severity': self.severity.value,
                'timestamp': self.timestamp.isoformat(),
                'title': self.title,
                'description': self.description,
                'details': self.details,
                'instance_id': self.instance_id,
                'sequence_number': self.sequence_number
            }
            content_str = json.dumps(content, sort_keys=True)
            self.content_hash = hashlib.sha256(content_str.encode()).hexdigest()

@dataclass
class LedgerBlock:
    """A block containing multiple ledger entries."""
    block_id: str
    timestamp: datetime
    entries: List[LedgerEntry]
    previous_block_hash: str = ""
    block_hash: str = ""
    merkle_root: str = ""
    sequence_number: int = 0

    def __post_init__(self):
        """Generate block hash after initialization."""
        if not self.block_hash:
            # Create Merkle tree root from entries
            entry_hashes = [entry.content_hash for entry in self.entries]
            self.merkle_root = self._build_merkle_root(entry_hashes)

            # Block content for hashing
            block_content = {
                'block_id': self.block_id,
                'timestamp': self.timestamp.isoformat(),
                'previous_block_hash': self.previous_block_hash,
                'merkle_root': self.merkle_root,
                'sequence_number': self.sequence_number,
                'entry_count': len(self.entries)
            }

            content_str = json.dumps(block_content, sort_keys=True)
            self.block_hash = hashlib.sha256(content_str.encode()).hexdigest()

            # Update entries with block hash and merkle root
            for entry in self.entries:
                entry.block_hash = self.block_hash
                entry.merkle_root = self.merkle_root

    def _build_merkle_root(self, hashes: List[str]) -> str:
        """Build Merkle tree root from list of hashes."""
        if not hashes:
            return hashlib.sha256(b'empty').hexdigest()

        if len(hashes) == 1:
            return hashes[0]

        # Build tree level by level
        current_level = hashes
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                next_level.append(combined)
            current_level = next_level

        return current_level[0]

class ImmutableIncidentLedger:
    """Immutable ledger for governance incidents and constitutional events."""

    def __init__(self, instance_id: Optional[str] = None, storage_path: Optional[str] = None):
        self.instance_id = instance_id or str(uuid.uuid4())[:8]
        self.storage_path = storage_path or f"./ledger_{self.instance_id}.json"

        # In-memory ledger state
        self.entries: List[LedgerEntry] = []
        self.blocks: List[LedgerBlock] = []
        self.pending_entries: List[LedgerEntry] = []

        # Chain integrity
        self.current_sequence = 0
        self.genesis_hash = self._generate_genesis_hash()

        # Block configuration
        self.max_entries_per_block = 100
        self.block_interval_seconds = 300  # 5 minutes

        # Load existing ledger if available
        self._load_ledger()

        logger.info(f"📋 Immutable Incident Ledger initialized for instance {self.instance_id}")

    def _generate_genesis_hash(self) -> str:
        """Generate genesis block hash."""
        genesis_content = f"genesis_{self.instance_id}_{datetime.now().date().isoformat()}"
        return hashlib.sha256(genesis_content.encode()).hexdigest()

    async def record_incident(self, incident_data: Dict[str, Any]) -> str:
        """Record a new incident in the ledger."""
        # Validate incident data
        if not self._validate_incident_data(incident_data):
            raise ValueError("Invalid incident data")

        # Create ledger entry
        entry = LedgerEntry(
            entry_id=str(uuid.uuid4())[:12],
            incident_type=IncidentType(incident_data['incident_type']),
            severity=IncidentSeverity(incident_data.get('severity', 'info')),
            timestamp=incident_data.get('timestamp', datetime.now()),
            title=incident_data['title'],
            description=incident_data['description'],
            details=incident_data.get('details', {}),
            instance_id=self.instance_id,
            sequence_number=self.current_sequence
        )

        # Set previous hash
        if self.entries:
            entry.previous_hash = self.entries[-1].content_hash

        # Add to pending entries
        self.pending_entries.append(entry)
        self.entries.append(entry)
        self.current_sequence += 1

        # Check if we should create a new block
        await self._check_block_creation()

        # Persist to storage
        self._save_ledger()

        logger.info(f"📝 Recorded incident: {entry.entry_id} - {entry.title}")
        return entry.entry_id

    def _validate_incident_data(self, data: Dict[str, Any]) -> bool:
        """Validate incident data structure."""
        required_fields = ['incident_type', 'title', 'description']

        for field in required_fields:
            if field not in data:
                return False

        # Validate incident type
        try:
            IncidentType(data['incident_type'])
        except ValueError:
            return False

        # Validate severity if provided
        if 'severity' in data:
            try:
                IncidentSeverity(data['severity'])
            except ValueError:
                return False

        return True

    async def _check_block_creation(self) -> None:
        """Check if a new block should be created."""
        should_create = (
            len(self.pending_entries) >= self.max_entries_per_block or
            (self.pending_entries and
             datetime.now() - self.pending_entries[0].timestamp > timedelta(seconds=self.block_interval_seconds))
        )

        if should_create:
            await self._create_block()

    async def _create_block(self) -> None:
        """Create a new block from pending entries."""
        if not self.pending_entries:
            return

        # Create block
        block = LedgerBlock(
            block_id=str(uuid.uuid4())[:12],
            timestamp=datetime.now(),
            entries=self.pending_entries.copy(),
            previous_block_hash=self.blocks[-1].block_hash if self.blocks else self.genesis_hash,
            sequence_number=len(self.blocks)
        )

        # Add block to chain
        self.blocks.append(block)
        self.pending_entries.clear()

        logger.info(f"🧱 Created block {block.block_id} with {len(block.entries)} entries")

    def verify_chain_integrity(self) -> Tuple[bool, List[str]]:
        """Verify the integrity of the entire ledger chain."""
        issues = []

        # Verify block chain
        previous_hash = self.genesis_hash
        for block in self.blocks:
            # Check block hash chain
            if block.previous_block_hash != previous_hash:
                issues.append(f"Block {block.block_id}: Invalid previous hash chain")

            # Verify block hash
            expected_hash = block.block_hash
            recalculated = LedgerBlock(
                block_id=block.block_id,
                timestamp=block.timestamp,
                entries=block.entries,
                previous_block_hash=block.previous_block_hash,
                sequence_number=block.sequence_number
            ).block_hash

            if expected_hash != recalculated:
                issues.append(f"Block {block.block_id}: Block hash mismatch")

            # Verify Merkle root
            entry_hashes = [entry.content_hash for entry in block.entries]
            expected_merkle = block._build_merkle_root(entry_hashes)

            if block.merkle_root != expected_merkle:
                issues.append(f"Block {block.block_id}: Merkle root mismatch")

            previous_hash = block.block_hash

        # Verify entry chain
        for i, entry in enumerate(self.entries):
            # Check sequence
            if entry.sequence_number != i:
                issues.append(f"Entry {entry.entry_id}: Invalid sequence number")

            # Check previous hash
            if i > 0 and entry.previous_hash != self.entries[i-1].content_hash:
                issues.append(f"Entry {entry.entry_id}: Invalid previous hash")

            # Verify content hash
            expected_content_hash = LedgerEntry(
                entry_id=entry.entry_id,
                incident_type=entry.incident_type,
                severity=entry.severity,
                timestamp=entry.timestamp,
                title=entry.title,
                description=entry.description,
                details=entry.details,
                instance_id=entry.instance_id,
                sequence_number=entry.sequence_number
            ).content_hash

            if entry.content_hash != expected_content_hash:
                issues.append(f"Entry {entry.entry_id}: Content hash mismatch")

        return len(issues) == 0, issues

    def get_incident_history(self, incident_type: Optional[IncidentType] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Get incident history with optional filtering."""
        filtered_entries = self.entries

        # Apply filters
        if incident_type:
            filtered_entries = [e for e in filtered_entries if e.incident_type == incident_type]

        if start_date:
            filtered_entries = [e for e in filtered_entries if e.timestamp >= start_date]

        if end_date:
            filtered_entries = [e for e in filtered_entries if e.timestamp <= end_date]

        # Sort by timestamp (newest first)
        filtered_entries.sort(key=lambda e: e.timestamp, reverse=True)

        # Convert to dict format
        result = []
        for entry in filtered_entries[:limit]:
            result.append({
                'entry_id': entry.entry_id,
                'incident_type': entry.incident_type.value,
                'severity': entry.severity.value,
                'timestamp': entry.timestamp.isoformat(),
                'title': entry.title,
                'description': entry.description,
                'details': entry.details,
                'content_hash': entry.content_hash,
                'block_hash': entry.block_hash,
                'sequence_number': entry.sequence_number
            })

        return result

    def get_chain_statistics(self) -> Dict[str, Any]:
        """Get comprehensive ledger statistics."""
        total_entries = len(self.entries)
        total_blocks = len(self.blocks)

        # Entry type breakdown
        entry_types = {}
        for entry in self.entries:
            etype = entry.incident_type.value
            entry_types[etype] = entry_types.get(etype, 0) + 1

        # Severity breakdown
        severities = {}
        for entry in self.entries:
            sev = entry.severity.value
            severities[sev] = severities.get(sev, 0) + 1

        # Time range
        if self.entries:
            oldest_entry = min(e.timestamp for e in self.entries)
            newest_entry = max(e.timestamp for e in self.entries)
        else:
            oldest_entry = newest_entry = None

        # Chain integrity
        is_valid, integrity_issues = self.verify_chain_integrity()

        return {
            "instance_id": self.instance_id,
            "total_entries": total_entries,
            "total_blocks": total_blocks,
            "pending_entries": len(self.pending_entries),
            "current_sequence": self.current_sequence,
            "chain_integrity": {
                "is_valid": is_valid,
                "issues_count": len(integrity_issues),
                "issues": integrity_issues[:5]  # First 5 issues
            },
            "entry_types": entry_types,
            "severities": severities,
            "time_range": {
                "oldest": oldest_entry.isoformat() if oldest_entry else None,
                "newest": newest_entry.isoformat() if newest_entry else None
            },
            "storage_path": self.storage_path
        }

    def export_chain_for_audit(self, start_sequence: Optional[int] = None,
                             end_sequence: Optional[int] = None) -> Dict[str, Any]:
        """Export chain data for external audit."""
        start_seq = start_sequence or 0
        end_seq = end_sequence or self.current_sequence

        # Get entries in range
        export_entries = [
            e for e in self.entries
            if start_seq <= e.sequence_number < end_seq
        ]

        # Get blocks containing these entries
        relevant_blocks = []
        for block in self.blocks:
            if any(e.entry_id in [ex.entry_id for ex in export_entries] for e in block.entries):
                relevant_blocks.append({
                    'block_id': block.block_id,
                    'timestamp': block.timestamp.isoformat(),
                    'sequence_number': block.sequence_number,
                    'previous_block_hash': block.previous_block_hash,
                    'block_hash': block.block_hash,
                    'merkle_root': block.merkle_root,
                    'entry_count': len(block.entries),
                    'entry_hashes': [e.content_hash for e in block.entries]
                })

        return {
            "export_timestamp": datetime.now().isoformat(),
            "instance_id": self.instance_id,
            "sequence_range": {"start": start_seq, "end": end_seq},
            "genesis_hash": self.genesis_hash,
            "blocks": relevant_blocks,
            "entries": [
                {
                    'entry_id': e.entry_id,
                    'sequence_number': e.sequence_number,
                    'content_hash': e.content_hash,
                    'previous_hash': e.previous_hash,
                    'block_hash': e.block_hash,
                    'incident_data': {
                        'type': e.incident_type.value,
                        'severity': e.severity.value,
                        'timestamp': e.timestamp.isoformat(),
                        'title': e.title,
                        'description': e.description,
                        'details': e.details
                    }
                }
                for e in export_entries
            ]
        }

    def _save_ledger(self) -> None:
        """Save ledger to persistent storage."""
        try:
            data = {
                "instance_id": self.instance_id,
                "genesis_hash": self.genesis_hash,
                "current_sequence": self.current_sequence,
                "blocks": [
                    {
                        "block_id": b.block_id,
                        "timestamp": b.timestamp.isoformat(),
                        "previous_block_hash": b.previous_block_hash,
                        "block_hash": b.block_hash,
                        "merkle_root": b.merkle_root,
                        "sequence_number": b.sequence_number,
                        "entries": [
                            {
                                "entry_id": e.entry_id,
                                "incident_type": e.incident_type.value,
                                "severity": e.severity.value,
                                "timestamp": e.timestamp.isoformat(),
                                "title": e.title,
                                "description": e.description,
                                "details": e.details,
                                "content_hash": e.content_hash,
                                "previous_hash": e.previous_hash,
                                "sequence_number": e.sequence_number
                            }
                            for e in b.entries
                        ]
                    }
                    for b in self.blocks
                ]
            }

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save ledger: {e}")

    def _load_ledger(self) -> None:
        """Load ledger from persistent storage."""
        if not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)

            self.instance_id = data.get("instance_id", self.instance_id)
            self.genesis_hash = data.get("genesis_hash", self.genesis_hash)
            self.current_sequence = data.get("current_sequence", 0)

            # Reconstruct blocks and entries
            for block_data in data.get("blocks", []):
                entries = []
                for entry_data in block_data.get("entries", []):
                    entry = LedgerEntry(
                        entry_id=entry_data["entry_id"],
                        incident_type=IncidentType(entry_data["incident_type"]),
                        severity=IncidentSeverity(entry_data["severity"]),
                        timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                        title=entry_data["title"],
                        description=entry_data["description"],
                        details=entry_data["details"],
                        content_hash=entry_data["content_hash"],
                        previous_hash=entry_data["previous_hash"],
                        instance_id=self.instance_id,
                        sequence_number=entry_data["sequence_number"]
                    )
                    entries.append(entry)
                    self.entries.append(entry)

                block = LedgerBlock(
                    block_id=block_data["block_id"],
                    timestamp=datetime.fromisoformat(block_data["timestamp"]),
                    entries=entries,
                    previous_block_hash=block_data["previous_block_hash"],
                    sequence_number=block_data["sequence_number"]
                )
                # Override block hash with stored value
                block.block_hash = block_data["block_hash"]
                self.blocks.append(block)

            logger.info(f"📖 Loaded ledger with {len(self.entries)} entries in {len(self.blocks)} blocks")

        except Exception as e:
            logger.error(f"Failed to load ledger: {e}")

# Global instance
_incident_ledger = None

def get_incident_ledger(instance_id: Optional[str] = None) -> ImmutableIncidentLedger:
    """Get the global incident ledger instance."""
    global _incident_ledger
    if _incident_ledger is None:
        _incident_ledger = ImmutableIncidentLedger(instance_id)
    return _incident_ledger

# Test function
async def test_incident_ledger():
    """Test the incident ledger functionality."""
    print("📋 Testing Immutable Incident Ledger")
    print("=" * 50)

    # Create ledger
    ledger = get_incident_ledger("test_instance_001")

    # Record test incidents
    test_incidents = [
        {
            'incident_type': 'governance_violation',
            'severity': 'high',
            'title': 'Ethical Boundary Violation',
            'description': 'Strategy violated ethical bias constraints',
            'details': {
                'strategy_id': 'strat_123',
                'violation_type': 'bias_amplification',
                'severity_score': 0.8,
                'affected_users': 1500
            }
        },
        {
            'incident_type': 'drift_detected',
            'severity': 'medium',
            'title': 'Policy Delta Drift Detected',
            'description': 'Constitutional weights shifted from baseline',
            'details': {
                'drift_type': 'policy_delta',
                'baseline_value': 0.85,
                'current_value': 0.72,
                'delta_percentage': -15.3,
                'affected_policies': ['ethical_compliance', 'user_satisfaction']
            }
        },
        {
            'incident_type': 'quarantine_initiated',
            'severity': 'high',
            'title': 'Strategy Quarantine Activated',
            'description': 'High-violation strategy quarantined for review',
            'details': {
                'strategy_id': 'strat_456',
                'quarantine_duration_hours': 48,
                'violation_count': 12,
                'auto_release_enabled': True
            }
        },
        {
            'incident_type': 'amendment_proposed',
            'severity': 'info',
            'title': 'Constitutional Amendment Proposed',
            'description': 'Optimization engine proposed bias detection improvements',
            'details': {
                'amendment_id': 'amend_789',
                'category': 'ethical_boundary',
                'proposed_by': 'optimization_engine',
                'changes': {'bias_threshold': 0.12}
            }
        },
        {
            'incident_type': 'system_health_check',
            'severity': 'info',
            'title': 'Daily Health Check Completed',
            'description': 'All systems operating within normal parameters',
            'details': {
                'governance_score': 0.91,
                'violation_rate': 0.023,
                'peer_connections': 5,
                'active_strategies': 1247
            }
        }
    ]

    entry_ids = []
    for incident in test_incidents:
        try:
            entry_id = await ledger.record_incident(incident)
            entry_ids.append(entry_id)
            print(f"📝 Recorded incident: {entry_id}")
        except Exception as e:
            print(f"❌ Failed to record incident: {e}")

    # Force block creation
    await ledger._create_block()

    # Verify chain integrity
    is_valid, issues = ledger.verify_chain_integrity()
    print(f"\n🔍 Chain integrity: {'✅ VALID' if is_valid else '❌ INVALID'}")
    if issues:
        print(f"   Issues found: {len(issues)}")
        for issue in issues[:3]:
            print(f"   • {issue}")

    # Get incident history
    violations = ledger.get_incident_history(IncidentType.GOVERNANCE_VIOLATION)
    print(f"\n📊 Found {len(violations)} governance violations")

    amendments = ledger.get_incident_history(IncidentType.AMENDMENT_PROPOSED)
    print(f"📜 Found {len(amendments)} amendment proposals")

    # Show statistics
    stats = ledger.get_chain_statistics()
    print("\n📈 Ledger Statistics:")
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Total blocks: {stats['total_blocks']}")
    print(f"   Entry types: {stats['entry_types']}")
    print(f"   Severities: {stats['severities']}")

    # Export audit data
    audit_export = ledger.export_chain_for_audit(0, 3)
    print(f"\n📤 Exported audit data for first 3 entries: {len(audit_export['entries'])} entries")

    print("\n🎉 Incident ledger test completed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_incident_ledger())
