from mcp.server.fastmcp import FastMCP
from .client import BookClient


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def read_books(
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
        client = BookClient()
        return await client.read_books(title=title, author=author, publisher=publisher)

    @mcp.tool()
    async def add_book(title: str, author: str, publisher: str) -> str:
        """書籍を登録する

        タイトル・著者名・出版社名を指定して書籍を登録します。

        Args:
            title (str): 書籍のタイトル
            author (str): 書籍の著者名
            publisher (str): 書籍の出版社名

        Returns:
            str: 登録結果
        """
        client = BookClient()
        return await client.add_book(title=title, author=author, publisher=publisher)
