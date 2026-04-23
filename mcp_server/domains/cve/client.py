import os
from datetime import datetime, timezone, timedelta
import httpx
from shared.logger import get_logger

logger = get_logger(__name__)

NVD_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


class CVEClient:

    def __init__(self):
        self.api_key = os.getenv("NVD_API_KEY")
        self.base_url = NVD_BASE_URL

    def _build_headers(self) -> dict:
        if self.api_key:
            return {"apiKey": self.api_key}
        return {}

    async def fetch_cve_by_oss(
        self, oss_name: str, version: str | None = None, limit: int = 10
    ) -> str | None:
        """指定したOSSのCVE情報をNVDから取得する

        Args:
            oss_name (str): OSSの名前
            version (str | None): バージョン（省略時は全バージョン）
            limit (int): 最大取得件数

        Returns:
            str | None: 整形されたCVE情報、エラーの場合はNone
        """
        keyword = f"{oss_name} {version}" if version else oss_name
        params = {
            "keywordSearch": keyword,
            "resultsPerPage": min(limit, 20),
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers=self._build_headers(),
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                logger.info(
                    "fetch_cve_by_oss: keyword=%s, total=%s",
                    keyword,
                    data.get("totalResults"),
                )
                return self._format_cve_list(data, title=f"{keyword} の CVE情報")
            except httpx.HTTPStatusError as e:
                logger.error(
                    "fetch_cve_by_oss HTTPエラー: %s %s",
                    e.response.status_code,
                    e.response.text,
                )
                return None
            except Exception as e:
                logger.error("fetch_cve_by_oss 予期しないエラー: %s", e, exc_info=True)
                return None

    async def fetch_new_cves(self, days: int = 7, limit: int = 10) -> str | None:
        """直近N日間に公開されたCVE情報をNVDから取得する

        Args:
            days (int): 何日前までのCVEを取得するか
            limit (int): 最大取得件数

        Returns:
            str | None: 整形されたCVE情報、エラーの場合はNone
        """
        now = datetime.now(tz=timezone.utc)
        start = now - timedelta(days=days)
        params = {
            "pubStartDate": start.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "pubEndDate": now.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "resultsPerPage": min(limit, 20),
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers=self._build_headers(),
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                logger.info(
                    "fetch_new_cves: days=%s, total=%s", days, data.get("totalResults")
                )
                return self._format_cve_list(data, title=f"直近{days}日間の新着CVE情報")
            except httpx.HTTPStatusError as e:
                logger.error(
                    "fetch_new_cves HTTPエラー: %s %s",
                    e.response.status_code,
                    e.response.text,
                )
                return None
            except Exception as e:
                logger.error("fetch_new_cves 予期しないエラー: %s", e, exc_info=True)
                return None

    def _format_cve_list(self, data: dict, title: str) -> str:
        """CVEリストを人間が読みやすい形式に整形する

        Args:
            data (dict): NVD APIからのレスポンスデータ
            title (str): 出力のタイトル

        Returns:
            str: 整形されたCVE情報の文字列
        """
        total = data.get("totalResults", 0)
        vulnerabilities = data.get("vulnerabilities", [])

        if not vulnerabilities:
            return f"{title}\n\n該当するCVEは見つかりませんでした。"

        lines = [
            title,
            f"（全{total}件中 {len(vulnerabilities)}件を表示）",
            "",
        ]

        for item in vulnerabilities:
            cve = item.get("cve", {})
            cve_id = cve.get("id", "不明")
            published = cve.get("published", "")[:10]
            vuln_status = cve.get("vulnStatus", "不明")

            descriptions = cve.get("descriptions", [])
            description = next(
                (d["value"] for d in descriptions if d.get("lang") == "en"),
                "説明なし",
            )
            if len(description) > 200:
                description = description[:200] + "..."

            metrics = cve.get("metrics", {})
            score, severity = self._extract_cvss(metrics)

            lines.append(f"【{cve_id}】")
            lines.append(f"  公開日: {published} | ステータス: {vuln_status}")
            if score:
                lines.append(f"  深刻度: {severity} (CVSSスコア: {score})")
            lines.append(f"  概要: {description}")
            lines.append("")

        return "\n".join(lines).strip()

    def _extract_cvss(self, metrics: dict) -> tuple[str | None, str | None]:
        """CVSSスコアと深刻度を抽出する（v3.1 → v3.0 → v2.0 の優先順）

        Args:
            metrics (dict): CVEのmetricsフィールド

        Returns:
            tuple[str | None, str | None]: (スコア, 深刻度)
        """
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            entries = metrics.get(key, [])
            if entries:
                cvss_data = entries[0].get("cvssData", {})
                score = cvss_data.get("baseScore")
                severity = cvss_data.get("baseSeverity") or entries[0].get(
                    "baseSeverity"
                )
                if score:
                    return str(score), severity
        return None, None
