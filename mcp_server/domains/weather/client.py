import os
from datetime import datetime, timezone, timedelta
import httpx
from shared.logger import get_logger

logger = get_logger(__name__)


class WeatherClient:

    def __init__(self):
        self.openweather_api_key = os.getenv("OpenWeather_API_KEY")
        if not self.openweather_api_key:
            raise ValueError("OpenWeather_API_KEY が未設定です。")
        self.openweather_base_url = os.getenv("OpenWeather_BASE_URL")
        if not self.openweather_base_url:
            raise ValueError("OpenWeather_BASE_URL が未設定です。")

    async def fetch_weather_data(self, city: str) -> str | None:
        """指定された都市の天気情報を取得する

        Args:
            city (str): 天気情報を取得したい都市の名前

        Returns:
            str: 天気情報の文字列、エラーの場合はNone
        """
        url = f"{self.openweather_base_url}/weather"
        params = {
            "q": city,
            "appid": self.openweather_api_key,
            "units": "metric",
            "lang": "ja",
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                return self._format_weather_response(response.json())
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.error("fetch_weather_data 都市未発見: city=%s", city)
                elif e.response.status_code == 401:
                    logger.error("fetch_weather_data APIキー無効: status=401")
                else:
                    logger.error(
                        "fetch_weather_data HTTPエラー: %s %s",
                        e.response.status_code,
                        e.response.text,
                    )
                return None
            except Exception as e:
                logger.error(
                    "fetch_weather_data 予期しないエラー: %s", e, exc_info=True
                )
                return None

    def _format_weather_response(self, data: dict) -> str:
        """OpenWeather APIのレスポンスを人間が読みやすい形式に整形する

        Args:
            data (dict): OpenWeather APIからのレスポンスデータ

        Returns:
            str: 整形された天気情報の文字列
        """
        if not data:
            return "天気情報を取得できませんでした。"

        logger.info("fetch_weather_data APIレスポンス: %s", data)

        # ロケーション情報
        city = data.get("name", "不明な都市")
        country = data.get("sys", {}).get("country", "不明な国")

        # 天気雨情報
        weather = data.get("weather", [{}])[0]
        weather_description = weather.get("description", "不明な天気")

        # 温度情報
        main = data.get("main", {})
        temp = main.get("temp", 0)
        feeds_like = main.get("feels_like", 0)
        temp_min = main.get("temp_min", 0)
        temp_max = main.get("temp_max", 0)
        humidity = main.get("humidity", 0)
        pressure = main.get("pressure", 0)

        # 風情報
        wind = data.get("wind", {})
        wind_speed = wind.get("speed", 0)
        wind_deg = wind.get("deg", 0)

        # 風向きを方位に変換
        wind_direction = self._convert_degrees_to_direction(wind_deg)

        # 日の出・日の入り情報
        sys_data = data.get("sys", {})
        timezone_offset = data.get("timezone", 0)
        tz = timezone(timedelta(seconds=timezone_offset))
        sunrise_ts = sys_data.get("sunrise")
        sunset_ts = sys_data.get("sunset")
        sunrise = (
            datetime.fromtimestamp(sunrise_ts, tz=tz).strftime("%H:%M")
            if sunrise_ts
            else "不明"
        )
        sunset = (
            datetime.fromtimestamp(sunset_ts, tz=tz).strftime("%H:%M")
            if sunset_ts
            else "不明"
        )

        # フォーマットされた回答を生成
        response = f"""
{city} ({country}) の現在の天気

天候: {weather_description}
現在の気温 : {temp}°C (体感温度: {feeds_like}°C)
最低気温: {temp_min}°C, 最高気温: {temp_max}°C
湿度: {humidity}%
気圧: {pressure} hPa
風速: {wind_speed} m/s, 風向き: {wind_direction}
日の出: {sunrise}, 日の入り: {sunset}
"""
        return response.strip()

    def _convert_degrees_to_direction(self, degrees: float) -> str:
        """風向きを度から方位に変換する

        Args:
            degrees (float): 風向きの度数

        Returns:
            str: 風向きの方位
        """
        directions = [
            "北",
            "北北東",
            "北東",
            "東北東",
            "東",
            "東南東",
            "南東",
            "南南東",
            "南",
            "南南西",
            "南西",
            "西南西",
            "西",
            "西北西",
            "北西",
            "北北西",
        ]
        index = round(degrees / 22.5) % 16
        return directions[index]
