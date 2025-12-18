import json

def test_register_student_user_success(client):
    # 事前に学生を登録
    student_data = {
        "student_id": "20250010",
        "name": "田中 学生",
        "email": "tanaka@example.com"
    }
    client.post("/api/v1/students", data=json.dumps(student_data), content_type="application/json")
    # 学生ユーザ登録
    user_data = {
        "email": "studentuser@example.com",
        "password": "pass1234",
        "role": "student",
        "student_id": "20250010"
    }
    response = client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    assert response.status_code == 201
    res_json = response.get_json()
    assert "user_id" in res_json
    assert "ユーザを登録しました" in res_json["message"]

def test_register_admin_user_success(client):
    # 管理者ユーザ登録
    user_data = {
        "email": "admin@example.com",
        "password": "adminpass",
        "role": "admin"
    }
    response = client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    assert response.status_code == 201
    res_json = response.get_json()
    assert "user_id" in res_json
    assert "ユーザを登録しました" in res_json["message"]

def test_register_user_duplicate_email(client):
    # 同じemailで2回登録
    user_data = {
        "email": "dup@example.com",
        "password": "pass",
        "role": "admin"
    }
    client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    response = client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    assert response.status_code == 400
    res_json = response.get_json()
    assert "既に登録されています" in res_json["message"]

def test_register_student_user_missing_student_id(client):
    # studentロールでstudent_id未指定
    user_data = {
        "email": "nostudentid@example.com",
        "password": "pass",
        "role": "student"
    }
    response = client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    assert response.status_code == 400
    res_json = response.get_json()
    assert "student_idが必須" in res_json["message"]

def test_register_user_invalid_role(client):
    # 不正なrole
    user_data = {
        "email": "invalidrole@example.com",
        "password": "pass",
        "role": "hacker"
    }
    response = client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    assert response.status_code == 400
    res_json = response.get_json()
    assert "roleは" in res_json["message"]
