import requests
from bs4 import BeautifulSoup
import os
import queue
import time
import random

SAVE_PATH = 'article'

def download_pdf(q):
    while True:
        url = q.get()
        if url is None:
            break  

        print(f"Начинаем обработку: {url}")

        headers = {
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.101 Mobile Safari/537.36"
            ])
        }

        for attempt in range(5): 
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                break  
            except requests.exceptions.HTTPError as e:
                if response.status_code == 503:
                    wait_time = random.uniform(5, 15) 
                    print(f"Сервер временно недоступен (503). Повтор через {wait_time:.1f} сек.")
                    time.sleep(wait_time)
                else:
                    print(f"Ошибка при загрузке {url}: {e}")
                    q.task_done()
                    return
            except requests.exceptions.RequestException as e:
                print(f"Ошибка сети: {e}")
                q.task_done()
                return
        else:
            print(f"Не удалось загрузить {url} после 5 попыток.")
            q.task_done()
            return

        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("i", itemprop="headline")
        title = title_tag.get_text(strip=True) if title_tag else "Без_названия"
        title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)

        article_div = soup.find("div", class_="ocr", itemprop="articleBody")
        paragraphs = article_div.find_all("p") if article_div else []
        text = "\n".join(p.get_text(strip=True) for p in paragraphs)

        os.makedirs(SAVE_PATH, exist_ok=True)

        text_file_path = os.path.join(SAVE_PATH, f"{title}.txt")
        with open(text_file_path, "w", encoding="utf-8") as file:
            file.write(text)

        pdf_meta = soup.find("meta", {"name": "citation_pdf_url"})
        if not pdf_meta:
            print(f"PDF не найден для {url}")
            q.task_done()
            return

        pdf_url = pdf_meta["content"]

        for attempt in range(5):  
            try:
                pdf_response = requests.get(pdf_url, headers=headers, timeout=10)
                pdf_response.raise_for_status()
                break
            except requests.exceptions.HTTPError as e:
                if pdf_response.status_code == 503:
                    wait_time = random.uniform(5, 15)
                    print(f"PDF временно недоступен (503). Повтор через {wait_time:.1f} сек.")
                    time.sleep(wait_time)
                else:
                    print(f"Ошибка при скачивании PDF {pdf_url}: {e}")
                    q.task_done()
                    return
            except requests.exceptions.RequestException as e:
                print(f"Ошибка сети при скачивании PDF: {e}")
                q.task_done()
                return
        else:
            print(f"Не удалось скачать PDF {pdf_url} после 5 попыток.")
            q.task_done()
            return

        pdf_file_path = os.path.join(SAVE_PATH, f"{title}.pdf")
        with open(pdf_file_path, "wb") as file:
            file.write(pdf_response.content)

        print(f"Файл сохранен: {pdf_file_path}")

        time.sleep(random.uniform(2, 5))

        q.task_done()
