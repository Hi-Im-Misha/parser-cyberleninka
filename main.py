import requests
from bs4 import BeautifulSoup
import threading
import queue

from pars import download_pdf  # Импортируем функцию загрузки PDF

q = queue.Queue()  # Очередь для передачи ссылок

def get_article_links(base_url):
    """Собирает ссылки на статьи и сразу отправляет их в очередь"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0 Safari/537.36"
    }

    page = 1
    while True:
        url = f"{base_url}/{page}" if page > 1 else base_url
        print(f'Проверяем страницу: {url}')
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Ошибка при загрузке страницы {url}. Останавливаем сбор.")
            break  

        soup = BeautifulSoup(response.text, "html.parser")
        list_container = soup.find("ul", class_="list")
        
        if not list_container or not list_container.find_all("li"):
            print(f"Страница {page} пуста. Останавливаем сбор.")
            break   

        for article in list_container.find_all("li"):
            link_tag = article.find("a")
            if link_tag and "href" in link_tag.attrs:
                article_url = "https://cyberleninka.ru" + link_tag["href"]
                q.put(article_url)  

        page += 1  


if __name__ == "__main__":
    # заменить на нужный раздел
    base_url = "https://cyberleninka.ru/article/c/basic-medicine"

    threading.Thread(target=get_article_links, args=(base_url,), daemon=True).start()

    threads = []
    for _ in range(5):  
        t = threading.Thread(target=lambda: download_pdf(q), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
