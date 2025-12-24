# 研究室配属管理システム（Lab Matching System）

## 概要
本プロジェクトは、大学等の研究室配属を効率的に管理・運用するためのWebバックエンドAPIです。ユーザ管理、学生・研究室管理、希望登録、マッチング、管理者機能などを提供します。

## 主な機能
- ユーザ登録・認証（JWT）
- 学生・研究室のCRUD
- 学生の希望登録・取得
- マッチング実行・履歴取得
- パスワードリセット
- 管理者向けバックアップ・リストア
- 学生CSV一括インポート
## 学生CSVインポートAPIの使い方

- エンドポイント: `/api/v1/admin/students/import`（POST, 管理者JWT必須）
- リクエスト: multipart/form-data, file（CSVファイル）
- CSVカラム仕様（全て必須）:
      - student_id: string/int
      - name: string
      - email: string
      - gpa: float
- 既存student_idはスキップしエラー返却、DBはリセットされません
- レスポンス例:
   ```json
   {
      "imported": 3,
      "errors": []
   }
   ```
- エラー例:
   - 全カラム必須です
   - gpaは数値で入力してください
   - student_idが既に存在します

## セットアップ手順
1. 必要なパッケージをインストール
   ```sh
   pip install -r requirements.txt
   ```
2. DB初期化・マイグレーション
   ```sh
   flask db upgrade
   ```
3. サーバ起動
   ```sh
   python app.py
   ```

## テスト実行
```sh
pytest -s
```

## API仕様
詳細は [API_SPEC.md](API_SPEC.md) を参照してください。

## 認証
- 管理者・一部APIはJWTトークンによる認証が必要です。
- ログインAPIで取得したトークンを `Authorization: Bearer <token>` ヘッダで送信してください。

## ディレクトリ構成例
```
├── app.py              # メインアプリケーション
├── API_SPEC.md         # API仕様書
├── requirements.txt    # 依存パッケージ
├── migrations/         # DBマイグレーション
├── tests/              # テストコード
└── ...
```

## ライセンス
MIT License

---

ご質問・要望はIssueまたはPull Requestでお知らせください。