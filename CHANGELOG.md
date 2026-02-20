# Changelog

All notable changes to this project will be documented in this file.

This project follows semantic versioning.

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
