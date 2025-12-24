import json

def get_admin_token(client):
    # 管理者ユーザ登録＆ログイン
    admin_data = {
        "email": "admin_del@example.com",
        "password": "adminpass",
        "role": "admin"
    }
    client.post("/api/v1/auth/register", data=json.dumps(admin_data), content_type="application/json")
    login_data = {
        "email": "admin_del@example.com",
        "password": "adminpass"
    }
    res = client.post("/api/v1/auth/login", data=json.dumps(login_data), content_type="application/json")
    return res.get_json()["access_token"]

def test_delete_user_success(client):
    # 事前にユーザ登録
    user_data = {
        "email": "delete_me@example.com",
        "password": "pass",
        "role": "admin"
    }
    res = client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    user_id = res.get_json()["user_id"]
    token = get_admin_token(client)
    # ユーザ削除
    response = client.delete(f"/api/v1/admin/users/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    res_json = response.get_json()
    assert "削除しました" in res_json["message"]

def test_delete_user_not_found(client):
    token = get_admin_token(client)
    response = client.delete("/api/v1/admin/users/9999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    res_json = response.get_json()
    assert "見つかりません" in res_json["message"]

def test_delete_user_forbidden(client):
    # 管理者以外は削除不可
    # 一般ユーザ登録＆ログイン
    student_data = {
        "student_id": "20259999",
        "name": "一般ユーザ",
        "email": "student_del@example.com"
    }
    client.post("/api/v1/students", data=json.dumps(student_data), content_type="application/json")
    user_data = {
        "email": "student_del@example.com",
        "password": "pass",
        "role": "student",
        "student_id": "20259999"
    }
    res = client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    user_id = res.get_json()["user_id"]
    login_data = {
        "email": "student_del@example.com",
        "password": "pass"
    }
    res = client.post("/api/v1/auth/login", data=json.dumps(login_data), content_type="application/json")
    token = res.get_json()["access_token"]
    # 削除リクエスト（管理者権限なし）
    response = client.delete(f"/api/v1/admin/users/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    res_json = response.get_json()
    assert "権限がありません" in res_json["message"]
