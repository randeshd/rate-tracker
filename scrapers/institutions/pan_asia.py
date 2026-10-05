from ..core.fetch import fetch_text
from ..core.models import Institution, Rate

INSTITUTION = Institution(
    id="pan_asia",
    name="Pan Asia Bank",
    type="bank",
    source_url="https://www.pabcbank.com/rates-tariffs/",
)


def scrape() -> list[Rate]:
    html = fetch_text(INSTITUTION.source_url)
    if "sucuri_cloudproxy_js" in html or "You are being redirected" in html:
        # The site answers automated requests with a bot-protection challenge. We do not bypass it.
        raise RuntimeError("site blocks automated access (bot-protection challenge)")
    raise NotImplementedError("page became reachable: parser needs to be written")
