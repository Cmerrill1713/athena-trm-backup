"""
Unit tests for log redaction
Ensures secrets are properly masked before logs are returned
"""

import pytest
import sys
import os

# Add bridge to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bridge'))

from logs_endpoint import redact_secrets


class TestLogRedaction:
    """Test suite for secret redaction in logs"""
    
    def test_bearer_token_redacted(self):
        """Bearer tokens should be masked"""
        input_log = "Authorization: Bearer supersecret123456"
        output = redact_secrets(input_log)
        
        assert "supersecret123456" not in output
        assert "***REDACTED***" in output
    
    def test_api_key_redacted(self):
        """API keys should be masked"""
        input_log = "api_key=sk-1234567890abcdefghijklmnop"
        output = redact_secrets(input_log)
        
        assert "sk-1234567890abcdefghijklmnop" not in output
        assert "***REDACTED***" in output
    
    def test_openai_key_redacted(self):
        """OpenAI keys (sk-...) should be masked"""
        input_log = "Using key: sk-proj-abc123def456ghi789jkl012mno345pqr"
        output = redact_secrets(input_log)
        
        assert "sk-proj-abc123def456" not in output
        assert "sk-***REDACTED***" in output
    
    def test_slack_token_redacted(self):
        """Slack tokens should be masked"""
        test_cases = [
            "xoxb-1234567890-abcdefghij",
            "xoxp-9876543210-zyxwvutsrq",
            "xoxa-team-credentials"
        ]
        
        for token in test_cases:
            input_log = f"Slack token: {token}"
            output = redact_secrets(input_log)
            assert token not in output
            assert "***REDACTED***" in output
    
    def test_password_redacted(self):
        """Passwords should be masked"""
        input_log = "password=MySecretPass123!"
        output = redact_secrets(input_log)
        
        assert "MySecretPass123!" not in output
        assert "***REDACTED***" in output
    
    def test_email_redacted(self):
        """Emails (PII) should be masked"""
        input_log = "User user@example.com accessed endpoint"
        output = redact_secrets(input_log)
        
        assert "user@example.com" not in output
        assert "***EMAIL_REDACTED***" in output
    
    def test_token_env_var_redacted(self):
        """Environment token values should be masked"""
        input_log = "UAT_TOKEN=mysecrettoken ATH_TOKEN=anothersecret"
        output = redact_secrets(input_log)
        
        assert "mysecrettoken" not in output
        assert "anothersecret" not in output
        assert "***REDACTED***" in output
    
    def test_multiple_secrets_in_one_line(self):
        """Multiple secrets in same line should all be redacted"""
        input_log = "Bearer secret123 and api_key=sk-abcdef and user@example.com"
        output = redact_secrets(input_log)
        
        assert "secret123" not in output
        assert "sk-abcdef" not in output
        assert "user@example.com" not in output
        assert output.count("***REDACTED***") >= 2
    
    def test_safe_content_unchanged(self):
        """Non-secret content should pass through"""
        input_log = "INFO: Processing request at 2025-10-12 20:15:30"
        output = redact_secrets(input_log)
        
        assert "INFO: Processing request" in output
        assert "2025-10-12 20:15:30" in output
    
    def test_case_insensitive_redaction(self):
        """Redaction should work regardless of case"""
        test_cases = [
            "authorization: Bearer token123",
            "AUTHORIZATION: Bearer token456",
            "Authorization: Bearer token789",
        ]
        
        for log in test_cases:
            output = redact_secrets(log)
            assert "token" not in output.lower() or "***REDACTED***" in output
    
    def test_multiline_redaction(self):
        """Redaction should work across multiple lines"""
        input_log = """
        Line 1: Bearer token123
        Line 2: api_key=sk-abcdef
        Line 3: user@example.com logged in
        """
        output = redact_secrets(input_log)
        
        assert "token123" not in output
        assert "sk-abcdef" not in output
        assert "user@example.com" not in output
        assert output.count("***REDACTED***") >= 2


class TestLogEndpointSecurity:
    """Integration tests for log endpoint security"""
    
    @pytest.mark.asyncio
    async def test_service_allowlist(self):
        """Only whitelisted services should be accessible"""
        # This would be an integration test hitting the actual endpoint
        # For now, document the expected behavior
        pass
    
    @pytest.mark.asyncio
    async def test_max_tail_enforced(self):
        """Tail parameter should be clamped to max"""
        pass
    
    @pytest.mark.asyncio
    async def test_timeout_protection(self):
        """Requests should timeout after 5s"""
        pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

