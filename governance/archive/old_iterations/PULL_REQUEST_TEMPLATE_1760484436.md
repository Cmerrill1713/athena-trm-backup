# Pull Request

## Description
<!-- Brief description of what this PR does -->

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Related Issues
<!-- Link to related issues, e.g., Fixes #123 -->

## Testing
<!-- Describe the tests you ran to verify your changes -->

### Pre-Merge Checklist
- [ ] All tests pass locally (`make test-all`)
- [ ] Acceptance tests pass (`make smoke`)
- [ ] Contract tests pass (`pytest tests/test_contract.py`)
- [ ] Integration tests pass (`pytest tests/test_integration.py`)
- [ ] No linter errors
- [ ] Documentation updated (if needed)
- [ ] SHIPLOG.md updated (if user-facing change)

### Bridge/Real Mode Specific (if applicable)
- [ ] Tested in mock mode (`USE_MOCK=1`)
- [ ] Tested in real mode (`USE_MOCK=0`)
- [ ] Observability headers working (`X-Mode`, `X-Breaker`)
- [ ] Circuit breaker logic verified
- [ ] Auth working (401 on bad token)
- [ ] No secrets in logs

### Performance (if applicable)
- [ ] p95 latency < 250ms
- [ ] No memory leaks
- [ ] Rate limiting respected

## Rollback Plan
<!-- If this PR is risky, describe how to rollback -->

## Screenshots (if applicable)
<!-- Add screenshots if UI changes -->

## Deployment Notes
<!-- Any special deployment instructions -->

---

**Reviewer**: Please verify:
1. Code quality and style
2. Test coverage is adequate
3. No performance regressions
4. Documentation is clear
5. No security issues introduced
