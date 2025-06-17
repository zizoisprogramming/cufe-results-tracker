import smtplib
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
from telegram import Bot
import asyncio
from datetime import datetime


# Telegram configuration
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def log_results(message):
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = f"logs_{today}.txt"

    with open(log_file, 'a') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}]\n{message}\n\n")

async def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print("📱 Telegram message sent.")
    except Exception as e:
        print("❌ Failed to send Telegram message:", e)

def load_previous_results():
    if not os.path.exists('previous_results.txt'):
        return set()
    
    with open('previous_results.txt', 'r') as f:
        return set(line.strip() for line in f if line.strip())

def save_results(results):
    with open('previous_results.txt', 'w') as f:
        for result in sorted(results):
            f.write(f"{result}\n")
            print("write")

def check_results():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Use system ChromeDriver
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get("http://www.results.eng.cu.edu.eg/")
        time.sleep(5)  # Wait for page to load

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'class': 'listitem'})
        rows = table.find('tbody').find_all('tr')
        years = ["الفرقة الاولى", " الفرقة الثانية", "الفرقة الثالثة", "الفرقة الرابعة"]
        current_results = set()
        new_results = []
        first = True
        
        for row in rows:
            if first:
                first = False
                continue
            cols = row.find_all('td')
            if len(cols) < 5:
                continue
            department = cols[0].text.strip()
            for i, cell in enumerate(cols[1:]):
                if cell.find('a'):
                    result = f"{department} - {years[i]}"
                    current_results.add(result)
                    new_results.append(result)


        # Load previous results
        previous_results = load_previous_results()
        
        # Find new results
        new_updates = [result for result in new_results if result not in previous_results]
        
        log_results("logs".join(new_updates))
        if new_updates:
            if len(new_updates) == 1:
                message = "🎓 ظهرت النتيجة التالية\n" + "\n".join(new_updates)
            else:
                message = "🎓 ظهرت النتائج التالية\n" + "\n".join(new_updates)
            print("New updates found:")
            print(message)
            # Send message to Telegram
            asyncio.run(send_telegram_message(message))
            # Save all current results
            save_results(current_results)
        else:
            print("❌ No new updates found.")
            # Still save current results to maintain the latest state
            save_results(current_results)
    finally:
        driver.quit()

if __name__ == "__main__":
    check_results()
