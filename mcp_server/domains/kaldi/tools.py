from mcp.server.fastmcp import FastMCP
from .client import KaldiClient


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def get_kaldi_sale_info(location_filter: str | None = None) -> str | None:
        """カルディコーヒーファームのセール情報を取得する

        現時点のセール情報を取得し、店舗ごとにセール内容をまとめた文字列を返します。
        location_filterが指定された場合、店舗の住所にlocation_filterで指定した文字列が含まれる場合のみ、その店舗の情報を返します。
        エラーが発生した場合はNoneを返します。

        Args:
            location_filter (str | None): 店舗の住所に含める文字列

        Returns:
            str | None: セール情報の文字列、エラーの場合はNone
        """
        client = KaldiClient()
        return await client.fetch_sale_data(location_filter=location_filter)
