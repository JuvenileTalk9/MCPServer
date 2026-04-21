from mcp.server.fastmcp import FastMCP
from .client import WeatherClient


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def get_weather(city: str) -> str | None:
        """指定された都市の天気情報を取得する

        タイトル・著者名・出版社名のいずれかを指定して検索することができます。
        複数の条件を指定した場合は、すべての条件に一致する書籍が検索されます。

        Args:
            city (str): 天気情報を取得したい都市の名前

        Returns:
            str | None: 天気情報の文字列、エラーの場合はNone
        """
        client = WeatherClient()
        return await client.fetch_weather_data(city=city)
