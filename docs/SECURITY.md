# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.5.x   | :white_check_mark: |
| < 0.5.0 | :x:                |

## Reporting a Vulnerability

We take the security of `api-mocker` seriously. If you find a vulnerability, please do NOT open an issue. Instead, please follow these steps:

1.  **Do not disclose publicly:** Please refrain from discussing the vulnerability in public issues, pull requests, or social media.
2.  **Email us:** Send the details of the vulnerability to `security@example.com` (replace with actual contact if available).
3.  **Provide details:** Include a description of the vulnerability, steps to reproduce, and any proof-of-concept code.

We will acknowledge your report within 48 hours and provide an estimated timeline for a fix.

## Security Best Practices for Users

### Authentication
*   **Always change default secrets:** Never run `api-mocker` in production with the default `API_MOCKER_SECRET_KEY`. Set this environment variable to a strong, random string.
*   **Use strong passwords:** The system now enforces password complexity, but ensure users choose strong passwords.
*   **Enable MFA:** Multi-Factor Authentication is supported and recommended for all administrative accounts.

### Database
*   **Use production databases:** For production usage, configure a PostgreSQL or MongoDB instance instead of the default SQLite.
*   **Least Privilege:** Ensure the database user used by `api-mocker` has only the necessary permissions.

### Network
*   **Reverse Proxy:** Always deploy `api-mocker` behind a reverse proxy (like Nginx or Traefik) that handles SSL termination (`https`).
*   **Firewall:** Restrict access to the API port (default 8000) to trusted sources.

## Known Vulnerabilities
*   **Pre-0.5.0:** Versions prior to 0.5.0 stored passwords in plain text and had potential SQL injection vulnerabilities. **Upgrade immediately.**
