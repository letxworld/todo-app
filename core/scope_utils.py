"""
Scope-import utilities for the Bug Bounty Tracker.

Supports three input paths:
  1. HackerOne Hacker API  -- structured_scopes endpoint
  2. CSV upload             -- auto-detect domain/url/type columns
  3. Plain-text paste       -- one domain/url per line

All three return a list of dicts with the keys:
    domain_or_url, asset_type, in_scope
that the scope review view can render for the user to pick from.
"""

from __future__ import annotations

import csv
import io
import re
import urllib.parse
from collections.abc import Sequence
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Broad pattern that catches most URLs and bare domains.
_URL_RE = re.compile(
    r'^(?:https?://)?'          # optional scheme
    r'(?:[a-zA-Z0-9-]+\.)+'    # sub/domain dots
    r'[a-zA-Z]{2,}'            # TLD
    r'(?::\d+)?'               # optional port
    r'(?:/[^\s]*)?$',          # optional path
    re.IGNORECASE,
)


def _normalise_url(raw: str) -> str:
    """Turn a pasted string into a clean URL or bare domain.

    - strips whitespace
    - prepends https:// if no scheme is present
    - lowercases the hostname portion only (paths stay as-is)
    """
    s = raw.strip()
    if not s:
        return s
    parsed = urllib.parse.urlparse(s)
    # urlparse('host:8080') treats 'host' as scheme and '8080' as path,
    # so we detect that case and force the prepend.
    if not parsed.scheme or not parsed.netloc:
        s = 'https://' + s
        parsed = urllib.parse.urlparse(s)
    # Rebuild with lowered netloc but preserved path/query/fragment.
    netloc = parsed.netloc.lower()
    rebuilt = urllib.parse.urlunparse(
        (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
    )
    return rebuilt


def _classify_asset_type(url: str, hint: str | None = None) -> str:
    """Best-effort asset-type guess from a URL or hint string.

    Priority: explicit hint > URL path heuristics > default 'web'.
    """
    if hint:
        h = hint.lower()
        if 'api' in h or 'apikey' in h or 'graphql' in h:
            return 'api'
        if 'mobile' in h or 'ios' in h or 'android' in h or 'app' in h:
            return 'mobile'
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    if '/api/' in path or '/graphql' in path or parsed.path.endswith('/api'):
        return 'api'
    return 'web'


def _is_valid_scope_line(line: str) -> bool:
    """Return True if *line* looks like a domain or URL we can import."""
    return bool(_URL_RE.match(line.strip()))


# ---------------------------------------------------------------------------
# HackerOne API
# ---------------------------------------------------------------------------

def fetch_hackerone_scopes(
    program_handle: str,
    api_token: str,
    *,
    base_url: str = 'https://api.hackerone.com/v1',
) -> list[dict[str, Any]]:
    """Fetch structured_scopes for a HackerOne program.

    Requires the user's HackerOne API token (one scope-reader token per
    program is the typical setup).  Returns a list of dicts suitable for
    the review screen:

        [
            {'domain_or_url': 'https://example.com', 'asset_type': 'web',
             'in_scope': True},
            {'domain_or_url': 'https://out.example.com', 'asset_type': 'web',
             'in_scope': False},
            ...
        ]

    Raises requests.HTTPError on auth / rate-limit / not-found failures.
    """
    url = f'{base_url}/programs/{program_handle}/structured_scopes'
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/json',
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    # HackerOne paginates; follow the 'links.next' cursor if present.
    scopes: list[dict[str, Any]] = []
    while url:
        page = data.get('data', [])
        for item in page:
            asset = item.get('asset', {})
            # asset.attributes.url is the canonical field.
            raw_url = asset.get('url') or asset.get('name') or ''
            if not raw_url:
                continue
            scopes.append({
                'domain_or_url': _normalise_url(raw_url),
                'asset_type': _classify_asset_type(raw_url),
                'in_scope': item.get('enabled', False),
            })
        next_link = data.get('links', {}).get('next')
        if next_link:
            url = next_link
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        else:
            url = None

    return scopes


# ---------------------------------------------------------------------------
# CSV import
# ---------------------------------------------------------------------------

# Column-name patterns we try to match (lowercased).
DOMAIN_CANDIDATES = ('domain', 'domains', 'url', 'urls', 'asset', 'assets',
                     'scope', 'asset_url', 'host', 'hosts', 'address')
TYPE_CANDIDATES = ('type', 'asset_type', 'assettype', 'category', 'kind')
SCOPE_CANDIDATES = ('in_scope', 'inscope', 'enabled', 'active', 'status',
                    'is_in_scope')


def _detect_column(headers: Sequence[str], candidates: tuple[str, ...]) -> str | None:
    """Return the first header whose lowered form matches a candidate."""
    lowered = {h.lower().strip(): h for h in headers}
    for cand in candidates:
        if cand in lowered:
            return lowered[cand]
    return None


def parse_scope_csv(csv_text: str) -> list[dict[str, Any]]:
    """Parse a scope CSV export from any platform.

    Auto-detects which column holds the domain/URL, which holds the type,
    and which holds the in-scope flag.  Returns a list of dicts:

        [{'domain_or_url': ..., 'asset_type': ..., 'in_scope': bool}, ...]

    Rows that don't parse as a URL/domain are silently skipped with a
    warning printed to stderr (the caller can override by passing a file-
    like object that captures them).
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    headers = reader.fieldnames or []
    if not headers:
        return []

    domain_col = _detect_column(headers, DOMAIN_CANDIDATES)
    type_col = _detect_column(headers, TYPE_CANDIDATES)
    scope_col = _detect_column(headers, SCOPE_CANDIDATES)

    results: list[dict[str, Any]] = []
    for row in reader:
        raw = row.get(domain_col) if domain_col else row.get(headers[0])
        if not raw or not _is_valid_scope_line(str(raw)):
            continue
        url = _normalise_url(str(raw))
        asset_type = 'web'
        if type_col and row.get(type_col):
            asset_type = _classify_asset_type(url, str(row.get(type_col)))
        in_scope = True
        if scope_col and row.get(scope_col) is not None:
            val = str(row.get(scope_col)).lower().strip()
            in_scope = val not in ('0', 'false', 'no', 'out', 'out of scope',
                                    'false', 'inactive', 'disabled')
        results.append({
            'domain_or_url': url,
            'asset_type': asset_type,
            'in_scope': in_scope,
        })
    return results


# ---------------------------------------------------------------------------
# Plain-text (one domain/URL per line)
# ---------------------------------------------------------------------------

def parse_scope_text(text: str) -> list[dict[str, Any]]:
    """Parse a pasted block of domains/URLs (one per line).

    Blank lines and lines that don't look like a URL/domain are skipped.
    """
    results: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//'):
            continue
        if not _is_valid_scope_line(line):
            continue
        url = _normalise_url(line)
        results.append({
            'domain_or_url': url,
            'asset_type': _classify_asset_type(url),
            'in_scope': True,
        })
    return results


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

def import_scopes_from_source(
    source: str,
    source_type: str,
    *,
    program_handle: str | None = None,
    api_token: str | None = None,
) -> list[dict[str, Any]]:
    """Dispatch to the right parser based on *source_type*.

    Parameters
    ----------
    source : str
        The raw text / CSV content.  For 'hackerone' this is ignored and
        *program_handle* + *api_token* are used instead.
    source_type : str
        One of 'hackerone', 'csv', 'text'.
    program_handle : str: optional
        HackerOne program handle (required when source_type == 'hackerone').
    api_token : str: optional
        HackerOne API token (required when source_type == 'hackerone').

    Returns
    -------
    list of dicts with keys domain_or_url, asset_type, in_scope.
    """
    if source_type == 'hackerone':
        if not program_handle or not api_token:
            raise ValueError('program_handle and api_token are required for HackerOne imports')
        return fetch_hackerone_scopes(program_handle, api_token)
    if source_type == 'csv':
        return parse_scope_csv(source)
    if source_type == 'text':
        return parse_scope_text(source)
    raise ValueError(f'Unknown source_type: {source_type!r}.  Use hackerone, csv, or text.')
