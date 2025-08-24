# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security issues seriously and appreciate your efforts to responsibly disclose any vulnerabilities you find.

### How to Report

To report a security vulnerability, please email [security@example.com](mailto:security@example.com) with the subject line "[FastSearch MCP] Security Vulnerability".

In your report, please include:

- A detailed description of the vulnerability
- Steps to reproduce the issue
- Any proof-of-concept code or exploit
- Your contact information (optional)

We will acknowledge receipt of your report within 48 hours and provide a more detailed response indicating the next steps in handling your report.

### Our Security Process

1. Your report will be reviewed by our security team
2. If the issue is confirmed, we will work on a fix
3. A security advisory will be released once the fix is available
4. The fix will be included in the next release

### Public Disclosure Policy

We follow responsible disclosure:

- We will work with you to understand and validate the issue
- We will not take legal action against you if you follow these guidelines
- We will keep you informed of the progress towards resolving the issue
- We will credit you in our security advisories (unless you prefer to remain anonymous)

## Security Considerations

### For Users

- Always run the service with the minimum required permissions
- Keep your installation up to date with the latest security patches
- Review and understand the permissions you grant to the application

### For Developers

- Follow secure coding practices
- Keep dependencies up to date
- Use the latest stable versions of all tools and libraries
- Regularly audit your code for security vulnerabilities

## Security Features

- **Privilege Separation**: The service runs with elevated privileges only when necessary
- **Input Validation**: All inputs are strictly validated
- **Secure Communication**: All inter-process communication is authenticated and encrypted
- **Minimal Attack Surface**: The service exposes only the minimum required functionality

## Contact

For any security-related questions or concerns, please contact [security@example.com](mailto:security@example.com).
