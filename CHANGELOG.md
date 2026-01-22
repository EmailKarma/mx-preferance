# Changelog

All notable changes to this project will be documented in this file.

This project follows a lightweight semantic versioning approach:
- Major versions introduce breaking changes.
- Minor versions add functionality in a backward-compatible way.
- Patch versions fix bugs or improve performance without changing behaviour.

---

## [0.1.0] – 2026-01-22

### Initial release

First public release of the MX Provider Classifier.

### Added
- Support for input files containing email addresses, domains, or mixed content.
- Automatic extraction and de-duplication of domains from input files.
- MX record lookups using the system resolver or a user-specified nameserver.
- Classification based on **highest-priority MX records only**.
- Pattern-driven provider identification via an editable CSV file.
- Separation of consumer and business platforms:
  - Gmail vs Google Workspace
  - Outlook vs Microsoft 365
- Identification of common mailbox providers and gateways, including:
  - Google, Microsoft, Yahoo, iCloud, Proton Mail
  - Mimecast, Proofpoint (Enterprise and Essentials)
  - GoDaddy / SecureServer
- Explicit handling of DNS failure cases:
  - No MX records
  - NXDOMAIN
  - Timeout
  - No nameservers
- Automatic classification of unmatched MX records as **Custom MX**.
- Parallel DNS lookups with configurable worker count.
- Three CSV outputs:
  - Provider counts
  - Domain-to-provider mapping
  - DNS errors and edge cases

### Configuration
- Provider classification logic externalized to `provider_patterns.csv`.
- Support for `suffix`, `contains`, `exact`, and `regex` matching.
- Pattern priority ordering to avoid provider overlap.

### Output
- Deterministic, date-stamped output filenames.
- Transparent reporting of MX preference and evaluated MX hosts.

### Known limitations
- Does not validate mailbox existence.
- Does not detect provider migrations or mixed-provider configurations.
- Does not enrich results with ASN, WHOIS, or IP data.

---