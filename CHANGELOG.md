# Changelog

All notable changes to this project will be documented in this file.

---

## v0.1.3 - 2026-04-15

### Added
- Detection of IP literals (IPv4 and IPv6)
- Support for bracketed IPv6 inputs (`[2001:db8::1]`)
- Internal domain detection, including:
  - `.local`
  - `.localdomain`
  - `.internal`
  - `.lan`
  - `.home`
  - `.home.arpa`
  - `.corp`
  - `.intranet`

### Improved
- Domain extraction logic for mixed input formats
- Input validation to reduce unnecessary DNS lookups
- Classification accuracy for non-routable and invalid inputs

### Fixed
- Prevented IP literals from being processed as valid domains
- Reduced misclassification of invalid inputs as `Custom MX`

### Known Issues
- MX targets such as `localhost` may still be classified as `Custom MX`
- Invalid MX hostnames (e.g., `~`) are not explicitly handled
- Provider classification depends on pattern coverage

---

## v0.1.2

### Added
- MX lookup and provider classification logic
- CSV output with date-based naming
- Pattern-based provider detection

### Features
- Batch processing of domains and email addresses
- DNS-based MX resolution
- Fallback classification as `Custom MX`

---

## [0.1.1] - 2026-02-20

---

## What’s New in v0.1.1

Version: **v0.1.1**

A command-line tool to:

- Extract domains from email addresses or domain lists
- Perform MX lookups
- Classify providers based on pattern matching
- Identify bad domains
- Generate structured reporting outputs

---

### Enhanced Counts Output

The counts file now includes two metrics:

| Field | Description |
|--------|-------------|
| `domain_count` | Number of unique domains mapped to a provider |
| `record_count` | Total number of input records mapped to a provider |

This allows you to see:

- Provider dominance by unique domain footprint
- Provider dominance by dataset volume
- Duplicate email impact
- Noise from bad domains

Example:

```

provider,domain_count,record_count
Outlook,4,1500
Microsoft 365,7,500
Mimecast,5,230
Proofpoint,18,200
Custom MX,120,320
Bad Domain - NXDOMAIN,12,12

```

### Added
- Added `record_count` metric to Counts output.
- Counts file now reports:
  - `domain_count` (unique domains per provider)
  - `record_count` (total input records per provider, including duplicates)
- Duplicate input records are now preserved for reporting accuracy.

### Changed
- MX lookups are still performed once per unique domain to avoid redundant DNS queries.
- Counts output now includes all buckets:
  - Mailbox providers
  - Security gateways
  - Institutional platforms
  - Custom MX
  - Bad Domain categories
- Improved internal aggregation logic for clearer reporting.

### Technical Notes
- Input processing now separates:
  - `raw_domains` (preserves duplicates)
  - `domains` (unique list for MX lookups)
- Updated `write_counts()` to support dual-metric output.
- Suppressed `unclassified` file output while retaining fallback bucket logic.

---

## [0.1] - Initial Release

### Features
- MX lookup with highest-priority record selection.
- Provider classification using pattern matching (`provider_patterns.csv`).
- Support for:
  - Mailbox providers (Google, Microsoft, Yahoo, etc.)
  - Security gateways (Proofpoint, Mimecast, etc.)
  - Institutional platforms (DFN, NHS Mail, etc.)
  - Custom MX detection
  - DNS error classification
- Output files:
  - Provider counts
  - Domain-to-provider mapping
  - Unclassified domains
- Customizable DNS resolver support via command-line options.
