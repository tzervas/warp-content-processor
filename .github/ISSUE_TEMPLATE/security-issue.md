---
name: Security Issue
about: Report a security vulnerability
title: "[SECURITY] "
labels: security
assignees: ""
---

⚠️ **IMPORTANT: Do not include sensitive information such as credentials, tokens, or specific exploit details in this public issue.** ⚠️

# Security Issue Template

## Type

- Type: dropdown
- Required: true
- Options:
  - Path Traversal
  - Cross-Site Scripting (XSS)
  - SQL Injection
  - Authentication Bypass
  - Authorization Bypass
  - Remote Code Execution
  - Information Disclosure
  - Denial of Service
  - Other (please specify)

## Severity

- Type: dropdown
- Required: true
- Options:
  - Critical
  - High
  - Medium
  - Low
  - Informational

## Description

- Type: text (markdown)
- Required: true
- Description: Provide a clear and concise description of the security vulnerability.

## Affected Versions

- Type: text (markdown)
- Required: true
- Description: List the affected versions, components, and relevant dependencies

## Reproduction Steps

- Type: text (markdown)
- Required: true
- Description: Detail the steps to reproduce the vulnerability (avoid including actual exploit code or credentials)
- Format:
  1. Step 1
  2. Step 2
  3. ...

## Impact

- Type: text (markdown)
- Required: true
- Description: Describe the potential impact if exploited
- Suggested sections:
  - Technical Impact
  - Business Impact
  - Affected Users/Systems

## Mitigation

- Type: text (markdown)
- Required: true
- Description: Proposed fix or mitigation steps
- Suggested sections:
  - Immediate Actions
  - Long-term Fixes
  - Alternative Solutions

## Security Contact

- Type: text (markdown)
- Required: false
- Description: For sensitive security issues that should not be disclosed publicly, please contact:
  - Email: [Security Team Email]
  - or refer to our security policy at [SECURITY.md]

## Confidentiality Note

- Type: text
- Required: true
- Default: "This security issue should be treated as confidential and only shared with necessary stakeholders until resolved."
- Description: Special handling instructions or confidentiality requirements
