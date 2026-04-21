# MCPサーバ

## 環境構築

```sh
cd mcp_server
uv init
uv add "mcp[cli]" httpx
```

## テストの実行

```sh
uv run mcp dev main.py
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
        "main.py"
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

## VSCode+Claudeでのデバッグ実行

1. `Python デバッガー: MCPサーバ`をデバッグ実行
2. `ctrl`+`shift`+`p`から`MCP: Add server`を選択
3. `HTTP`を選択
4. MCPサーバのURL`http://127.0.0.1:8765/mcp`を入力
5. サーバIDが表示されるのでそのままEnter
6. `Workspace`を選択
7. `mcp.json`が作成される
8. `Claude Code`から新しいセッションを作成し、適当なプロンプトでツールを実行
