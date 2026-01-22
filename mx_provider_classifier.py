#!/usr/bin/env python3
"""
MX Provider Classifier
- Input: file containing emails and/or domains.
- MX lookup: uses only the highest-priority MX set (lowest preference value).
- Output:
  1) YYYY-MM-DD-counts-<original>.csv
  2) YYYY-MM-DD-domains-<original>.csv
  3) YYYY-MM-DD-unclassified-<original>.csv

Patterns are loaded from a CSV file so you can extend providers easily.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    import dns.resolver
except ImportError:
    print("Missing dependency: dnspython. Install with: pip install dnspython", file=sys.stderr)
    sys.exit(1)


# ----------------------------
# Pattern model + matching
# ----------------------------

@dataclass(frozen=True)
class ProviderPattern:
    provider: str
    match_type: str  # suffix | contains | regex | exact
    pattern: str
    priority: int = 100
    notes: str = ""

    def matches(self, mx_host: str) -> bool:
        h = mx_host.rstrip(".").lower()
        p = self.pattern.rstrip(".").lower()

        if self.match_type == "suffix":
            return h.endswith(p)
        if self.match_type == "contains":
            return p in h
        if self.match_type == "exact":
            return h == p
        if self.match_type == "regex":
            return re.search(self.pattern, h, flags=re.IGNORECASE) is not None

        return False


def load_patterns(patterns_csv_path: str) -> List[ProviderPattern]:
    patterns: List[ProviderPattern] = []
    with open(patterns_csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"provider", "match_type", "pattern"}
        missing = required - set((reader.fieldnames or []))
        if missing:
            raise ValueError(f"patterns CSV missing required columns: {sorted(missing)}")

        for row in reader:
            provider = (row.get("provider") or "").strip()
            match_type = (row.get("match_type") or "").strip().lower()
            pattern = (row.get("pattern") or "").strip()
            if not provider or not match_type or not pattern:
                continue

            priority_str = (row.get("priority") or "").strip()
            notes = (row.get("notes") or "").strip()
            try:
                priority = int(priority_str) if priority_str else 100
            except ValueError:
                priority = 100

            patterns.append(ProviderPattern(
                provider=provider,
                match_type=match_type,
                pattern=pattern,
                priority=priority,
                notes=notes,
            ))

    patterns.sort(key=lambda x: x.priority)
    return patterns


def classify_mx_hosts(mx_hosts: List[str], patterns: List[ProviderPattern]) -> Optional[str]:
    """
    Decide provider for a domain based on its MX hosts (already filtered to highest-priority set).
    Strategy:
      - Walk patterns by priority (pattern-table priority).
      - If any MX host matches a pattern, return that provider.
    """
    if not mx_hosts:
        return None

    for pat in patterns:
        for h in mx_hosts:
            if pat.matches(h):
                return pat.provider
    return None

def provider_from_dns_error(err: Optional[str]) -> Optional[str]:
    if not err:
        return None
    if err == "NoAnswer":
        return "Bad Domain - No MX"
    if err == "NXDOMAIN":
        return "Bad Domain - NXDOMAIN"
    if err == "Timeout":
        return "Bad Domain - Timeout"
    if err == "NoNameservers":
        return "Bad Domain - NoNameservers"
    return "Bad Domain - DNS Error"

def is_subdomain(child: str, parent: str) -> bool:
    child = child.rstrip(".").lower()
    parent = parent.rstrip(".").lower()
    return child == parent or child.endswith("." + parent)


# ----------------------------
# Input parsing
# ----------------------------

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Z0-9-]{1,63}(?<!-)(\.(?!-)[A-Z0-9-]{1,63}(?<!-))+$",
    re.IGNORECASE
)

EMAIL_RE = re.compile(r"^\s*[^@\s]+@([^@\s]+)\s*$")


def extract_domain(value: str) -> Optional[str]:
    v = (value or "").strip().strip(",").strip(";").strip()
    if not v:
        return None

    m = EMAIL_RE.match(v)
    if m:
        d = m.group(1).strip().lower().rstrip(".")
        return d if DOMAIN_RE.match(d) else None

    d = v.lower().rstrip(".")
    return d if DOMAIN_RE.match(d) else None


def read_domains_from_file(path: str) -> List[str]:
    domains: List[str] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        sample = f.read(4096)
        f.seek(0)
        is_csvish = "," in sample or "\t" in sample or ";" in sample

        if is_csvish:
            try:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    candidates = row[:3] if len(row) >= 3 else row
                    for cell in candidates:
                        d = extract_domain(cell)
                        if d:
                            domains.append(d)
                            break
                return sorted(set(domains))
            except csv.Error:
                f.seek(0)

        for line in f:
            line = line.strip()
            if not line:
                continue

            d = extract_domain(line)
            if d:
                domains.append(d)
                continue

            for part in re.split(r"[\s,;]+", line):
                d2 = extract_domain(part)
                if d2:
                    domains.append(d2)

    return sorted(set(domains))


# ----------------------------
# MX lookup (highest priority only)
# ----------------------------

def build_resolver(nameserver: Optional[str], timeout: float) -> dns.resolver.Resolver:
    r = dns.resolver.Resolver(configure=True)
    r.lifetime = timeout
    r.timeout = timeout
    if nameserver:
        r.nameservers = [nameserver]
    return r


def lookup_mx_highest_priority(
    domain: str,
    resolver: dns.resolver.Resolver
) -> Tuple[str, Optional[int], List[str], Optional[str]]:
    """
    Returns (domain, best_pref, mx_hosts_at_best_pref_sorted, error_message)

    "Highest priority MX" means the lowest preference value.
    If multiple MX records share that preference, we keep them all.
    """
    try:
        answers = resolver.resolve(domain, "MX")
        records: List[Tuple[int, str]] = []
        for rdata in answers:
            pref = int(getattr(rdata, "preference"))
            host = str(getattr(rdata, "exchange")).rstrip(".").lower()
            records.append((pref, host))

        if not records:
            return domain, None, [], "NoAnswer"

        best_pref = min(pref for pref, _ in records)
        best_hosts = sorted({host for pref, host in records if pref == best_pref})
        return domain, best_pref, best_hosts, None

    except dns.resolver.NXDOMAIN:
        return domain, None, [], "NXDOMAIN"
    except dns.resolver.NoAnswer:
        return domain, None, [], "NoAnswer"
    except dns.resolver.NoNameservers:
        return domain, None, [], "NoNameservers"
    except dns.exception.Timeout:
        return domain, None, [], "Timeout"
    except Exception as e:
        return domain, None, [], f"Error: {type(e).__name__}"


# ----------------------------
# Output helpers
# ----------------------------

def dated_output_name(input_path: str, result_type: str) -> str:
    base = os.path.basename(input_path)
    today = dt.date.today().strftime("%Y-%m-%d")
    return f"{today}-{result_type}-{base}.csv"


def write_counts(path: str, provider_counts: Dict[str, int]) -> None:
    rows = sorted(provider_counts.items(), key=lambda x: (-x[1], x[0].lower()))
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["provider", "domain_count"])
        w.writerows(rows)


def write_domains(
    path: str,
    domain_to_provider: Dict[str, str],
    domain_to_best_pref: Dict[str, Optional[int]],
    domain_to_mx: Dict[str, List[str]],
) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["domain", "provider", "best_mx_preference", "mx_hosts"])
        for domain in sorted(domain_to_provider.keys()):
            provider = domain_to_provider[domain]
            best_pref = domain_to_best_pref.get(domain)
            mx_hosts = ";".join(domain_to_mx.get(domain, []))
            w.writerow([domain, provider, "" if best_pref is None else best_pref, mx_hosts])


def write_unclassified(
    path: str,
    unclassified: List[Tuple[str, Optional[int], List[str], Optional[str]]]
) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["domain", "best_mx_preference", "mx_hosts", "error"])
        for domain, best_pref, mx_hosts, err in sorted(unclassified, key=lambda x: x[0]):
            w.writerow([domain, "" if best_pref is None else best_pref, ";".join(mx_hosts), err or ""])


# ----------------------------
# Main
# ----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Classify domains by MX provider patterns (highest priority MX only).")
    ap.add_argument("--input", default=None, help="Path to input file. If omitted, you'll be prompted.")
    ap.add_argument("--patterns", default=os.path.join(SCRIPT_DIR, "provider_patterns.csv"), help="CSV file with MX classification patterns.")
    ap.add_argument("--nameserver", default=None, help="Optional DNS server IP to query (ex: 8.8.8.8).")
    ap.add_argument("--timeout", type=float, default=4.0, help="DNS timeout in seconds.")
    ap.add_argument("--workers", type=int, default=20, help="Concurrent lookup workers.")
    args = ap.parse_args()

    input_path = args.input
    if not input_path:
        input_path = input("Enter the path to your source file (emails/domains): ").strip()

    if not input_path or not os.path.exists(input_path):
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    if not os.path.exists(args.patterns):
        print(f"Patterns file not found: {args.patterns}", file=sys.stderr)
        print("Create it using the sample provider_patterns.csv shown earlier.", file=sys.stderr)
        return 2

    patterns = load_patterns(args.patterns)
    domains = read_domains_from_file(input_path)

    if not domains:
        print("No valid domains or emails found in input file.", file=sys.stderr)
        return 2

    resolver = build_resolver(args.nameserver, args.timeout)

    domain_to_mx: Dict[str, List[str]] = {}
    domain_to_best_pref: Dict[str, Optional[int]] = {}
    domain_to_provider: Dict[str, str] = {}
    unclassified: List[Tuple[str, Optional[int], List[str], Optional[str]]] = []

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = [ex.submit(lookup_mx_highest_priority, d, resolver) for d in domains]
        for fut in as_completed(futures):
            domain, best_pref, mx_hosts, err = fut.result()
            domain_to_best_pref[domain] = best_pref
            domain_to_mx[domain] = mx_hosts

            provider = classify_mx_hosts(mx_hosts, patterns)

            # Map DNS failures with no MX to explicit "Bad Domain" buckets
            if not provider and err and not mx_hosts:
                provider = provider_from_dns_error(err)

            # If MX exists but no provider matched, label as Custom MX
            if not provider and mx_hosts:
                provider = "Custom MX"

            if provider:
                domain_to_provider[domain] = provider
            else:
                # This should be rare now, but keep it for truly odd cases
                unclassified.append((domain, best_pref, mx_hosts, err))

    provider_counts: Dict[str, int] = {}
    for provider in domain_to_provider.values():
        provider_counts[provider] = provider_counts.get(provider, 0) + 1

    out_counts = dated_output_name(input_path, "counts")
    out_domains = dated_output_name(input_path, "domains")
    out_unclassified = dated_output_name(input_path, "unclassified")

    write_counts(out_counts, provider_counts)
    write_domains(out_domains, domain_to_provider, domain_to_best_pref, domain_to_mx)
    write_unclassified(out_unclassified, unclassified)

    print("Done.")
    print(f"Wrote: {out_counts}")
    print(f"Wrote: {out_domains}")
    print(f"Wrote: {out_unclassified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
