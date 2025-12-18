import json

def test_request_password_reset_success(client):
    # 事前にユーザ登録
    student_data = {
        "student_id": "20250100",
        "name": "リセット太郎",
        "email": "reset@example.com"
    }
    client.post("/api/v1/students", data=json.dumps(student_data), content_type="application/json")
    user_data = {
        "email": "reset@example.com",
        "password": "resetpass",
        "role": "student",
        "student_id": "20250100"
    }
    client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    # パスワードリセットリクエスト
    req = {"email": "reset@example.com"}
    response = client.post("/api/v1/auth/request_password_reset", data=json.dumps(req), content_type="application/json")
    assert response.status_code == 200
    res_json = response.get_json()
    assert "reset_token" in res_json
    assert "発行しました" in res_json["message"]

def test_request_password_reset_not_found(client):
    # 未登録email
    req = {"email": "notfound@example.com"}
    response = client.post("/api/v1/auth/request_password_reset", data=json.dumps(req), content_type="application/json")
    assert response.status_code == 404
    res_json = response.get_json()
    assert "見つかりません" in res_json["message"]

def test_reset_password_success(client):
    # 事前にユーザ登録
    student_data = {
        "student_id": "20250101",
        "name": "リセット次郎",
        "email": "reset2@example.com"
    }
    client.post("/api/v1/students", data=json.dumps(student_data), content_type="application/json")
    user_data = {
        "email": "reset2@example.com",
        "password": "oldpass",
        "role": "student",
        "student_id": "20250101"
    }
    client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    # リセットトークン取得
    req = {"email": "reset2@example.com"}
    res = client.post("/api/v1/auth/request_password_reset", data=json.dumps(req), content_type="application/json")
    reset_token = res.get_json()["reset_token"]
    # パスワードリセット実行
    reset_req = {"reset_token": reset_token, "new_password": "newpass123"}
    response = client.post("/api/v1/auth/reset_password", data=json.dumps(reset_req), content_type="application/json")
    assert response.status_code == 200
    res_json = response.get_json()
    assert "リセットしました" in res_json["message"]

def test_reset_password_invalid_token(client):
    # 不正なトークン
    reset_req = {"reset_token": "invalidtoken", "new_password": "newpass"}
    response = client.post("/api/v1/auth/reset_password", data=json.dumps(reset_req), content_type="application/json")
    assert response.status_code == 401
    res_json = response.get_json()
    assert "トークンが不正" in res_json["message"]

def test_reset_password_missing_field(client):
    # 必須項目不足
    reset_req = {"reset_token": "", "new_password": ""}
    response = client.post("/api/v1/auth/reset_password", data=json.dumps(reset_req), content_type="application/json")
    assert response.status_code == 400
    res_json = response.get_json()
    assert "必須です" in res_json["message"]
