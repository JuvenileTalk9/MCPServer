import sqlite3
from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel


DB_PATH = "books.db"


app = FastAPI()


class Book(BaseModel):
    title: str
    author: str
    publisher: str


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/books/search")
def read_books(
    title: Optional[str] = None,
    author: Optional[str] = None,
    publisher: Optional[str] = None,
):
    query = "SELECT * FROM books WHERE 1=1"
    params = []

    if title:
        query += " AND title LIKE ?"
        params.append(f"%{title}%")
    if author:
        query += " AND author LIKE ?"
        params.append(f"%{author}%")
    if publisher:
        query += " AND publisher LIKE ?"
        params.append(f"%{publisher}%")

    conn = get_db_connection()
    books = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(book) for book in books]


@app.post("/books/add")
def add_book(book: Book):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO books (title, author, publisher) VALUES (?, ?, ?)",
        (book.title, book.author, book.publisher),
    )
    conn.commit()
    conn.close()
    return {"message": "Book added successfully"}
