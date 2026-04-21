import os
import httpx
from shared.logger import get_logger

logger = get_logger(__name__)


class BookClient:

    def __init__(self):
        self.book_api_base = os.getenv("BOOK_API_BASE")
        if not self.book_api_base:
            raise ValueError("BOOK_API_BASE が未設定です。")
        self.google_books_api_url = os.getenv("GOOGLE_BOOKS_API_URL")
        if not self.google_books_api_url:
            raise ValueError("GOOGLE_BOOKS_API_URL が未設定です。")

    async def read_books(
        self,
        title: str | None = None,
        author: str | None = None,
        publisher: str | None = None,
    ) -> str:
        """登録されている書籍を検索する

        タイトル・著者名・出版社名のいずれかを指定して検索することができます。
        複数の条件を指定した場合は、すべての条件に一致する書籍が検索されます。

        Args:
            title (str, optional): 書籍のタイトル. Defaults to None.
            author (str, optional): 書籍の著者名. Defaults to None.
            publisher (str, optional): 書籍の出版社名. Defaults to None.

        Returns:
            str: 検索結果のリスト
        """
        params = {}
        if title:
            params["title"] = title
        if author:
            params["author"] = author
        if publisher:
            params["publisher"] = publisher

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.book_api_base}/books/read",
                    params=params,
                )
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as e:
                logger.error(
                    "read_books HTTPエラー: %s %s",
                    e.response.status_code,
                    e.response.text,
                )
                if 400 <= e.response.status_code < 500:
                    return f"書籍管理サーバが停止している可能性があります。{e.response.status_code} {e.response.text}"
                raise

    async def add_book(self, title: str, author: str, publisher: str) -> str:
        """書籍を登録する

        タイトル・著者名・出版社名を指定して書籍を登録します。

        Args:
            title (str): 書籍のタイトル
            author (str): 書籍の著者名
            publisher (str): 書籍の出版社名

        Returns:
            str: 登録結果
        """
        data = {
            "title": title,
            "author": author,
            "publisher": publisher,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.book_api_base}/books/add", json=data
                )
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as e:
                logger.error(
                    "add_book HTTPエラー: %s %s",
                    e.response.status_code,
                    e.response.text,
                )
                if 400 <= e.response.status_code < 500:
                    return f"書籍管理サーバが停止している可能性があります。{e.response.status_code} {e.response.text}"
                raise

    async def search_books(self, keyword: str, max_results: int | None = 10) -> dict:
        """
        入力した文字列をもとに、Google Books APIからタイトル・著者・出版社を検索します。
        """
        max_results = max(1, min(max_results, 40))  # max_resultsは1以上40以下に制限
        params = {
            "q": keyword,
            "maxResults": max_results,
            "fields": "items(volumeInfo(title,authors,publisher))",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.google_books_api_url, params=params, timeout=10.0
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(
                    "search_books HTTPエラー: %s %s",
                    e.response.status_code,
                    e.response.text,
                )
                return {
                    "status_code": e.response.status_code,
                    "detail": "Google Books APIエラー",
                }
            except httpx.RequestError as e:
                logger.error("search_books 接続エラー: %s", e)
                return {
                    "status_code": 503,
                    "detail": "Google Books APIに接続できませんでした",
                }

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

        return {"query": keyword, "total": len(books), "books": books}
