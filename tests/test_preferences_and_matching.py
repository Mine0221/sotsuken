import json
import pytest

def get_student_token(client, student_id="20251111", email="student_pref@example.com"):
    # 学生登録
    student_data = {
        "student_id": student_id,
        "name": "希望太郎",
        "email": email,
        "gpa": 3.2
    }
    client.post("/api/v1/students", data=json.dumps(student_data), content_type="application/json")
    user_data = {
        "email": email,
        "password": "pass",
        "role": "student",
        "student_id": student_id
    }
    client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    login_data = {
        "email": email,
        "password": "pass"
    }
    res = client.post("/api/v1/auth/login", data=json.dumps(login_data), content_type="application/json")
    return res.get_json()["access_token"]

def get_admin_token(client):
    admin_data = {
        "email": "admin_match@example.com",
        "password": "adminpass",
        "role": "admin"
    }
    client.post("/api/v1/auth/register", data=json.dumps(admin_data), content_type="application/json")
    login_data = {
        "email": "admin_match@example.com",
        "password": "adminpass"
    }
    res = client.post("/api/v1/auth/login", data=json.dumps(login_data), content_type="application/json")
    return res.get_json()["access_token"]

def test_set_preferences_success(client):
    token = get_student_token(client)
    # 研究室を2つ登録
    lab1 = {"lab_name": "ラボA", "teacher_name": "佐藤", "capacity": 5, "field_tag": "AI"}
    lab2 = {"lab_name": "ラボB", "teacher_name": "鈴木", "capacity": 5, "field_tag": "ロボ"}
    client.post("/api/v1/laboratories", data=json.dumps(lab1), content_type="application/json")
    client.post("/api/v1/laboratories", data=json.dumps(lab2), content_type="application/json")
    # 希望登録
    prefs = {
        "student_id": "20251111",
        "preferences": [
            {"lab_id": "LAB01", "rank": 1},
            {"lab_id": "LAB02", "rank": 2}
        ]
    }
    res = client.post(
        "/api/v1/preferences",
        data=json.dumps(prefs),
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert "希望を登録しました" in res.get_json()["message"]

def test_set_preferences_invalid(client):
    token = get_student_token(client, student_id="20251112", email="student_pref2@example.com")
    # 希望リストが空
    prefs = {"student_id": "20251112", "preferences": []}
    res = client.post(
        "/api/v1/preferences",
        data=json.dumps(prefs),
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200  # 空リストでもエラー返さない現仕様

def test_run_matching_success(client):
    # 事前に学生・研究室・希望データを登録
    student_id = "20252222"
    student_data = {
        "student_id": student_id,
        "name": "マッチ希望",
        "email": "match_student@example.com",
        "gpa": 3.0
    }
    client.post("/api/v1/students", data=json.dumps(student_data), content_type="application/json")
    user_data = {
        "email": "match_student@example.com",
        "password": "pass",
        "role": "student",
        "student_id": student_id
    }
    client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    # 研究室2つ
    lab1 = {"lab_name": "ラボC", "teacher_name": "田中", "capacity": 5, "field_tag": "AI"}
    lab2 = {"lab_name": "ラボD", "teacher_name": "高橋", "capacity": 5, "field_tag": "ロボ"}
    client.post("/api/v1/laboratories", data=json.dumps(lab1), content_type="application/json")
    client.post("/api/v1/laboratories", data=json.dumps(lab2), content_type="application/json")
    # 希望登録
    prefs = {
        "student_id": student_id,
        "preferences": [
            {"lab_id": "LAB01", "rank": 1},
            {"lab_id": "LAB02", "rank": 2}
        ]
    }
    client.post(
        "/api/v1/preferences",
        data=json.dumps(prefs),
        content_type="application/json"
    )
    # 管理者トークンでマッチング実行
    token = get_admin_token(client)
    res = client.post(
        "/api/v1/admin/matching/run",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert "マッチングを実行しました" in res.get_json()["message"]

def test_run_matching_forbidden(client):
    # 事前に学生・研究室・希望データを登録
    student_id = "20253333"
    student_data = {
        "student_id": student_id,
        "name": "マッチ権限テスト",
        "email": "match_forbid@example.com",
        "gpa": 2.8
    }
    client.post("/api/v1/students", data=json.dumps(student_data), content_type="application/json")
    user_data = {
        "email": "match_forbid@example.com",
        "password": "pass",
        "role": "student",
        "student_id": student_id
    }
    client.post("/api/v1/auth/register", data=json.dumps(user_data), content_type="application/json")
    # 研究室2つ
    lab1 = {"lab_name": "ラボE", "teacher_name": "山本", "capacity": 5, "field_tag": "AI"}
    lab2 = {"lab_name": "ラボF", "teacher_name": "中村", "capacity": 5, "field_tag": "ロボ"}
    client.post("/api/v1/laboratories", data=json.dumps(lab1), content_type="application/json")
    client.post("/api/v1/laboratories", data=json.dumps(lab2), content_type="application/json")
    # 希望登録
    prefs = {
        "student_id": student_id,
        "preferences": [
            {"lab_id": "LAB01", "rank": 1},
            {"lab_id": "LAB02", "rank": 2}
        ]
    }
    client.post(
        "/api/v1/preferences",
        data=json.dumps(prefs),
        content_type="application/json"
    )
    # 一般学生トークンでマッチング実行
    token = get_student_token(client, student_id=student_id, email="match_forbid@example.com")
    res = client.post(
        "/api/v1/admin/matching/run",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403
