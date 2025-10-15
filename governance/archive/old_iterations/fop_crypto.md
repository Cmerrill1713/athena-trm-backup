# 🔐 FOP CRYPTOGRAPHIC ARCHITECTURE

## Federation Onboarding Protocol Cryptographic Standards

**Zero-Trust Federation Security for Sovereign AI Jurisdictions**

---

## IDENTITY MANAGEMENT

### Decentralized Identifiers (DID)
**Format**: `did:airep:<sha256(pubkey)>`
- **Method**: `airep` (AI Republic)
- **Identifier**: SHA-256 hash of Ed25519 public key
- **Resolution**: Self-resolving, no external registry required

**Example**:
```
did:airep:a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890
```

**Benefits**:
- **Sovereignty**: Jurisdiction controls its own identity
- **Portability**: Identity works across federation instances
- **Privacy**: No correlation between real-world entities and DIDs

### Key Generation
```python
import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519

# Generate keypair
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Derive DID
pubkey_bytes = public_key.public_bytes_raw()
did = f"did:airep:{hashlib.sha256(pubkey_bytes).hexdigest()}"
```

---

## TRANSPORT SECURITY

### Mutual TLS (mTLS)
**Purpose**: Authenticate both client and server in federation communications

**Certificate Requirements**:
- **Subject**: DID as certificate subject
- **Public Key**: Ed25519 public key in certificate
- **Issuer**: Federation Certificate Authority (CA)
- **Validity**: 90 days maximum, automatic rotation
- **Extensions**: Client authentication, server authentication

**mTLS Handshake**:
```
Client ──── ClientHello + Client Cert ────> Server
Server ──── ServerHello + Server Cert + Cert Request ────> Client
Client ──── Client Cert Verify ────> Server
Server ──── Server Cert Verify ────> Client
[Encrypted Application Data Exchange]
```

**Implementation**:
```python
import ssl

# Client context
client_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
client_context.load_cert_chain(certfile='client.pem', keyfile='client.key')
client_context.load_verify_locations(cafile='federation-ca.pem')
client_context.check_hostname = False
client_context.verify_mode = ssl.CERT_REQUIRED
```

---

## MESSAGE SIGNING

### JSON Web Signature (JWS)
**Algorithm**: EdDSA (Ed25519)
**Format**: Detached payload (payload not included in JWS)
**Header**:
```json
{
  "alg": "EdDSA",
  "kid": "did:airep:a1b2c3d4...#key-1"
}
```

### Signing Process
```python
import jwcrypto.jws as jws
import jwcrypto.jwk as jwk

# Create JWK from Ed25519 key
key = jwk.JWK.from_pyca(private_key)
key.key_id = f"{did}#key-1"

# Sign payload
payload = json.dumps(canonical_payload, sort_keys=True, separators=(',', ':'))
token = jws.JWS(payload.encode('utf-8'))
token.add_signature(key, protected={"alg": "EdDSA", "kid": key.key_id})
jws_signature = token.serialize(compact=True)
```

### Verification Process
```python
# Verify signature
token = jws.JWS()
token.deserialize(jws_signature)
token.verify(key)

# Extract payload
verified_payload = json.loads(token.payload.decode('utf-8'))
```

---

## EVIDENCE INTEGRITY

### SHA-256 Content Hashing
**Purpose**: Verify evidence payload integrity

```python
def content_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
```

### Merkle Tree Construction
**Purpose**: Batch integrity and proof generation

```python
class MerkleTree:
    def __init__(self, items: List[bytes]):
        self.items = items
        self.tree = self.build_tree(items)

    def build_tree(self, items: List[bytes]) -> List[List[bytes]]:
        tree = [items]
        while len(tree[-1]) > 1:
            level = []
            for i in range(0, len(tree[-1]), 2):
                left = tree[-1][i]
                right = tree[-1][i + 1] if i + 1 < len(tree[-1]) else left
                level.append(hashlib.sha256(left + right).digest())
            tree.append(level)
        return tree

    def get_root(self) -> str:
        return self.tree[-1][0].hex()

    def get_proof(self, index: int) -> List[Tuple[bytes, bool]]:
        """Generate Merkle proof for item at index"""
        proof = []
        for level in self.tree[:-1]:
            if index % 2 == 0:
                # Left sibling
                if index + 1 < len(level):
                    proof.append((level[index + 1], False))  # Right neighbor
            else:
                # Right sibling
                proof.append((level[index - 1], True))   # Left neighbor
            index //= 2
        return proof
```

### Batch Evidence Processing
```python
def create_evidence_batch(evidence_items: List[dict]) -> dict:
    # Create content hashes
    hashes = [bytes.fromhex(item['hash']) for item in evidence_items]

    # Build Merkle tree
    merkle = MerkleTree(hashes)
    merkle_root = merkle.get_root()

    # Create batch
    batch = {
        'items': evidence_items,
        'merkle_root': merkle_root,
        'timestamp': time.time(),
        'batch_size': len(evidence_items)
    }

    return batch
```

---

## PRIVACY PRESERVATION

### ε-Differential Privacy
**Purpose**: Add statistical noise to prevent individual identification

```python
import numpy as np

class DifferentialPrivacy:
    def __init__(self, epsilon: float):
        self.epsilon = epsilon

    def add_noise(self, value: float, sensitivity: float = 1.0) -> float:
        """Add Laplace noise for differential privacy"""
        scale = sensitivity / self.epsilon
        noise = np.random.laplace(0, scale)
        return value + noise

    def privatize_count(self, true_count: int) -> int:
        """Privatize a count statistic"""
        noisy_count = self.add_noise(true_count, sensitivity=1.0)
        return max(0, round(noisy_count))

    def privatize_percentage(self, true_percentage: float) -> float:
        """Privatize a percentage (0-100)"""
        noisy_percentage = self.add_noise(true_percentage, sensitivity=1.0)
        return max(0.0, min(100.0, noisy_percentage))
```

### K-Anonymity Bucketing
**Purpose**: Group similar incidents to prevent individual identification

```python
from collections import defaultdict

class KAnonymityBucket:
    def __init__(self, k: int = 5):
        self.k = k
        self.buckets = defaultdict(list)

    def add_incident(self, incident: dict, category_key: str = 'category'):
        """Add incident to appropriate anonymity bucket"""
        category = incident.get(category_key, 'unknown')
        bucket_key = self._get_bucket_key(incident, category)
        self.buckets[bucket_key].append(incident)

    def _get_bucket_key(self, incident: dict, category: str) -> str:
        """Generate bucket key for k-anonymity"""
        # Group by category and time window (e.g., hourly)
        timestamp = incident.get('timestamp', 0)
        hour_bucket = timestamp // 3600  # Hourly buckets
        return f"{category}_{hour_bucket}"

    def get_anonymized_buckets(self) -> List[dict]:
        """Return only buckets with sufficient anonymity"""
        anonymized = []
        for bucket_key, incidents in self.buckets.items():
            if len(incidents) >= self.k:
                # Create anonymized summary
                anonymized.append({
                    'bucket_key': bucket_key,
                    'count': len(incidents),
                    'category': bucket_key.split('_')[0],
                    'time_bucket': bucket_key.split('_')[1],
                    'anonymity_level': len(incidents)
                })
        return anonymized
```

---

## KEY MANAGEMENT

### Key Rotation Protocol
**Maximum Lifetime**: 90 days
**Rotation Triggers**:
- Scheduled rotation (90 days)
- Compromise detection
- Tribunal-ordered rotation
- Jurisdiction exit/re-entry

### Emergency Key Rotation
```python
def emergency_rotate_keys(old_private_key, reason: str):
    """Emergency key rotation with federation notification"""

    # Generate new keypair
    new_private_key = ed25519.Ed25519PrivateKey.generate()
    new_public_key = new_private_key.public_key()

    # Create rotation attestation
    rotation_attestation = {
        'old_did': f"did:airep:{hashlib.sha256(old_private_key.public_key().public_bytes_raw()).hexdigest()}",
        'new_did': f"did:airep:{hashlib.sha256(new_public_key.public_bytes_raw()).hexdigest()}",
        'rotation_timestamp': time.time(),
        'reason': reason,
        'emergency': True
    }

    # Sign with old key
    old_key_jwk = jwk.JWK.from_pyca(old_private_key)
    token = jws.JWS(json.dumps(rotation_attestation, sort_keys=True).encode())
    token.add_signature(old_key_jwk, protected={"alg": "EdDSA"})
    rotation_jws = token.serialize(compact=True)

    # Broadcast rotation to federation
    notify_federation_rotation(rotation_attestation, rotation_jws)

    return new_private_key, rotation_attestation
```

### Key Compromise Response
1. **Detection**: Automated monitoring or manual report
2. **Isolation**: Immediate quarantine of affected jurisdiction
3. **Rotation**: Emergency key rotation across all systems
4. **Notification**: Federation-wide alert with compromise details
5. **Recovery**: Independent audit before reinstatement

---

## AUDIT TRAILS

### Cryptographic Audit Chain
**Purpose**: Immutable, verifiable record of all federation operations

```python
class AuditChain:
    def __init__(self):
        self.chain = []
        self.current_hash = None

    def add_entry(self, entry: dict) -> str:
        """Add entry to audit chain"""
        entry_with_prev = {
            **entry,
            'previous_hash': self.current_hash,
            'sequence_number': len(self.chain)
        }

        # Create entry hash
        entry_hash = hashlib.sha256(
            json.dumps(entry_with_prev, sort_keys=True).encode()
        ).hexdigest()

        entry_with_prev['entry_hash'] = entry_hash
        self.chain.append(entry_with_prev)
        self.current_hash = entry_hash

        return entry_hash

    def verify_chain(self) -> bool:
        """Verify integrity of entire audit chain"""
        expected_hash = None
        for i, entry in enumerate(self.chain):
            # Verify sequence
            if entry.get('sequence_number') != i:
                return False

            # Verify previous hash
            if entry.get('previous_hash') != expected_hash:
                return False

            # Verify entry hash
            entry_copy = {k: v for k, v in entry.items() if k != 'entry_hash'}
            calculated_hash = hashlib.sha256(
                json.dumps(entry_copy, sort_keys=True).encode()
            ).hexdigest()

            if calculated_hash != entry.get('entry_hash'):
                return False

            expected_hash = entry.get('entry_hash')

        return True
```

---

## IMPLEMENTATION SECURITY CHECKLIST

### Pre-Deployment Verification
- [ ] Ed25519 key generation and signing operational
- [ ] mTLS certificate generation and validation working
- [ ] JWS detached payload signing/verification functional
- [ ] SHA-256 hashing and Merkle tree construction tested
- [ ] Differential privacy noise addition calibrated
- [ ] K-anonymity bucketing algorithm validated
- [ ] Audit chain immutability verified

### Runtime Security Monitoring
- [ ] Key rotation automation active
- [ ] Certificate expiration monitoring enabled
- [ ] Compromise detection alerts configured
- [ ] Audit chain integrity continuously verified
- [ ] Privacy budget consumption tracked
- [ ] Rate limiting and abuse detection active

### Incident Response Procedures
- [ ] Key compromise response plan documented
- [ ] Certificate revocation procedures established
- [ ] Federation-wide alert mechanisms tested
- [ ] Recovery and reinstatement processes validated
- [ ] Post-incident forensic analysis capabilities ready

---

This cryptographic architecture provides the zero-trust foundation for secure, sovereignty-preserving federation among AI jurisdictions. All protocols prioritize cryptographic accountability while maintaining operational efficiency and privacy protection.
