import asyncio
import os
from datetime import datetime, timezone, timedelta
import httpx
from shared.logger import get_logger

logger = get_logger(__name__)

NVD_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NVD_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.000+00:00"
NVD_MAX_DATE_RANGE_DAYS = 120
NVD_RATE_LIMIT_SLEEP = 6  # NVD推奨: リクエスト間隔6秒以上


class CVEClient:

    def __init__(self):
        self.api_key = os.getenv("NVD_API_KEY")
        self.base_url = NVD_BASE_URL

    def _build_headers(self) -> dict:
        if self.api_key:
            return {"apiKey": self.api_key}
        return {}

    def _build_date_params(self, start: datetime, end: datetime) -> dict:
        return {
            "pubStartDate": start.strftime(NVD_DATETIME_FORMAT),
            "pubEndDate": end.strftime(NVD_DATETIME_FORMAT),
        }

    async def _fetch_one_chunk(self, params: dict) -> tuple[list, int] | str:
        """1チャンク分のAPIリクエストを実行する。

        Returns:
            tuple[list, int]: (vulnerabilities, totalResults) — 成功時
            str: レート制限エラーメッセージ — 429発生時
        """
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
                return data.get("vulnerabilities", []), data.get("totalResults", 0)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    retry_after = e.response.headers.get("Retry-After", "しばらく")
                    logger.error("_fetch_one_chunk レート制限: Retry-After=%s", retry_after)
                    return f"NVD APIのレート制限に達しました。{retry_after}秒後に再試行してください。"
                logger.error(
                    "_fetch_one_chunk HTTPエラー: %s %s",
                    e.response.status_code,
                    e.response.text,
                )
                return [], 0
            except Exception as e:
                logger.error("_fetch_one_chunk 予期しないエラー: %s", e, exc_info=True)
                return [], 0

    async def fetch_cve_by_oss(
        self,
        oss_name: str,
        version: str | None = None,
        limit: int = 10,
        days: int | None = None,
    ) -> str | None:
        """指定したOSSのCVE情報をNVDから取得する

        daysが120日を超える場合は120日チャンクに分割して順次取得します。
        NVDのレート制限（APIキーなし: 5リクエスト/30秒）を考慮し、
        チャンク間に6秒のスリープを挟みます。

        Args:
            oss_name (str): OSSの名前
            version (str | None): バージョン（省略時は全バージョン）
            limit (int): 取得する最大件数（1〜20）
            days (int | None): 指定した日数以内のCVEを取得。120日超は分割取得。省略時は直近120日。

        Returns:
            str | None: CVE情報の文字列。エラーの場合はNone。
        """
        keyword = f"{oss_name} {version}" if version else oss_name
        days = days if days is not None else NVD_MAX_DATE_RANGE_DAYS

        try:
            now = datetime.now(tz=timezone.utc)
            overall_start = now - timedelta(days=days)

            # 新しい順にチャンクを生成（chunk_end → chunk_start の順で遡る）
            chunks: list[tuple[datetime, datetime]] = []
            chunk_end = now
            while chunk_end > overall_start:
                chunk_start = max(
                    chunk_end - timedelta(days=NVD_MAX_DATE_RANGE_DAYS),
                    overall_start,
                )
                chunks.append((chunk_start, chunk_end))
                chunk_end = chunk_start

            all_vulnerabilities: dict[str, dict] = {}  # CVE ID → item（重複排除）
            total = 0
            rate_limited = False

            for i, (chunk_start, chunk_end) in enumerate(chunks):
                if i > 0:
                    await asyncio.sleep(NVD_RATE_LIMIT_SLEEP)

                params = {
                    "keywordSearch": keyword,
                    "resultsPerPage": 20,  # チャンクごとに最大件数取得
                    **self._build_date_params(chunk_start, chunk_end),
                }
                result = await self._fetch_one_chunk(params)

                if isinstance(result, str):
                    # レート制限: 取得済み分があれば継続、なければそのまま返す
                    logger.error("チャンク%d/%d でレート制限発生", i + 1, len(chunks))
                    if not all_vulnerabilities:
                        return result
                    rate_limited = True
                    break

                chunk_vulns, chunk_total = result
                total += chunk_total
                logger.info(
                    "fetch_cve_by_oss chunk %d/%d: %s〜%s, 取得=%d件 / 全%d件",
                    i + 1, len(chunks),
                    chunk_start.strftime("%Y-%m-%d"),
                    chunk_end.strftime("%Y-%m-%d"),
                    len(chunk_vulns),
                    chunk_total,
                )
                for item in chunk_vulns:
                    cve_id = item.get("cve", {}).get("id")
                    if cve_id and cve_id not in all_vulnerabilities:
                        all_vulnerabilities[cve_id] = item

            vulnerabilities = list(all_vulnerabilities.values())
            title = f"{keyword} の CVE情報（直近{days}日間）"
            if rate_limited:
                title += " ※レート制限により途中までの結果です。しばらく待ってから再試行してください。"

            vulnerabilities = sorted(
                vulnerabilities,
                key=lambda x: x.get("cve", {}).get("published", ""),
                reverse=True,
            )[:limit]

            logger.info(
                "fetch_cve_by_oss: keyword=%s, days=%s, total=%s", keyword, days, total
            )
            return self._format_cve_list(vulnerabilities, total, title=title)

        except Exception as e:
            logger.error("fetch_cve_by_oss 予期しないエラー: %s", e, exc_info=True)
            return None

    async def fetch_new_cves(self, days: int = 7, limit: int = 10) -> str | None:
        """直近N日間に公開されたCVE情報をNVDから取得する

        Args:
            days (int): 何日前までのCVEを取得するか（最大120日）
            limit (int): 最大取得件数

        Returns:
            str | None: 整形されたCVE情報、エラーの場合はNone
        """
        actual_days = min(days, NVD_MAX_DATE_RANGE_DAYS)
        now = datetime.now(tz=timezone.utc)
        params = {
            **self._build_date_params(now - timedelta(days=actual_days), now),
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
                    "fetch_new_cves: days=%s, total=%s", actual_days, data.get("totalResults")
                )
                vulnerabilities = data.get("vulnerabilities", [])
                return self._format_cve_list(
                    vulnerabilities, data.get("totalResults", 0),
                    title=f"直近{actual_days}日間の新着CVE情報",
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    retry_after = e.response.headers.get("Retry-After", "しばらく")
                    logger.error("fetch_new_cves レート制限: Retry-After=%s", retry_after)
                    return f"NVD APIのレート制限に達しました。{retry_after}秒後に再試行してください。"
                logger.error(
                    "fetch_new_cves HTTPエラー: %s %s",
                    e.response.status_code,
                    e.response.text,
                )
                return None
            except Exception as e:
                logger.error("fetch_new_cves 予期しないエラー: %s", e, exc_info=True)
                return None

    def _format_cve_list(self, vulnerabilities: list, total: int, title: str) -> str:
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

            affected = self._extract_affected_versions(cve)

            lines.append(f"【{cve_id}】")
            lines.append(f"  公開日: {published} | ステータス: {vuln_status}")
            if score:
                lines.append(f"  深刻度: {severity} (CVSSスコア: {score})")
            lines.append(f"  概要: {description}")
            if affected:
                lines.append("  影響バージョン:")
                for v in affected:
                    lines.append(f"    - {v}")
            lines.append("")

        return "\n".join(lines).strip()

    async def fetch_cve_by_id(self, cve_id: str) -> str | None:
        """CVE IDを指定してCVEの詳細情報をNVDから取得する

        Args:
            cve_id (str): CVE ID（例: "CVE-2021-44228"）

        Returns:
            str | None: 整形されたCVE詳細情報、エラーの場合はNone
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.base_url,
                    params={"cveId": cve_id},
                    headers=self._build_headers(),
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                vulnerabilities = data.get("vulnerabilities", [])
                if not vulnerabilities:
                    return f"{cve_id} は見つかりませんでした。"
                cve = vulnerabilities[0].get("cve", {})
                logger.info("fetch_cve_by_id: cve_id=%s", cve_id)
                return self._format_cve_detail(cve)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    retry_after = e.response.headers.get("Retry-After", "しばらく")
                    logger.error("fetch_cve_by_id レート制限: Retry-After=%s", retry_after)
                    return f"NVD APIのレート制限に達しました。{retry_after}秒後に再試行してください。"
                logger.error(
                    "fetch_cve_by_id HTTPエラー: %s %s",
                    e.response.status_code,
                    e.response.text,
                )
                return None
            except Exception as e:
                logger.error("fetch_cve_by_id 予期しないエラー: %s", e, exc_info=True)
                return None

    def _format_cve_detail(self, cve: dict) -> str:
        cve_id = cve.get("id", "不明")
        published = cve.get("published", "")[:10]
        last_modified = cve.get("lastModified", "")[:10]
        vuln_status = cve.get("vulnStatus", "不明")

        descriptions = cve.get("descriptions", [])
        description = next(
            (d["value"] for d in descriptions if d.get("lang") == "en"),
            "説明なし",
        )

        score, severity = self._extract_cvss(cve.get("metrics", {}))

        affected = self._extract_affected_versions(cve)

        references = [
            ref.get("url", "")
            for ref in cve.get("references", [])
            if ref.get("url")
        ]

        lines = [
            f"【{cve_id}】",
            f"  公開日: {published} | 最終更新: {last_modified} | ステータス: {vuln_status}",
        ]
        if score:
            lines.append(f"  深刻度: {severity} (CVSSスコア: {score})")
        lines.append(f"  概要: {description}")
        if affected:
            lines.append("  影響バージョン:")
            for v in affected:
                lines.append(f"    - {v}")
        if references:
            lines.append("  参考URL:")
            for url in references[:5]:
                lines.append(f"    - {url}")
        return "\n".join(lines)

    def _extract_affected_versions(self, cve: dict) -> list[str] | None:
        configurations = cve.get("configurations")
        if not configurations:
            return None

        entries = []
        seen: set[str] = set()

        for config in configurations:
            for node in config.get("nodes", []):
                for match in node.get("cpeMatch", []):
                    if not match.get("vulnerable"):
                        continue

                    parts = match.get("criteria", "").split(":")
                    # cpe:2.3:<part>:<vendor>:<product>:<version>:...
                    vendor = parts[3] if len(parts) > 3 else ""
                    product = parts[4] if len(parts) > 4 else ""
                    version = parts[5] if len(parts) > 5 else ""

                    start_inc = match.get("versionStartIncluding")
                    start_exc = match.get("versionStartExcluding")
                    end_inc = match.get("versionEndIncluding")
                    end_exc = match.get("versionEndExcluding")

                    if any([start_inc, start_exc, end_inc, end_exc]):
                        range_parts = []
                        if start_inc:
                            range_parts.append(f">= {start_inc}")
                        elif start_exc:
                            range_parts.append(f"> {start_exc}")
                        if end_inc:
                            range_parts.append(f"<= {end_inc}")
                        elif end_exc:
                            range_parts.append(f"< {end_exc}")
                        label = f"{vendor}:{product} {', '.join(range_parts)}"
                    elif version and version != "*":
                        label = f"{vendor}:{product} {version}"
                    else:
                        label = f"{vendor}:{product}"

                    if label not in seen:
                        seen.add(label)
                        entries.append(label)

        return entries if entries else None

    def _extract_cvss(self, metrics: dict) -> tuple[str | None, str | None]:
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            entries = metrics.get(key, [])
            if entries:
                cvss_data = entries[0].get("cvssData", {})
                score = cvss_data.get("baseScore")
                severity = cvss_data.get("baseSeverity") or entries[0].get("baseSeverity")
                if score:
                    return str(score), severity
        return None, None
