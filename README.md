[![Website Watcher](https://github.com/Clovie8/WhatsApp-Marketing-Agent/actions/workflows/whatsapp_watcher.yml/badge.svg)](https://github.com/Clovie8/WhatsApp-Marketing-Agent/actions/workflows/whatsapp_watcher.yml)

# WhatsApp-Marketing-Agent
A headless Playwright scraper and AI social media manager. It uses Gemini 2.5 Flash to detect new website content and automatically pushes engaging updates to a WhatsApp Channel via GitHub Actions.

# 🚀 AI-Powered WhatsApp Marketing Agent

An autonomous, serverless Python bot that monitors [TheOneMovies.com](https://theonemovies.com) for new uploads, generates hype-driven marketing copy using Google Gemini 2.5 Flash, and automatically broadcasts formatted updates (with screenshots!) to a WhatsApp Channel via Whapi.Cloud.

Built to run entirely in the background using GitHub Actions cron jobs.

---

## ✨ Key Features
* **Headless Web Scraping:** Uses `Playwright` and `playwright-stealth` to bypass bot protection, wait for elements to load, and automatically close intrusive UI popups before capturing data.
* **Visual Proof (Screenshots):** Automatically captures a clean screenshot of the newly added movie or series grid to send as the WhatsApp message header.
* **Smart Content Diffing:** Maintains a dynamic `memory.json` state to compare "Old" vs "New" website text, ensuring the bot *only* alerts users about brand-new uploads.
* **AI Formatting (Gemini 2.5 Flash):** Feeds the scraped text to Google's Gemini AI to intelligently extract key details (Title, Season/Episode, and Translator/Umusobanuzi) and format them into a highly engaging, emoji-filled WhatsApp broadcast.
* **Dynamic Routing:** Automatically detects if the new content is a Movie or a Series and adjusts the broadcast wording and watch links accordingly.
* **Zero-Downtime Architecture:** Leverages GitHub Actions for cron scheduling and Whapi.Cloud for the WhatsApp gateway, completely eliminating the need for paid VPS hosting or sleeping Render servers.

---

## 🏗️ System Architecture Flow
1. **Trigger:** GitHub Actions wakes up the bot every 30 minutes (`*/30 * * * *`).
2. **Scrape & Snap:** Playwright opens a hidden browser, visits the Movies and Series sections, closes any popups, reads the text, and takes a screenshot (`movie.png`).
3. **Analyze:** The bot checks the scraped text against `memory.json`. If it's identical, it goes back to sleep.
4. **Generate:** If new content is detected, the old and new text are sent to Gemini to write the marketing copy.
5. **Broadcast:** The AI text and the `movie.png` screenshot are bundled into a Base64 payload and POSTed to the Whapi.Cloud API.
6. **Update:** The new website state is saved to `memory.json` for the next cycle.

---

## ⚙️ Configuration Files

### `sites.json`
Tells the bot exactly which HTML sections to target. We use CSS pseudo-classes to separate the Movies section from the Series section:
```json
[
  {
    "url": "[https://www.theonemovies.com/](https://www.theonemovies.com/)",
    "selector": "section.media-section:nth-of-type(1)"
  },
  {
    "url": "[https://www.theonemovies.com/](https://www.theonemovies.com/)",
    "selector": "section.media-section:nth-of-type(2)"
  }
]
```
```memory.json```

The bot's brain. It stores the raw text of the most recent successful scrape.
(Note: If resetting the bot, this file must contain an empty JSON object {}).

---

## 🚀 Setup & Deployment Instructions
### 1. Prerequisites
* A **Google AI Studio** account for the Gemini API Key.
* A Whapi.Cloud account linked to your WhatsApp phone number to get the API Token.
* The hidden ID of your target WhatsApp Channel (looks like ```120363xxxxxxxxxxxx@newsletter```).

### 2. GitHub Secrets
To run this securely, you must add the following API keys to your GitHub repository via **Settings > Secrets and variables > Actions:**
* ```GEMINI_API_KEY:``` Your Google Gemini key.
* ```WA_API_TOKEN:``` Your Whapi.Cloud Bearer token.

### 3. Environment Specs (Crucial)
To ensure Playwright and its stealth dependencies run correctly on GitHub's free tier, the ```.github/workflows/whatsapp_watcher.yml``` must be locked to specific environments:
* **OS:** ```ubuntu-22.04``` (Fixes missing ```libasound2``` dependencies in newer Ubuntu builds).

* **Python:** ```3.10``` (Fixes missing ```pkg_resources``` in Python 3.12+).

## 🛠️ Built With
* Python 3.10
* Playwright - Headless browser automation
* Google GenAI SDK - For Gemini 2.5 Flash text generation
* Whapi.Cloud - WhatsApp API Gateway
* GitHub Actions - CI/CD and Cron scheduling
