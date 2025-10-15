#!/bin/bash
# Example environment setup for Twilio iPhone alerts
# Copy this and fill in your actual credentials

# Create .env file in project directory (you can move it to /opt/ai-republic later)
cat > .env << 'INNER_EOF'
TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_FROM_NUMBER="+15555555555"     # your Twilio number
ATHENA_ALERT_PHONE="+1YOURIPHONE"     # your iPhone number
INNER_EOF

echo "✅ .env file created with placeholder credentials"
echo "Edit .env with your actual Twilio credentials before testing"
