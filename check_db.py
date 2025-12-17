import sqlite3

# instanceディレクトリ内のDBファイルを開く
conn = sqlite3.connect('instance/sotsuken.db')
cursor = conn.cursor()

# テーブル一覧を取得
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('テーブル一覧:', tables)

# 各テーブルのスキーマを表示
for table in tables:
    name = table[0]
    cursor.execute(f"PRAGMA table_info({name});")
    columns = cursor.fetchall()
    print(f'\n{name} のカラム:')
    for col in columns:
        print(col)

conn.close()
