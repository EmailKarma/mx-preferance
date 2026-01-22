# MX Provider Classifier

A Python tool that analyzes email addresses or domains, looks up their MX records, and classifies them by mailbox provider or mail infrastructure.

This tool helps answer questions like:

* How many domains use Gmail, Microsoft 365, Yahoo, or other providers?
* Which domains are behind security gateways like Mimecast or Proofpoint?
* Which domains are misconfigured or not mail-ready?
* Which domains run custom or self-hosted mail systems?

## What the tool does

Given a source file containing **email addresses and/or domains**, the script will:

1. Extract the domain portion (from email addresses if needed).
2. Perform MX lookups for each domain.
3. Use **only the highest-priority MX records** (lowest preference value).
4. Classify domains based on a pattern table you control.
5. Return three CSV outputs:

   * Provider counts
   * Domain-to-provider mapping
   * DNS failures and edge cases

## Supported classifications

Out of the box, the tool can identify:

* Gmail 
* Google Workspace
* Outlook 
* Microsoft 365
* Yahoo
* iCloud Mail
* Proton Mail
* Mimecast
* Proofpoint (Enterprise and Essentials)
* GoDaddy / SecureServer
* Various regional and niche providers
* Custom MX (self-hosted or unknown providers)
* Bad domains (DNS failures, no MX, NXDOMAIN, etc.)

New providers can be added by editing the provider_patterns.csv file. No code changes required.

---

## Repository structure

```text
scripts/
├── mx_provider_classifier.py
├── provider_patterns.csv
```

Note: Both files should live in the same directory.

---

## Requirements

* Python 3.9 or newer
* `dnspython`

Install dependencies:

```bash
pip install dnspython
```
or
```bash
pip install -r requirements.txt
```

---

## Input file format

The input file can contain:

* Email addresses
* Domains
* Mixed content

Supported formats:

* Plain text (one value per line)
* CSV files (domain or email in the first column)

Examples:

```text
user@example.com
example.org
marketing@company.ca
```

or

```csv
email
user@example.com
sales@brand.com
```

---

## How MX classification works

* The script looks up **all MX records** for a domain.
* It selects the **highest-priority MX set** (lowest preference value).
* If multiple MX records share that priority, all are evaluated.
* The MX hostnames are compared against `provider_patterns.csv`.
* The first matching pattern (by priority) determines the provider.

If no pattern matches:

* Domains with MX records are labeled **Custom MX**.
* Domains without MX records or with DNS errors are labeled **Bad Domain** with a reason.

---

## Running the tool

### Basic usage

From the repository root:

```bash
python [location]/mx_provider_classifier.py
```

You’ll be prompted for the input file path.

### Specify the input file directly

```bash
python [PATH]/mx_provider_classifier.py --input [PATH]/domains.txt
```

### Use a specific DNS resolver

By default, the system resolver is used. You can override it:

```bash
python [PATH]/mx_provider_classifier.py \
  --input [PATH]/domains.txt \
  --nameserver 8.8.8.8
```

This is useful for:

* Reproducible results
* Debugging DNS inconsistencies
* Avoiding local resolver caching

### Adjust DNS timeout

```bash
python [PATH]/mx_provider_classifier.py --timeout 6.0
```

Default is 4 seconds.

### Control concurrency

MX lookups run in parallel. Adjust if you’re hitting rate limits:

```bash
python [PATH]/mx_provider_classifier.py --workers 10
```

Default is 20.

---

## Output files

All output files are written to the current directory and follow this format:

```text
YYYY-MM-DD-[result type]-[original file name].csv
```

### 1. Provider counts

Example filename:

```text
2026-01-22-counts-domains.txt.csv
```

Columns:

* `provider`
* `domain_count`

### 2. Domain classification

Example filename:

```text
2026-01-22-domains-domains.txt.csv
```

Columns:

* `domain`
* `provider`
* `best_mx_preference`
* `mx_hosts`

MX hosts are semicolon-separated.

### 3. Unclassified and DNS errors

Example filename:

```text
2026-01-22-unclassified-domains.txt.csv
```

Columns:

* `domain`
* `best_mx_preference`
* `mx_hosts`
* `error`

This file is your review queue for:

* New providers to pattern
* DNS failures
* Edge cases

---

## Provider pattern configuration

All provider logic lives in `provider_patterns.csv`.

Example:

```csv
provider,match_type,pattern,priority,notes
Microsoft 365,suffix,mail.protection.outlook.com,10,Exchange Online Protection
Google Workspace,suffix,aspmx.l.google.com,10,Workspace primary MX
Mimecast,suffix,mimecast.com,10,Inbound security gateway
Custom Provider,suffix,example.net,20,Example provider
```

### Match types

* `suffix`: hostname ends with the pattern
* `contains`: hostname contains the pattern
* `exact`: full hostname match
* `regex`: Python regular expression

Lower priority numbers win.

---

## Bad domain classification

The tool automatically labels DNS failures:

* **Bad Domain – No MX**
  Domain exists but has no MX records.
* **Bad Domain – NXDOMAIN**
  Domain does not exist.
* **Bad Domain – Timeout**
  DNS lookup failed.
* **Bad Domain – NoNameservers**
  Broken or missing delegation.

These are included in provider counts by default.

---

## When to use this tool

This tool is ideal for:

* List hygiene and acquisition analysis
* Provider mix reporting
* ESP and gateway migration analysis
* Deliverability investigations
* Sales, audit, and compliance workflows

NOTE: This is not an email validation tool. It does not check mailbox existence.