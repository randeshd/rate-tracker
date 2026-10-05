# Rate Tracker

Private web app comparing Sri Lankan fixed deposit rates (interest paid at maturity, normal rates).

## How it works

1. **Scrapers** (`scrapers/institutions/`, one per institution) read each institution's published rates
   and return them in a common format (`scrapers/core/models.py`).
2. **GitHub Actions** run the scrapers every day and the ratings refresh every Monday, then commit the
   results to `data/`.
3. **The web page** (`web/`, Next.js on Vercel) is rebuilt from `data/` on every commit and sits behind a
   password (`SITE_PASSWORD` environment variable in Vercel).

## The web page

One page (`web/app/Dashboard.tsx`, styled in `web/app/globals.css`) with three views, each filterable to
banks or finance companies:

- **By tenure**: every offer at the chosen tenure, ranked by AER, with credit ratings.
- **All tenures**: one row per institution across the standard tenures, the best AER in each tenure in
  green, and the CBSL ceiling for finance companies on top.
- **Best AER**: each institution's highest offer at any tenure.

Summary cards show the best bank and best finance company rate for the chosen tenure, and on desktop
the best overall rate across every institution and tenure.
Each shows AER; click a card to switch it to the nominal rate p.a. and back.

On phones (760px wide or less) the list becomes cards and the views move to a tab bar at the bottom.
The header shows the highest AER on offer across every institution and tenure, and in All tenures
tapping a rate shows its nominal rate p.a.

The logo is `web/app/Logo.tsx`. The icons are `icon.svg`, `favicon.ico` and `apple-icon.png` in
`web/app/`.

## Data files

| File | Contents |
| --- | --- |
| `data/latest.json` | Latest rates per institution, with status (`ok`, `stale`, `no_data`) |
| `data/history/rates.csv` | One row per institution, tenure and day |
| `data/ratings.json` | Credit ratings (Lanka Rating Agency list; Fitch as disclosed by each institution) |
| `data/cbsl.json` | CBSL maximum deposit rates for finance companies, T-bill average plus the margins in CBSL Directions No. 01 of 2026 |

AER for interest at maturity: `(1 + r*t)^(1/t) - 1`, with `t` the term in years.

## Scraping rules

- robots.txt is checked and crawl delays are honoured (minimum 3 seconds between requests to a site).
- Each page is requested at most once per day (responses are cached in `.cache/`).
- If a scraper fails, the last good rates are kept and the institution is marked stale.
- Sites that block automated access are not bypassed.

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
