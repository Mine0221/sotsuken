# API仕様書（自動生成）

## 概要
本APIは研究室配属管理システムのバックエンドとして、ユーザ・学生・研究室・マッチング等の管理機能を提供します。

---

## エンドポイント一覧

### ユーザ認証・管理

#### ユーザ登録
- **POST** `/api/v1/auth/register`
- 認証: 不要
- リクエスト: email, password, role, student_id（studentの場合）
- レスポンス: user_id, message

#### ログイン
- **POST** `/api/v1/auth/login`
- 認証: 不要
- リクエスト: email, password
- レスポンス: access_token, role

#### ユーザ削除（管理者のみ）
- **DELETE** `/api/v1/admin/users/<user_id>`
- 認証: JWT（admin）
- レスポンス: message

---

### 学生管理

#### 学生一覧取得
- **GET** `/api/v1/students`
- 認証: 不要
- クエリ: page, per_page
- レスポンス: students[]

#### 学生登録
- **POST** `/api/v1/students`
- 認証: 不要
- リクエスト: student_id, name, email, gpa
- レスポンス: student_id, message

#### 学生詳細取得
- **GET** `/api/v1/students/<student_id>`
- 認証: 不要
- レスポンス: student情報

#### 学生更新
- **PUT/PATCH** `/api/v1/students/<student_id>`
- 認証: 不要
- リクエスト: name, email, gpa, assigned_lab
- レスポンス: student_id, message

#### 学生削除
- **DELETE** `/api/v1/students/<student_id>`
- 認証: 不要
- レスポンス: message

---

### 研究室管理

#### 研究室一覧取得
- **GET** `/api/v1/laboratories`
- 認証: 不要
- クエリ: page, per_page, field_tag
- レスポンス: labs[]

#### 研究室登録
- **POST** `/api/v1/laboratories`
- 認証: 不要
- リクエスト: lab_name, teacher_name, capacity, field_tag
- レスポンス: lab_id, message

#### 研究室削除
- **DELETE** `/api/v1/laboratories/<lab_id>`
- 認証: 不要
- レスポンス: message

---

### パスワードリセット

#### リセットリクエスト
- **POST** `/api/v1/auth/request_password_reset`
- 認証: 不要
- リクエスト: email
- レスポンス: reset_token, message

#### パスワードリセット
- **POST** `/api/v1/auth/reset_password`
- 認証: 不要
- リクエスト: reset_token, new_password
- レスポンス: message

---

### マッチング

#### マッチング実行（管理者のみ）
- **POST** `/api/v1/admin/matching/run`
- 認証: JWT（admin）
- レスポンス: message, result_id

#### マッチング結果取得
- **GET** `/api/v1/matching/results`
- 認証: 不要
- レスポンス: results[]

---

### その他

#### バックアップ・リストア（管理者のみ）
- **GET** `/api/v1/admin/backup`
- **POST** `/api/v1/admin/restore`
- 認証: JWT（admin）
- レスポンス: message


#### 学生CSVインポート（管理者のみ）
- **POST** `/api/v1/admin/students/import`
- 認証: JWT（admin）
- リクエスト: multipart/form-data, file（CSVファイル）
- CSVカラム仕様（全て必須）:
	- student_id: string/int
	- name: string
	- email: string
	- gpa: float
- 動作:
	- 既存student_idはスキップしエラー返却、DBはリセットされない
	- 新規student_idのみ追加
- レスポンス:
	- imported: 登録成功件数
	- errors: [{row, error}]（例: {"row": 3, "error": "student_idが既に存在します"}）
- エラー例:
	- 全カラム必須です
	- gpaは数値で入力してください
	- student_idが既に存在します

---

## 備考
- 認証が必要なAPIはJWTトークンをAuthorizationヘッダで送信してください。
- エラー時はJSONでerror, messageを返します。
- 詳細なリクエスト・レスポンス例やパラメータ仕様は必要に応じて追記してください。
