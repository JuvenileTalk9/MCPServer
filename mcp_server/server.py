import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("書籍管理API")

# Contants
API_BASE = "http://127.0.0.1:8000"


@mcp.tool()
def search_books(
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

    response = httpx.get(f"{API_BASE}/books/search", params=params)
    return response.text


@mcp.tool()
def add_book(title: str, author: str, publisher: str) -> str:
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
    response = httpx.post(f"{API_BASE}/books/add", json=data)
    return response.text


if __name__ == "__main__":
    mcp.run(transport="stdio")
