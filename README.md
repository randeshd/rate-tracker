# Investment Tracker

Private web app comparing Sri Lankan fixed deposit rates (interest paid at maturity, normal rates).

- `scrapers/` – Python scrapers, one per institution, sharing a common data format
- `data/` – latest rates, ratings, CBSL ceiling and rate history (updated by GitHub Actions)
- `web/` – the web page (deployed on Vercel, password protected)

## Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m scrapers.run            # scrape everything
.venv/bin/python -m scrapers.run hnb seylan # scrape selected institutions
.venv/bin/pytest
```
