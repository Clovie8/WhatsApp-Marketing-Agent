import os
import json
import time
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

# Whapi Configuration
WA_API_URL = "https://gate.whapi.cloud/messages/image" 
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
            
            # Grab all the text in the section
            extracted_text = "\n".join([el.inner_text() for el in elements])
            
            # Take a picture of the entire section so all new movies are visible!
            if len(elements) > 0:
               elements[0].screenshot(path="movie.png")
               
            return extracted_text
        except Exception as e:
            logging.error(f"Failed to scrape {url}: {e}")
            return None
        finally:
            browser.close()

def generate_whatsapp_hype(old_text, new_text):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        # --- THE NEW PROMPT ---
        prompt = f"""
        Act as the professional Social Media Manager for the streaming site TheOneMovies.com.

        I am going to give you the OLD text of the website, and the NEW text of the website.
        Your job is to compare them, find ALL the completely NEW movies or shows that were just added, and write a WhatsApp broadcast announcing ONLY the new content.

        For EACH new movie/show, you MUST extract and format these details in a clean list:
        🎬 *Title:* (Name of the movie/show)
        🎭 *Genre:* (e.g., Action, Horror)
        📅 *Year:* (e.g., 2026)
        🎙️ *Umusobanuzi:* (The translator name next to the 🎙️ icon. If not found, skip this line)

        Write a professional, exciting intro. Then list the new content with the details above. Use emojis!
        End the message telling them to watch it now on TheOneMovies.com.

        OLD WEBSITE TEXT:
        {old_text[:2500]}

        NEW WEBSITE TEXT:
        {new_text[:2500]}
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        logging.error(f"AI Brain failed: {e}")
        return "🚨 MASSIVE UPLOAD ALERT! 🚨\n\nNew content just dropped with fresh translations! Head over to TheOneMovies.com right now to see the latest uploads!"

def send_whatsapp_broadcast(message_text, image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        media_data = f"data:image/png;base64,{encoded_string}"
        
    headers = {
        "Authorization": f"Bearer {WA_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "to": CHANNEL_ID,
        "media": media_data,
        "caption": message_text
    }
    
    try:
        response = requests.post(WA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        logging.info("🚀 Image and text successfully sent to WhatsApp!")
    except Exception as e:
        logging.error(f"Failed to send image message: {e}")

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
        logging.info(f"Checking {selector} ...")

        # FIX: Create a unique memory key so Movies and Series don't overwrite each other!
        memory_key = f"{url}_{selector}"

        content = get_page_content(url, selector)
        if not content:
            continue

        saved_text = memory.get(memory_key, "")

        if content != saved_text:
            logging.info(f"🚨 NEW CONTENT DETECTED! Waking AI...")
            
            # Pass BOTH the old and new text to Gemini
            hype_message = generate_whatsapp_hype(saved_text, content)
            
            send_whatsapp_broadcast(hype_message, "movie.png")
            
            # Save the raw text to memory for next time
            memory[memory_key] = content
            memory_changed = True
        else:
            logging.info(f"zzz No new content on {selector}.")

        time.sleep(10) # Cooldown timer

    if memory_changed:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=4)
        logging.info("Memory updated and saved.")

if __name__ == "__main__":
    main()
