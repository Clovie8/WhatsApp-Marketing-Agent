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
WAHA_BASE_URL = os.environ.get("WAHA_BASE_URL")

WA_API_URL = "https://stormlike-subbasal-alona.ngrok-free.dev/api/sendImage" 
CHANNEL_ID = "120363405654722379@newsletter" 

SITES_FILE = "sites.json"
MEMORY_FILE = "memory.json"

def get_page_content(url, selector):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        stealth_sync(page)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # --- NEW: CLOSE THE WHATSAPP POPUP ---
            try:
                # Target the exact class of your specific WhatsApp widget close button
                close_button = page.locator("button.wa-widget-close")
                close_button.first.click(timeout=5000)
                logging.info("🧹 Closed the WhatsApp community popup!")
                
                # Wait 1 second for the fade-out animation to finish so it isn't in the screenshot
                page.wait_for_timeout(1000) 
            except Exception:
                # If the popup isn't there, just ignore it and move on!
                pass
            # --------------------------------------
            
            page.wait_for_selector(selector, timeout=30000)
            elements = page.query_selector_all(selector)
            
            extracted_text = "\n".join([el.inner_text() for el in elements])
            
            if len(elements) > 0:
               elements[0].screenshot(path="movie.png")
               
            return extracted_text
        except Exception as e:
            logging.error(f"Failed to scrape {url}: {e}")
            return None
        finally:
            browser.close()

def generate_whatsapp_hype(old_text, new_text, content_type, watch_link):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # --- THE DYNAMIC PROMPT ---
        # --- THE DYNAMIC PROMPT ---
        prompt = f"""
        Act as the professional Social Media Manager for the streaming site TheOneMovies.com.

        I am giving you the OLD text and the NEW text of the {content_type} section of the website.
        Your job is to compare them, find ALL the completely NEW content that was just added, and write a WhatsApp broadcast announcing ONLY the new additions.

        RULES:
        1. Make the headline HUGE and clearly state if it is a "NEW {content_type.upper()} ADDED!"
        2. IMMEDIATELY after the headline, provide these two links exactly as shown:
        
        🌐 *Visit:* https://theonemovies.com
        👉 *Watch Recent {content_type}s:* {watch_link}
        
        3. For EACH new addition, format the details EXACTLY like this in a clean list (skip any info you cannot find):
        
        🎬 *Title:* (Name of the {content_type})
        📺 *Episode:* (ONLY if it is a Series, extract the Season and Episode badge, e.g., 'S1 : Ep2')
        🎭 *Genre:* (e.g., Action, Horror, Drama)
        📅 *Year:* (e.g., 2024)
        🎙️ *Umusobanuzi:* (The translator name next to the 🎙️ icon)
        
        4. End the message with a fun sign-off telling them to grab their popcorn and enjoy!, and of it below add this text:
           🚨 *Only On: TheOneMovies.com*
           
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
        return f"🚨 MASSIVE UPLOAD ALERT! 🚨\n\nNew {content_type}s just dropped! Head over to {watch_link} right now to see the latest uploads!"

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
        
        # --- THE SMART LOGIC ---
        # Detect if we are scraping Movies or Series based on the nth-of-type number
        if "nth-of-type(1)" in selector:
            content_type = "Movie"
            watch_link = "https://theonemovies.com/movies?sort=recent"
        else:
            content_type = "Series"
            watch_link = "https://theonemovies.com/series?sort=recent"

        memory_key = f"{url}_{selector}"

        content = get_page_content(url, selector)
        if not content:
            continue

        saved_text = memory.get(memory_key, "")

        if content != saved_text:
            logging.info(f"🚨 NEW {content_type.upper()} DETECTED! Waking AI...")
            
            # Pass the Type and the Link to Gemini so it customizes the message
            hype_message = generate_whatsapp_hype(saved_text, content, content_type, watch_link)
            
            send_whatsapp_broadcast(hype_message, "movie.png")
            
            memory[memory_key] = content
            memory_changed = True
        else:
            logging.info(f"zzz No new {content_type}s on {selector}.")

        time.sleep(10) # Cooldown timer

    if memory_changed:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=4)
        logging.info("Memory updated and saved.")

if __name__ == "__main__":
    main()
