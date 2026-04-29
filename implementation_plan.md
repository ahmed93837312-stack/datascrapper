# Scraper Agent — Implementation Plan

## Overview
Build a production-ready scraper agent with 3 independent modules (Upwork, LinkedIn, Local Directories) plus a premium Next.js dashboard connected via a FastAPI API server.

## Architecture

```
c:\datascrap\
├── backend/
│   ├── main.py                    # CLI runner with argparse
│   ├── api_server.py              # FastAPI API for frontend
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── upwork_scraper.py      # Upwork RSS + search scraper
│   │   ├── linkedin_scraper.py    # LinkedIn Selenium scraper
│   │   └── directories_scraper.py # YellowPages/Yelp/Canada411
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── csv_handler.py         # Shared CSV read/write utilities
│   │   └── logger.py              # Centralized logging config
│   ├── output/                    # CSV output directory
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── pages/
│   │   ├── index.js               # Dashboard home
│   │   ├── upwork.js              # Upwork detail page
│   │   ├── linkedin.js            # LinkedIn detail page
│   │   └── directories.js         # Directories detail page
│   ├── components/
│   │   ├── Card.js                # Glassmorphism card
│   │   ├── ProgressBar.js         # Animated progress bar
│   │   ├── Navbar.js              # Navigation bar
│   │   └── Layout.js              # Page layout wrapper
│   ├── styles/
│   │   └── globals.css            # Global styles + design tokens
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
└── README.md
```

## Backend Strategy

### Scraper Approaches
| Module | Method | Rationale |
|--------|--------|-----------|
| Upwork | `requests` + `BeautifulSoup` + RSS feeds | Upwork RSS feeds are publicly accessible for search queries |
| LinkedIn | `Selenium` + Chrome WebDriver | LinkedIn requires authenticated sessions |
| Directories | `requests` + `BeautifulSoup` | Standard HTML pages, well-structured |

### API Server (FastAPI)
- `POST /api/scrape/{module}` — trigger a scraper run
- `GET /api/status/{module}` — get scraping progress
- `GET /api/download/{module}` — download CSV
- `GET /api/stats` — get aggregate stats for dashboard

## Frontend Design
- Glassmorphism cards with `backdrop-filter: blur()`
- Color palette: Deep indigo/violet gradients, soft slate backgrounds
- Typography: Inter from Google Fonts
- Framer Motion for page transitions, card hover effects, progress animations

## Verification
- Run each scraper module independently via CLI
- Start FastAPI server and test all endpoints
- Start Next.js dev server and verify UI renders correctly
- Test scraper trigger → progress → download flow
