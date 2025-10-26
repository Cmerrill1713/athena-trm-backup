#!/bin/bash
# Generate self-signed TLS certificates for Athena services
# For local family use - valid for 10 years

set -e

echo "🔐 Generating TLS certificates for Athena..."

# Generate private key
openssl genrsa -out server.key 4096

# Generate certificate signing request
openssl req -new -key server.key -out server.csr -subj "/C=US/ST=State/L=City/O=Athena/CN=localhost"

# Generate self-signed certificate (valid for 10 years)
openssl x509 -req -days 3650 -in server.csr -signkey server.key -out server.crt

# Create combined PEM file (some services need this)
cat server.crt server.key > server.pem

# Set appropriate permissions
chmod 600 server.key server.pem
chmod 644 server.crt

echo "✅ Certificates generated:"
echo "   - server.key (private key)"
echo "   - server.crt (certificate)"
echo "   - server.pem (combined)"
echo ""
echo "Valid for: 10 years"
echo "Common Name: localhost"
echo ""
echo "🔒 These are self-signed certificates for local use only."
echo "   Browsers will show a warning - this is normal for self-signed certs."
