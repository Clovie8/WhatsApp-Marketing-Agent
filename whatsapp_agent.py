import os
import json
import time
import hashlib
import logging
import requests
import base64
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from google import genai

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WA_API_TOKEN = os.environ.get("WA_API_TOKEN")

# Replace this with your API Gateway URL and Channel ID
WA_API_URL = "https://gate.whapi.cloud/messages/text" 
CHANNEL_ID = "120363405654722379@newsletter" 

SITES_FILE = "sites.json"
MEMORY_FILE = "memory.json"

def get_page_content(url, selector):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        stealth_sync(page)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector(selector, timeout=15000)
            elements = page.query_selector_all(selector)
            
            # Grab the top 3 newest items to give Gemini context
            extracted_text = "\n".join([el.inner_text() for el in elements[:3]])
            return extracted_text
        except Exception as e:
            logging.error(f"Failed to scrape {url}: {e}")
            return None
        finally:
            browser.close()

def generate_whatsapp_hype(raw_text):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"""
        Act as the hype Social Media Manager for the streaming site TheOneMovies.com.
        Based on this scraped website text, identify the VERY FIRST movie or TV show listed (this is the newest addition).
        
        Write a short, incredibly exciting WhatsApp channel broadcast announcing this new upload.
        - Use emojis! 🍿🔥🎬
        - Keep it punchy and easy to read on a phone.
        - End the message telling them to go watch it right now on TheOneMovies.com!

        Raw text:
        {raw_text[:1500]}
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        logging.error(f"AI Brain failed: {e}")
        return "🍿 New Content Alert! Head over to TheOneMovies.com right now to see the latest upload!"

def send_whatsapp_broadcast(message_text):
    headers = {
        "Authorization": f"Bearer {WA_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "to": CHANNEL_ID,
        "body": message_text
    }
    try:
        response = requests.post(WA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        logging.info("🚀 WhatsApp Channel updated successfully!")
    except Exception as e:
        logging.error(f"Failed to send WhatsApp message: {e}")

def main():
    with open(SITES_FILE, "r") as f:
        sites = json.load(f)

    memory = {}
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            memory = json.load(f)

    memory_changed = False

    for site in sites:
        url = site["url"]
        selector = site["selector"]
        logging.info(f"Checking {url} ...")

        content = get_page_content(url, selector)
        if not content:
            continue

        current_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        saved_hash = memory.get(url)

        if current_hash != saved_hash:
            logging.info(f"🚨 NEW MOVIE DETECTED on {url}! Waking AI...")
            
            # 1. Generate the Hype Message
            hype_message = generate_whatsapp_hype(content)
            
            # 2. Send to WhatsApp
            send_whatsapp_broadcast(hype_message)
            
            # 3. Update Memory
            memory[url] = current_hash
            memory_changed = True
        else:
            logging.info(f"zzz No new movies on {url}.")

        time.sleep(10) # Cooldown timer

    if memory_changed:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=4)
        logging.info("Memory updated and saved.")

if __name__ == "__main__":
    main()
