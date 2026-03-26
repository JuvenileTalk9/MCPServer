# MCPサーバ

## 環境構築

```sh
cd mcp_server
uv init
uv add "mcp[cli]" httpx
```

## テストの実行

```sh
uv run mcp dev server.py
```

## Claude DesktopへのMCPサーバの登録

```json
{
  "mcpServers": {
    # 編集箇所ここから
    "local_mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "[server.pyがあるディレクトリのフルパス]",
        "python",
        "server.py"
      ]
    }
    # 編集箇所ここまで
  },
  "preferences": {
    "coworkScheduledTasksEnabled": false,
    "ccdScheduledTasksEnabled": false,
    "sidebarMode": "chat",
    "coworkWebSearchEnabled": true
  }
}
```
