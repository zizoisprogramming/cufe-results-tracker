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
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:    

        driver.get("http://www.results.eng.cu.edu.eg/")
        time.sleep(15)

        print(driver.title)
        print(driver.page_source)

        if "cannot be displayed" not in driver.title.lower():
            return

        
        print("fetching")
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        table = soup.find('table', {'class': 'listitem'})

        if not table:
            return
        rows = table.find('tbody').find_all('tr')
        if not rows:
            return
        years = ["الفرقة الاولى", "الفرقة الثانية", "الفرقة الثالثة", "الفرقة الرابعة"]
        edady_years = ["المجموعة الاولى", "المجموعة الثانية"]
        current_results = set()
        appeared_results = 0
        total_results = 0
        empty_cells = 0

        for row in rows[1:]:
            print("hello3")
            cols = row.find_all('td')
            if len(cols) == 3:
                department = cols[0].text.strip()
                for i, cell in enumerate(cols[1:]):
                    total_results += 1
                    if cell.get('class') != None and cell.get('class') == ['emptyCells']:
                        empty_cells += 1
                        
                    if cell.find('a'):
                        result = f"{department} - {edady_years[i]}"
                        current_results.add(result.strip())
                        appeared_results += 1
            else:
                department = cols[0].text.strip()
                for i, cell in enumerate(cols[1:]):
                    total_results += 1
                    if cell.get('class') != None and cell.get('class') == ['emptyCells']:
                        empty_cells += 1

                    if cell.find('a'):
                        result = f"{department} - {years[i]}"
                        current_results.add(result.strip())
                        appeared_results += 1
            print(appeared_results)

        previous_results = load_previous_results()
        message = ''
        print(previous_results)
        
        if len(current_results) < len(previous_results):
            time.sleep(60 * 10)
            previous_results = set()

        new_updates = current_results - previous_results

        log_results("\n".join(new_updates))

        if new_updates:
            if len(new_updates) == 1:
                message = "🎓 ظهرت النتيجة التالية\n" + "\n".join(new_updates)
            else:
                message = "🎓 ظهرت النتائج التالية\n" + "\n".join(new_updates)

            message += "\n📎 للاطلاع على النتيجة\nhttps://std.eng.cu.edu.eg/"
            print("New updates found:")
            print(message)
            asyncio.run(send_telegram_message(message))
        else:
            print("❌ No new updates found.")

        save_results(current_results)

        if appeared_results == total_results - empty_cells:
            print("🎉 All results have appeared.")

    finally:
        driver.quit()

if __name__ == "__main__":
    check_results()
