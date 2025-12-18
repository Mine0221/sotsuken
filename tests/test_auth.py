import json

def test_login_success(client):
    # 事前に学生・ユーザ登録
    student_data = {
        "student_id": "20250020",
        "name": "鈴木 学生",
        "email": "suzuki@example.com"
    }
    client.post("/api/v1/students", data=json.dumps(student_data), content_type="application/json")
    user_data = {
        "email": "loginuser@example.com",
        "password": "testpass",
        "role": "student",
        "student_id": "20250020"
    }
    client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    # ログイン
    login_data = {
        "email": "loginuser@example.com",
        "password": "testpass"
    }
    response = client.post("/api/v1/auth/login", data=json.dumps(login_data), content_type="application/json")
    assert response.status_code == 200
    res_json = response.get_json()
    assert "access_token" in res_json
    assert res_json["role"] == "student"

def test_login_wrong_password(client):
    # 事前登録
    user_data = {
        "email": "wrongpass@example.com",
        "password": "rightpass",
        "role": "admin"
    }
    client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    # パスワード誤り
    login_data = {
        "email": "wrongpass@example.com",
        "password": "wrongpass"
    }
    response = client.post("/api/v1/auth/login", data=json.dumps(login_data), content_type="application/json")
    assert response.status_code == 401
    res_json = response.get_json()
    assert "認証に失敗" in res_json["message"]

def test_login_unregistered_email(client):
    # 未登録email
    login_data = {
        "email": "notfound@example.com",
        "password": "any"
    }
    response = client.post("/api/v1/auth/login", data=json.dumps(login_data), content_type="application/json")
    assert response.status_code == 401
    res_json = response.get_json()
    assert "認証に失敗" in res_json["message"]
