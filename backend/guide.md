# Guide: Setting Up LinkedIn Credentials

The LinkedIn scraper module uses **Selenium** to simulate a real user login. Because LinkedIn requires authentication to view full job details and search results effectively, you must provide your account credentials.

## 1. Setup Instructions

1.  Open the `backend/.env` file.
2.  Replace `your_email@gmail.com` with your LinkedIn login email.
3.  Replace `your_password_here` with your LinkedIn password.

## 2. Security Recommendations

> [!WARNING]
> **Use a Burner Account:** LinkedIn has strict anti-scraping policies. We highly recommend using a "secondary" or "burner" account rather than your primary professional profile to avoid any risk of temporary restriction.

## 3. Handling Verification (MFA)

LinkedIn may occasionally trigger a **security challenge** (CAPTCHA or Email Code) when it detects a login from a new location or an automated driver.

- **Non-Headless Mode:** If the scraper consistently fails, you can temporarily change `headless=True` to `headless=False` in `backend/scrapers/linkedin_scraper.py`. This will open a visible browser window where you can manually solve the CAPTCHA or enter the code.
- **Session Persistence:** Once logged in once, LinkedIn typically trusts the "device" for a period, making future runs smoother.

## 4. Troubleshooting

- **Login Failed:** Double-check your email and password in the `.env` file.
- **Timed Out:** LinkedIn might be loading slowly or presenting a verification screen. Check the `logs/` folder for screenshots if the error persists.
- **Dependencies:** Ensure you have the latest Chrome browser installed. The `webdriver-manager` in our `requirements.txt` will handle the driver installation automatically.
