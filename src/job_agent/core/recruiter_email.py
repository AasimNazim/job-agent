import html
import json
import logging
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Dict, Iterable, Optional
from urllib.parse import urljoin, urlparse

import httpx

from ..models.job import Job

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PLACEHOLDER_DOMAINS = {"example.com", "example.org", "example.net", "test.com"}
UNSUITABLE_PREFIXES = ("noreply@", "no-reply@", "do-not-reply@", "donotreply@")
RELEVANT_LINK_WORDS = ("career", "job", "recruit", "talent", "hiring", "hr", "graduate", "university", "contact")


@dataclass(frozen=True)
class RecruiterEmailResult:
    email: Optional[str]
    status: str
    source_url: Optional[str]


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.emails: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._href: Optional[str] = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attributes = dict(attrs)
        if tag == "a":
            self._href = attributes.get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        self.emails.extend(EMAIL_RE.findall(html.unescape(data)))
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text)))
            self._href = None
            self._text = []


class RecruiterEmailDiscovery:
    """Find publicly displayed application contacts without guessing addresses."""

    def __init__(self, timeout: float = 10.0, client: Optional[httpx.Client] = None) -> None:
        self.timeout = timeout
        self.client = client
        self._official_cache: Dict[str, RecruiterEmailResult] = {}
        self.verified_count = 0
        self.not_found_count = 0

    @staticmethod
    def _valid_email(email: str) -> bool:
        normalized = email.strip().lower().rstrip(".,;:)")
        if not EMAIL_RE.fullmatch(normalized):
            return False
        domain = normalized.rsplit("@", 1)[1]
        return domain not in PLACEHOLDER_DOMAINS and not normalized.startswith(UNSUITABLE_PREFIXES)

    @classmethod
    def is_verified_email(cls, email: Optional[str], status: str, source_url: Optional[str]) -> bool:
        return bool(email and status == "VERIFIED" and source_url and cls._valid_email(email))

    @classmethod
    def _first_valid(cls, emails: Iterable[str], preferred_host: Optional[str] = None) -> Optional[str]:
        valid = []
        for email in emails:
            normalized = email.strip().lower().rstrip(".,;:)")
            if cls._valid_email(normalized) and normalized not in valid:
                valid.append(normalized)
        if preferred_host:
            preferred = [email for email in valid if email.rsplit("@", 1)[1] == preferred_host]
            if preferred:
                return preferred[0]
        return valid[0] if valid else None

    def _get(self, url: str) -> Optional[str]:
        try:
            client = self.client or httpx.Client(timeout=self.timeout, follow_redirects=True)
            response = client.get(url)
            response.raise_for_status()
            return response.text
        except (httpx.HTTPError, ValueError) as exc:
            logger.debug("Could not inspect public contact page %s: %s", url, exc)
            return None
        finally:
            if self.client is None and "client" in locals():
                client.close()

    @staticmethod
    def _parse(content: str) -> _PageParser:
        parser = _PageParser()
        parser.feed(content)
        return parser

    def _inspect_page(self, url: str, preferred_host: Optional[str] = None) -> RecruiterEmailResult:
        content = self._get(url)
        if content is None:
            return RecruiterEmailResult(None, "NOT_FOUND", None)
        parser = self._parse(content)
        mailto_emails = [href[7:].split("?", 1)[0] for href, _ in parser.links if href.lower().startswith("mailto:")]
        email = self._first_valid([*mailto_emails, *parser.emails], preferred_host)
        if email:
            return RecruiterEmailResult(email, "VERIFIED", url)
        return RecruiterEmailResult(None, "NOT_FOUND", None)

    def _inspect_official_pages(self, career_url: str) -> RecruiterEmailResult:
        cached = self._official_cache.get(career_url)
        if cached:
            return cached

        host = urlparse(career_url).netloc.lower().split(":", 1)[0]
        content = self._get(career_url)
        if content is None:
            result = RecruiterEmailResult(None, "NOT_FOUND", None)
            self._official_cache[career_url] = result
            return result

        parser = self._parse(content)
        email = self._first_valid(
            [href[7:].split("?", 1)[0] for href, _ in parser.links if href.lower().startswith("mailto:")] + parser.emails,
            host,
        )
        if email:
            result = RecruiterEmailResult(email, "VERIFIED", career_url)
            self._official_cache[career_url] = result
            return result

        visited = set()
        for href, label in parser.links:
            page_url = urljoin(career_url, href)
            parsed = urlparse(page_url)
            searchable = f"{label} {parsed.path}".lower()
            if parsed.scheme not in ("http", "https") or parsed.netloc.lower().split(":", 1)[0] != host:
                continue
            if page_url in visited or not any(word in searchable for word in RELEVANT_LINK_WORDS):
                continue
            visited.add(page_url)
            result = self._inspect_page(page_url, host)
            if result.email:
                self._official_cache[career_url] = result
                return result

        result = RecruiterEmailResult(None, "NOT_FOUND", None)
        self._official_cache[career_url] = result
        return result

    def discover(self, job: Job, career_url: Optional[str] = None) -> RecruiterEmailResult:
        """Inspect the posting, embedded API content, then cached official company pages."""
        posting = self._inspect_page(job.url, urlparse(career_url).netloc.lower().split(":", 1)[0] if career_url else None)
        if not posting.email and job.description:
            email = self._first_valid(EMAIL_RE.findall(html.unescape(job.description)))
            if email:
                posting = RecruiterEmailResult(email, "VERIFIED", job.url)
        if not posting.email and job.raw_data:
            try:
                raw_data = json.loads(job.raw_data)
            except (TypeError, ValueError):
                raw_data = {}
            raw_text = json.dumps(raw_data)
            email = self._first_valid(EMAIL_RE.findall(html.unescape(raw_text)))
            if email:
                posting = RecruiterEmailResult(email, "VERIFIED", job.url)
        if not posting.email and career_url:
            posting = self._inspect_official_pages(career_url)

        logger.info("[EMAIL] Job: %s", job.title)
        logger.info("[EMAIL] Company: %s", job.company_name)
        logger.info("[EMAIL] Recruiter email: %s", posting.email or "NOT FOUND")
        logger.info("[EMAIL] Status: %s", posting.status)
        logger.info("[EMAIL] Source: %s", posting.source_url or "NOT FOUND")
        if posting.status == "VERIFIED":
            self.verified_count += 1
        else:
            self.not_found_count += 1
        return posting