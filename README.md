# DataScrap Agent
## AI-Powered Lead Generation Scraper with Premium Dashboard

A production-ready scraper agent with 3 independent modules and a glassmorphism Next.js dashboard.

---

## Architecture

```
datascrap/
├── backend/                    # Python scraper engine + API
│   ├── main.py                 # CLI runner (--upwork, --linkedin, --directories, --all)
│   ├── api_server.py           # FastAPI server for frontend integration
│   ├── scrapers/
│   │   ├── upwork_scraper.py   # Upwork RSS + search scraper
│   │   ├── linkedin_scraper.py # LinkedIn Selenium scraper
│   │   └── directories_scraper.py  # YellowPages, Yelp, Canada411
│   ├── utils/
│   │   ├── logger.py           # Centralized logging
│   │   └── csv_handler.py      # CSV read/write utilities
│   ├── output/                 # CSV output files
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # Next.js + Tailwind CSS + Framer Motion
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.js        # Dashboard home
│   │   │   ├── upwork.js       # Upwork detail view
│   │   │   ├── linkedin.js     # LinkedIn detail view
│   │   │   └── directories.js  # Directories detail view
│   │   ├── components/
│   │   │   ├── Card.js         # Glassmorphism scraper card
│   │   │   ├── ProgressBar.js  # Animated progress bar
│   │   │   ├── Navbar.js       # Navigation bar
│   │   │   └── Layout.js       # Page layout wrapper
│   │   └── styles/
│   │       └── globals.css     # Global design system
│   └── package.json
└── README.md
```

---

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure LinkedIn credentials
copy .env.example .env
# Edit .env and add your LinkedIn email/password
```

### 2. Run Scrapers via CLI

```bash
# Run individual scrapers
python main.py --upwork
python main.py --linkedin
python main.py --directories

# Run all scrapers
python main.py --all

# Run specific combination
python main.py --upwork --directories
```

### 3. Start API Server (for dashboard)

```bash
cd backend
python api_server.py
# → Server runs at http://localhost:8000
# → API docs at http://localhost:8000/docs
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies (already done if you ran create-next-app)
npm install

# Start development server
npm run dev
# → Dashboard runs at http://localhost:3000
```

---

## Scraper Modules

### Module 1: Upwork Scraper
- **Method**: RSS feeds + HTML fallback
- **Keywords**: AI automation, AI chatbot, SaaS, web development, app development
- **Fields**: Project Title, Description, Budget, Client Location, Client Spend History, Posted Date
- **Output**: `output/upwork_jobs.csv`

### Module 2: LinkedIn Scraper
- **Method**: Selenium WebDriver with authentication
- **Keywords**: AI automation, AI chatbot, SaaS, web development, app development
- **Fields**: Job Title, Company Name, Recruiter Name, Location, Job Description
- **Output**: `output/linkedin_jobs.csv`
- **Requires**: `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` in `.env`

### Module 3: Local Directories Scraper
- **Sources**: Yellow Pages (U.S.), Yelp (U.S.), Canada411 (Canada)
- **Niches**: logistics, retail, healthcare, education
- **Fields**: Business Name, Industry, Phone, Email, Website, Location
- **Output**: `output/local_directories.csv`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Health check |
| `POST` | `/api/scrape/{module}` | Start a scraper (upwork/linkedin/directories) |
| `GET`  | `/api/status/{module}` | Get scraping progress |
| `GET`  | `/api/download/{module}` | Download CSV file |
| `GET`  | `/api/preview/{module}` | Preview CSV data (first 50 rows) |
| `GET`  | `/api/stats` | Dashboard statistics |

---

## Environment Variables

| Variable | Description | Required For |
|----------|-------------|--------------|
| `LINKEDIN_EMAIL` | LinkedIn login email | LinkedIn scraper |
| `LINKEDIN_PASSWORD` | LinkedIn login password | LinkedIn scraper |

---

## Tech Stack

### Backend
- Python 3.10+
- FastAPI + Uvicorn
- Requests + BeautifulSoup4
- Selenium (LinkedIn automation)
- python-dotenv

### Frontend
- Next.js (Pages Router)
- Tailwind CSS
- Framer Motion
- Inter font (Google Fonts)

---

## Important Notes

1. **Rate Limiting**: All scrapers include polite delays between requests to avoid being blocked.
2. **Anti-Detection**: The LinkedIn scraper uses anti-detection measures (custom User-Agent, disabled automation flags, human-like typing).
3. **Error Handling**: Each module handles errors gracefully with try/except blocks and detailed logging.
4. **Logging**: All activity is logged to both console and `logs/` directory.
5. **De-duplication**: Results are de-duplicated before saving to CSV.
