# DataScrap Agent - Project Memory & State

This file serves as the core memory for the project. If you bring a new AI assistant into this workspace in the future, point them to this file to get them instantly up to speed on the architecture, current state, and known quirks of the system.

## Project Overview
**Name**: DataScrap Agent
**Goal**: A modular, Next.js dashboard that triggers asynchronous Python/FastAPI scrapers to gather leads from LinkedIn, Upwork, and Local Directories (Yelp, YellowPages, Canada411) using Selenium to bypass enterprise bot-protections.

---

## 🏗 System Architecture

### 1. The Backend (`/backend`)
- **Framework**: FastAPI (`api_server.py`) serving endpoints at `http://localhost:8000`.
- **Core Engine**: Selenium WebDriver running Headless (mostly) to emulate real browsers.
- **Scraper Modules**:
  1. `upwork_scraper.py`: Extracts jobs. VERY aggressive Cloudflare protection. 
  2. `linkedin_scraper.py`: Extracts jobs. Standard security challenge.
  3. `directories_scraper.py`: Extracts physical businesses from Yelp, YP, Canada411.
- **Running the Backend**:
  ```powershell
  cd c:\datascrap\backend
  .\venv\Scripts\activate
  uvicorn api_server:app --reload --port 8000
  ```

### 2. The Frontend (`/frontend`)
- **Framework**: Next.js (Pages router) with Tailwind CSS and Framer Motion.
- **Design**: Premium Glassmorphism UI. Dashboard tracks progress in real-time by polling the FastAPI backend.
- **Running the Frontend**:
  ```powershell
  cd c:\datascrap\frontend
  npm run dev
  ```

---

## 🔒 Security Bypasses & Known Quirks (CRITICAL)

Because we are scraping highly protected enterprise websites, we had to implement aggressive workarounds:

### Upwork (The Cloudflare Loop)
Upwork uses Cloudflare Turnstile which infinitely loops generic Selenium bots.
- **The Fix**: The scraper is hardcoded to "Hijack" the user's real personal Google Chrome profile located at `C:\Users\SM\AppData\Local\Google\Chrome\User Data`.
- **The Catch**: **ALL normal Google Chrome windows MUST be closed** before running the Upwork scraper, otherwise the script will crash saying "User Data is already in use".

### LinkedIn (The Security PIN)
LinkedIn will occasionally intercept the login with a "Verify it's you" code sent to email.
- **The Fix**: The scraper runs in `headless=False` mode (visible) when run stand-alone so the user has 60 seconds to solve the captcha. Make sure `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` are valid in `backend/.env`.

### Local Directories (403 Forbidden)
Yelp and YellowPages block standard Python requests with 403 errors.
- **The Fix**: Migrated to a hybrid approach. Selenium `driver.get()` fetches the raw HTML page source to bypass the firewall, and `BeautifulSoup` instantly parses it. Runs totally invisibly.

---

## 🚀 Where We Left Off
1. Migrated **Local Directories** to Selenium. Tested successfully against New York Logistics.
2. Verified **LinkedIn** scraper successfully logs in and parses data (fixed the slow `implicitly_wait` 10-second penalty bug).
3. Upgraded **Upwork** to use the Real-Chrome-Profile hijack.

**Next Immediate Steps for the Developer:**
- Close all Chrome windows and test the Upwork scraper.
- Run a full batch extraction from the Next.js Dashboard to verify all 3 modules populate the CSVs correctly.
