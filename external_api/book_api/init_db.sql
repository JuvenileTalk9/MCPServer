DROP TABLE IF EXISTS books;

CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    publisher VARCHAR(255) NOT NULL
);

INSERT INTO
    books (title, author, publisher)
VALUES (
        'もういちどベートーヴェン',
        '中山 七里',
        '宝島社文庫'
    ),
    (
        '汚れた赤を恋と呼ぶんだ',
        '河野 裕',
        '新潮文庫nex'
    ),
    (
        'MCPサーバー開発大全',
        '岡 翔子',
        '技術評論社'
    );