from flask import Flask, render_template, request, url_for
import redis
import json
import os

app = Flask(__name__)

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

@app.route("/")
def index():
    query = request.args.get("q", "").lower()
    ocena = request.args.get("ocena", "")
    tylko_dostepne = request.args.get("dostepne", "") == "on"

    links = r.smembers("books:all")
    books = []
    for link in links:
        data = r.get(f"books:{link}")
        if data:
            book = json.loads(data)
            book_id = book['link'].split('/')[-2] + "/" + book['link'].split('/')[-1]
            book['book_id'] = book_id
            books.append(book)

    if query:
        books = [b for b in books if query in b['tytul'].lower()]
    if ocena:
        books = [b for b in books if b['ocena'] == ocena]

    if tylko_dostepne:
        books = [b for b in books if b['dostepnosc']]

    books = sorted(books, key=lambda x: x['tytul'])
    return render_template("index.html", books=books, q=query, ocena=ocena, tylko_dostepne=tylko_dostepne)

@app.route("/book/<path:book_id>")
def book(book_id):
    link = "https://books.toscrape.com/catalogue/" + book_id
    data = r.get(f"books:{link}")
    if data:
        book = json.loads(data)
        return render_template("book.html", book=book)
    else:
        return "Nie znaleziono książki", 404

if __name__ == "__main__":
    app.run(debug=True)
