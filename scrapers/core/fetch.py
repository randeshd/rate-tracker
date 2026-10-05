"""Polite HTTP fetching: robots.txt, crawl delay, clear user agent, one request per URL per day."""
import hashlib
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests

USER_AGENT = "RateTrackerBot/1.0 (personal fixed-deposit rate comparison; one request per page per day)"
DEFAULT_DELAY = 3.0  # seconds between requests to the same host
TIMEOUT = 40
CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache"

_robots: dict[str, RobotFileParser | None] = {}
_last_hit: dict[str, float] = {}


class RobotsDisallowed(Exception):
    pass


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en"})
    return s


def _robots_for(host_url: str) -> RobotFileParser | None:
    if host_url not in _robots:
        rp = RobotFileParser()
        try:
            resp = _session().get(host_url + "/robots.txt", timeout=TIMEOUT)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            else:
                rp = None  # no robots.txt: nothing is disallowed
        except requests.RequestException:
            rp = None
        _robots[host_url] = rp
        _last_hit[host_url] = time.monotonic()
    return _robots[host_url]


def _cache_path(url: str) -> Path:
    key = hashlib.sha256(url.encode()).hexdigest()[:24]
    return CACHE_DIR / date.today().isoformat() / key


def fetch(url: str, **kwargs) -> bytes:
    """GET a URL at most once per day (later calls the same day are served from disk)."""
    cached = _cache_path(url)
    if cached.exists():
        return cached.read_bytes()

    parts = urlsplit(url)
    host_url = f"{parts.scheme}://{parts.netloc}"
    rp = _robots_for(host_url)
    delay = DEFAULT_DELAY
    if rp is not None:
        if not rp.can_fetch(USER_AGENT, url):
            raise RobotsDisallowed(f"robots.txt disallows {url}")
        delay = max(delay, float(rp.crawl_delay(USER_AGENT) or 0))

    wait = _last_hit.get(host_url, -1e9) + delay - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    try:
        resp = _session().get(url, timeout=TIMEOUT, **kwargs)
    finally:
        _last_hit[host_url] = time.monotonic()
    resp.raise_for_status()

    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(resp.content)
    return resp.content


def fetch_text(url: str, **kwargs) -> str:
    return fetch(url, **kwargs).decode("utf-8", errors="replace")
