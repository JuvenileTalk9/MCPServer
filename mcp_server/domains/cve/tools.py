from mcp.server.fastmcp import FastMCP
from .client import CVEClient


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def get_cve_by_oss(
        oss_name: str,
        version: str | None = None,
        limit: int = 10,
        days: int | None = None,
    ) -> str | None:
        """指定したOSSに関連するCVE情報を取得する

        OSSの名前（およびバージョン）を入力として受け取り、NVD（National Vulnerability Database）から
        該当するCVE（Common Vulnerabilities and Exposures）情報を新しい順に返します。
        CVSSスコアや深刻度、脆弱性の概要を含む一覧を返します。

        Args:
            oss_name (str): CVEを検索するOSSの名前（例: "openssl", "log4j", "nginx"）
            version (str | None): バージョン（例: "3.0.0"）。省略時は全バージョンを対象に検索します。
            limit (int): 取得する最大件数（1〜20、デフォルト: 10）
            days (int | None): 指定した日数以内に公開されたCVEのみ取得（最大120日、例: 90）。省略時は全期間が対象。

        Returns:
            str | None: CVE情報の文字列。エラーの場合はNone。
        """
        client = CVEClient()
        return await client.fetch_cve_by_oss(
            oss_name=oss_name, version=version, limit=limit, days=days
        )

    @mcp.tool()
    async def get_new_cves(days: int = 7, limit: int = 10) -> str | None:
        """最近公開されたCVE情報を取得する

        指定した日数以内に公開されたCVE情報をNVD（National Vulnerability Database）から取得します。
        セキュリティ動向の定期的なモニタリングや最新の脅威把握に活用できます。

        Args:
            days (int): 何日前までに公開されたCVEを取得するか（デフォルト: 7）
            limit (int): 取得する最大件数（1〜20、デフォルト: 10）

        Returns:
            str | None: CVE情報の文字列。エラーの場合はNone。
        """
        client = CVEClient()
        return await client.fetch_new_cves(days=days, limit=limit)
