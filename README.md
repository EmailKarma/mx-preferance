# MX Provider Classifier

## Overview

This tool analyses domains or email addresses and determines:

- Which provider handles inbound mail
- Whether the domain uses a security gateway
- Whether the domain does not accept mail
- Whether the domain is invalid or misconfigured

Provider classification is driven by a manually maintained
`provider_patterns.csv` file for maximum flexibility.

---

## Installation

Requires Python 3.9+

Install dependencies:

```

pip install -r requirements.txt

```

---

## Usage

```

python mx_provider_classifier.py

```

The script will prompt for:

1. Path to input file
2. Optional custom DNS nameserver

---

## DNS Configuration

By default, the script uses the system resolver.

You may optionally provide a specific nameserver via command-line flag or configuration update.

---

## Input Format

Accepts:

- Plain domain list
- Email address list
- CSV files (first column assumed domain/email)

Duplicates are preserved for reporting accuracy.

---

## Outputs

Given an input file:

```

input.csv

```

The script generates:

```

YYYY-MM-DD-counts-input.csv
YYYY-MM-DD-domain-provider-input.csv

```

### Counts File Columns

```

provider
domain_count
record_count

```

All classification buckets are included:

- Mailbox providers
- Security gateways
- Institutional platforms
- Custom MX
- Bad Domain categories

---

## Bad Domain Categories

The script detects:

- Bad Domain - NXDOMAIN
- Bad Domain - NoAnswer
- Bad Domain - Timeout
- Bad Domain - NoNameservers
- Bad Domain - No mail (Null MX per RFC 7505)

---

## Provider Pattern File

Classification is driven by:

```

provider_patterns.csv

```

Structure:

```

provider,match_type,pattern,priority,notes

```

Supported match types:

- `suffix`
- `exact`
- `regex`

Patterns are evaluated by priority.

---

## Design Principles

- One MX lookup per unique domain
- Preserve input record counts
- Avoid overfitting patterns
- Classify infrastructure, not customers
- Keep provider rules human-readable

---

## Version History

See `CHANGELOG.md` for detailed release notes.

---

## License

Internal / private use unless otherwise specified.
```