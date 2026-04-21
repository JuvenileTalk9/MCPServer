from mcp.server.fastmcp import FastMCP
from .client import WeatherClient


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def get_weather(city: str) -> str | None:
        """指定された都市の天気情報を取得する

        都市名を入力として受け取り、その都市の天気情報を文字列で返します。エラーが発生した場合はNoneを返します。
        都市名は英語を指定してください（例: "Tokyo", "New York", "London"）。

        Args:
            city (str): 天気情報を取得したい都市の名前（例: "Tokyo", "New York", "London"）

        Returns:
            str | None: 天気情報の文字列、エラーの場合はNone
        """
        client = WeatherClient()
        return await client.fetch_weather_data(city=city)
