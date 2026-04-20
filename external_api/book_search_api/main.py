import httpx
from fastapi import FastAPI, HTTPException, Query
from typing import Optional

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

app = FastAPI(title="Book Internet Search API")


@app.get("/books/search")
async def search_books(
    q: str = Query(..., description="検索キーワード（タイトル・著者名など）"),
    max_results: Optional[int] = Query(
        10, ge=1, le=40, description="取得件数（最大40）"
    ),
):
    """
    入力した文字列をもとに、Google Books APIからタイトル・著者・出版社を検索します。
    """
    params = {
        "q": q,
        "maxResults": max_results,
        "fields": "items(volumeInfo(title,authors,publisher))",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                GOOGLE_BOOKS_API_URL, params=params, timeout=10.0
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail="Google Books APIエラー"
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=503, detail="Google Books APIに接続できませんでした"
            )

    data = response.json()
    items = data.get("items", [])

    books = []
    for item in items:
        info = item.get("volumeInfo", {})
        books.append(
            {
                "title": info.get("title", "不明"),
                "authors": info.get("authors", []),
                "publisher": info.get("publisher", "不明"),
            }
        )

    return {"query": q, "total": len(books), "books": books}
