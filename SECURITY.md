# Security Policy

## Supported Versions

Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Best Practices

### API Key Security

This MCP server requires a Pocketsmith API key with **full account access**. Treat your API key like a password:

- ✅ Store API keys in environment variables (never in code)
- ✅ Use different API keys for development and production
- ✅ Rotate API keys periodically
- ✅ Revoke API keys immediately if compromised
- ❌ Never commit API keys to version control
- ❌ Never share API keys publicly
- ❌ Never log API keys

### Permissions

This MCP server has full access to your Pocketsmith account and can:

- ✅ Read all transactions, accounts, and budgets
- ✅ Create, update, and delete transactions
- ✅ Create and modify categories
- ✅ Create category rules
- ✅ View account balances and sensitive financial data

**Only use this server with trusted AI assistants** (like Claude Desktop) on secure machines.

### Data Privacy

- This server does **not** store any of your financial data
- All data is retrieved directly from Pocketsmith's API
- No data is sent to third parties
- All communication with Pocketsmith uses HTTPS

### Network Security

- Only use this server on trusted networks
- The server communicates directly with Pocketsmith's API
- Consider using a VPN when accessing financial data on public networks

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

### How to Report

1. **DO NOT** open a public GitHub issue
2. Use GitHub's [Security Advisory](https://github.com/dannyshaw/pocketsmith-mcp/security/advisories/new) feature
3. Or email: daniel.m.shaw@gmail.com

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

### Response Timeline

- **Initial response:** Within 48 hours
- **Status update:** Within 7 days
- **Fix timeline:** Varies by severity (critical issues prioritized)

### Disclosure Policy

- We will acknowledge your report within 48 hours
- We will provide regular updates on our progress
- We will credit you in the fix (unless you prefer to remain anonymous)
- We ask that you do not publicly disclose the vulnerability until we've released a fix

## Security Updates

Security updates will be released as soon as possible and announced via:

- GitHub Security Advisories
- Release notes

## Audit History

- **2026-02-17**: Initial security assessment completed
  - No vulnerabilities found
  - Approved for public release

## Third-Party Dependencies

We regularly monitor our dependencies for known vulnerabilities:

- `mcp` - Official Model Context Protocol SDK
- `httpx` - Well-maintained HTTP client
- `pydantic` - Type-safe data validation
- `pydantic-settings` - Secure configuration management

Run `pip-audit` or `safety check` to verify dependency security.

## Contact

For security concerns: daniel.m.shaw@gmail.com

For general questions: Use GitHub Issues (do not include sensitive information)
