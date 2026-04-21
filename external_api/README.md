# 外部API

## 環境構築

```sh
cd external_api
uv init
uv add fastapi httpx uvicorn python-dotenv
```

## 書籍管理API（book_api）

ローカルデータベースで書籍のタイトル・著者・出版社をデータとして持つレコードを管理する。

### データベースの初期化

```sh
cd external_api/book_api
sqlite3 books.db < init_db.sql
```

### 起動方法

```sh
uv run uvicorn main:app --reload
```

※補足

- `main`は`main.py`を実行することを指定している
- `app`は`main.py`で`FastAPI`を`app`というインスタンスで作成していることを指定している
- `--reload`はソースコードが変更されたときにサーバを自動的にリロードすることを指定している

### アクセス例

#### Get

```curl
curl http://127.0.0.1:8000/books/read
```

#### POST

WindowsのコマンドプロンプトやPower Shellではエラーが発生するため、Linux環境で実行するか、Git Bashなどを使用すること。

```curl
curl -X POST -H "Content-Type: application/json" -d '{"title": "abcde", "author": "xzy", "publisher": "テスト文庫"}' http://127.0.0.1:8000/books/add
```
