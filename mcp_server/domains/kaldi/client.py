from datetime import datetime, timezone, timedelta
import httpx
from bs4 import BeautifulSoup
from shared.logger import get_logger

logger = get_logger(__name__)


class KaldiClient:

    def __init__(self):
        pass

    async def fetch_sale_data(self, location_filter: str | None = None) -> str:
        url = self._get_url()
        html = await self._get_sale_html(url)
        sale_shop_info_list = self._parse_html(html, location_filter=location_filter)
        return self._format_response(sale_shop_info_list)

    def _get_url(self) -> str:
        now = datetime.now(timezone.utc) + timedelta(hours=9)
        return f"https://map.kaldi.co.jp/kaldi/articleList?account=kaldi&accmd=1&ftop=1&kkw001={now.year}-{now.month:02}-{now.day:02}T{now.hour:02}%3A{now.minute:02}%3A{now.second:02}"

    async def _get_sale_html(self, url: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as e:
                logger.error(
                    "HTTPエラー: %s %s", e.response.status_code, e.response.text
                )
                raise

    def _parse_html(self, html: str, location_filter: str | None = None) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        sale_shop_rows = [row for row in soup.find("tbody").find_all("tr")]
        sale_shop_info_list = [
            {
                "shop_name": sale_shop.select_one(".salename").get_text(strip=True),
                "shop_addr": sale_shop.select_one(".saleadress").get_text(strip=True),
                "sale_date": sale_shop.find(
                    class_=lambda x: x and "saledate" in x
                ).get_text(strip=True),
                "sale_state": sale_shop.find(
                    class_=lambda x: x and "saleicon" in x
                ).get_text(strip=True),
                "sale_detail": sale_shop.select_one(".saledetail").get_text(strip=True),
            }
            for sale_shop in sale_shop_rows
        ]
        if location_filter:
            sale_shop_info_list = [
                info
                for info in sale_shop_info_list
                if location_filter in info["shop_addr"]
            ]
        return sale_shop_info_list

    def _format_response(self, sale_shop_info_list: list[dict]) -> str:
        if not sale_shop_info_list:
            return "セール情報を取得できませんでした。"

        response = "カルディコーヒーファームのセール情報:\n"
        for info in sale_shop_info_list:
            response += (
                f"店舗名: {info['shop_name']}\n"
                f"店舗住所: {info['shop_addr']}\n"
                f"セール期間: {info['sale_date']}\n"
                f"セール状態: {info['sale_state']}\n"
                f"セール内容: {info['sale_detail']}\n"
                "-------------------------\n"
            )
        return response
