import hashlib
from urllib.parse import urlparse, urlunparse

def normalize_url(url: str) -> str:
    """
    Normalizes job URLs by removing trailing slashes, stripping whitespace,
    and lowercasing scheme/netloc while keeping query/path consistent.
    """
    if not url:
        return ""
    url = url.strip()
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip('/')
    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, parsed.fragment))

def generate_canonical_content_hash(company_name: str, title: str, url: str, source_job_id: str = "") -> str:
    """
    Generates a stable canonical content hash for job deduplication.
    Excludes mutable fields like location string, posted date, or dynamic tags.
    """
    norm_company = (company_name or "").strip().lower()
    norm_title = (title or "").strip().lower()
    norm_url = normalize_url(url)
    norm_source_id = (source_job_id or "").strip()

    if norm_source_id:
        raw_key = f"{norm_company}|{norm_title}|{norm_source_id}|{norm_url}"
    else:
        raw_key = f"{norm_company}|{norm_title}|{norm_url}"

    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
