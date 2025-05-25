import asyncio
import aiohttp
from bs4 import BeautifulSoup
import redis
import json

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"

class Storage:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    def save(self, book):
        key = f"books:{book['link']}"
        self.redis.set(key, json.dumps(book, ensure_ascii=False))
        self.redis.sadd("books:all", book['link'])

async def pobierz_opis_i_zdjecie(session, book_url):
    async with session.get(book_url) as response:
        if response.status != 200:
            return "", ""
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")

        opis_tag = soup.select_one("#product_description ~ p")
        opis = opis_tag.text.strip() if opis_tag else ""
        img_tag = soup.select_one(".item.active img")
        if img_tag:
            img_url = img_tag['src'].replace("../../", "https://books.toscrape.com/")
        else:
            img_url = ""
        return opis, img_url

async def pobierz_strone(session, url):
    async with session.get(url) as response:
        if response.status != 200:
            return []
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        books = []
        for article in soup.select(".product_pod"):
            tytul = article.h3.a["title"]
            cena = float(article.select_one(".price_color").text[2:].replace(",", "."))
            ocena = article.p["class"][1]  
            dostepnosc = "In stock" in article.select_one(".availability").text
            link = "https://books.toscrape.com/catalogue/" + article.h3.a["href"]
            opis, img_url = await pobierz_opis_i_zdjecie(session, link)
            book = {
                "tytul": tytul,
                "cena": cena,
                "ocena": ocena,
                "dostepnosc": dostepnosc,
                "link": link,
                "img_url": img_url,
                "opis": opis
            }
            books.append(book)
        return books

async def main():
    storage = Storage()
    all_books = []
    async with aiohttp.ClientSession() as session:
        tasks = [pobierz_strone(session, BASE_URL.format(i)) for i in range(1, 11)]
        results = await asyncio.gather(*tasks)
        for books in results:
            all_books.extend(books)
    for book in all_books:
        storage.save(book)
    print(f"Zapisano {len(all_books)} książek do Redis.")


if __name__ == "__main__":
    asyncio.run(main())
