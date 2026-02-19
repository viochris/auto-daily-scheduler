# 📅 Auto Daily Scheduler: Personal Calendar Assistant

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![Prefect](https://img.shields.io/badge/Prefect-Orchestration-070E28?logo=prefect&logoColor=white)
![Google Calendar](https://img.shields.io/badge/Google-Calendar-4285F4?logo=googlecalendar&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Delivery-26A5E4?logo=telegram&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📌 Overview
**Auto Daily Scheduler** is a fully automated assistant designed to keep you updated with your daily agenda and public holidays.

Orchestrated by **Prefect**, this bot acts as your personal time manager. It performs secure data retrieval using the **Google Calendar API**, processes your daily events into a clean, readable format, and instantly delivers the schedule to a **Telegram Chat**. It features robust error handling, secure credential management, and asynchronous delivery mechanisms.

## ✨ Key Features
### 📅 Calendar Integration
* **Multi-Calendar Fetching:** Aggregates events from your Primary calendar and the official Indonesian Holidays calendar simultaneously.
* **Smart Formatting:** Automatically parses complex ISO datetime strings, distinguishing between all-day occurrences and specific time-bound events.

### 🛡️ Robust Orchestration
* **Prefect Flows:** Wraps all logic in tasks with automatic **Retry Policies** (3 retries, 5s delay) to handle transient network or API glitches.
* **Asynchronous Delivery:** Uses `python-telegram-bot` and `asyncio` for non-blocking, lightning-fast message transmission.
* **Fail-Fast Logic:** Explicitly catches and categorizes exceptions (Authentication, Quota, Network) to ensure accurate pipeline monitoring.

## ⚠️ Current Limitations & Disclaimer
Please be aware of the following limitations in the current version:
1. **Authentication Setup:** Requires manual initial setup to generate the 'token.json' file via Google Cloud Console before the script can run autonomously.
2. **Token Expiration:** The system relies on a local `token.json` file for Google OAuth2 authentication. If the refresh token expires or is revoked, manual re-authentication is required.
3. **Fixed Timezone:** The time boundary extraction is currently hardcoded to fetch events using the `+07:00` (WIB/Jakarta) timezone offset.
4. **Event Types:** This script only fetches Calendar Events. It does not retrieve Google Tasks or automated Contact Birthdays due to API architectural differences.

## 🛠️ Tech Stack
* **Orchestrator:** Prefect (Workflow Management)
* **Language:** Python 3.11
* **Google Integration:** Google API Python Client (`google-api-python-client`)
* **Notification:** Python Telegram Bot (`python-telegram-bot`)

## 🚀 The Automation Pipeline
1.  **Trigger:** Scheduled run (Daily).
2.  **Extract:** Authenticates and queries the Google Calendar API for events happening between 00:00 and 23:59 of the current day.
3.  **Transform:** Cleans the raw JSON data, extracts hours/minutes, and formats the output into a readable string.
4.  **Deliver:** Pushes the formatted agenda to Telegram asynchronously via PTB.

## ⚙️ Configuration (Environment Variables)
Create a `.env` file in the root directory:

```ini
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_target_chat_id
```
*Note: You also need a valid `token.json` authorized for Google Calendar API in the root directory.*

## 📦 Local Installation
1. **Clone the Repository**
```bash
git clone https://github.com/viochris/auto-daily-scheduler.git
cd auto-daily-scheduler
```

2. **Install Dependencies**
```bash
pip install prefect python-dotenv google-api-python-client google-auth-httplib2 google-auth-oauthlib python-telegram-bot
```

3. **Run the Automation**
```bash
python scheduler_automation.py
```

### 🖥️ Expected Output
You should see **Prefect** orchestrating the tasks in real-time:
```text
07:00:01.123 | INFO    | Task run 'Get Today Schedules From Calendar' - Executing task...
07:00:03.456 | INFO    | Task run 'Get Today Schedules From Calendar' - ✅ Finished in state Completed
07:00:04.100 | INFO    | Task run 'To Telegram' - 🚀 Sending message via Python-Telegram-Bot...
07:00:05.200 | INFO    | Task run 'To Telegram' - ✅ Success: Message sent to Telegram (via PTB)!
07:00:05.300 | INFO    | Flow run 'Get Today's Schedules' - ✅ Workflow completed successfully.

```

## 🚀 Deployment Options

This bot supports two release methods depending on your infrastructure:

| Method | Description | Use Case |
| --- | --- | --- |
| **GitHub Actions** | **Serverless.** Uses `cron` scheduling in `.github/workflows/daily_schedule.yml`. Runs on GitHub servers for free. | Best for daily runs (Requires configuring `token.json` as a secret/base64). |
| **Local / VPS** | **Always On.** Uses `main_flow.serve()` to run as a background service on your own server or Docker container. | Best if you run it locally where `token.json` is easily managed. |

---

**Author:** [Silvio Christian, Joe](https://www.linkedin.com/in/silvio-christian-joe)
*'Automate the boring stuff, generate the beautiful stuff.'*
