# Investment Tracker

Private web app comparing Sri Lankan fixed deposit rates (interest paid at maturity, normal rates).

## How it works

1. **Scrapers** (`scrapers/institutions/`, one per institution) read each institution's published rates
   and return them in a common format (`scrapers/core/models.py`).
2. **GitHub Actions** run the scrapers every day and the ratings refresh every Monday, then commit the
   results to `data/`.
3. **The web page** (`web/`, Next.js on Vercel) is rebuilt from `data/` on every commit and sits behind a
   password (`SITE_PASSWORD` environment variable in Vercel).

## Data files

| File | Contents |
| --- | --- |
| `data/latest.json` | Latest rates per institution, with status (`ok`, `stale`, `no_data`) |
| `data/history/rates.csv` | One row per institution, tenure and day |
| `data/ratings.json` | Credit ratings (Lanka Rating Agency list; Fitch as disclosed by each institution) |
| `data/cbsl.json` | CBSL maximum deposit rates for finance companies, derived from T-bill yields |

AER for interest at maturity: `(1 + r*t)^(1/t) - 1`, with `t` the term in years.

## Scraping rules

- robots.txt is checked and crawl delays are honoured (minimum 3 seconds between requests to a site).
- Each page is requested at most once per day (responses are cached in `.cache/`).
- If a scraper fails, the last good rates are kept and the institution is marked stale.
- Sites that block automated access are not bypassed; they show as "no data" (currently Pan Asia Bank).

## Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m scrapers.run            # all institutions
.venv/bin/python -m scrapers.run hnb seylan # selected institutions
.venv/bin/python -m scrapers.ratings        # credit ratings
.venv/bin/python -m scrapers.cbsl           # CBSL ceiling
.venv/bin/pytest
```

Web page:

```bash
cd web && npm install
echo "SITE_PASSWORD=choose-a-local-password" > .env.local
npm run dev
```
