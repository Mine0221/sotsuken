import io
import csv
import json
import pytest

def get_admin_token(client):
    admin_data = {
        "email": "admin_import@example.com",
        "password": "adminpass",
        "role": "admin"
    }
    client.post("/api/v1/auth/register", data=json.dumps(admin_data), content_type="application/json")
    login_data = {
        "email": "admin_import@example.com",
        "password": "adminpass"
    }
    res = client.post("/api/v1/auth/login", data=json.dumps(login_data), content_type="application/json")
    return res.get_json()["access_token"]

def test_import_students_success(client):
    token = get_admin_token(client)
    csv_content = """student_id,name,email,gpa\n20250001,山田 太郎,yamada@example.com,3.5\n20250002,佐藤 花子,sato@example.com,3.8\n20250003,鈴木 次郎,suzuki@example.com,2.9\n"""
    data = {
        'file': (io.BytesIO(csv_content.encode('utf-8')), 'students.csv')
    }
    response = client.post(
        "/api/v1/admin/students/import",
        headers={"Authorization": f"Bearer {token}"},
        content_type='multipart/form-data',
        data=data
    )
    res_json = response.get_json()
    assert response.status_code == 200
    assert res_json["imported"] == 3
    assert res_json["errors"] == []

def test_import_students_error(client):
    token = get_admin_token(client)
    # gpaが空欄、student_id重複
    csv_content = """student_id,name,email,gpa\n20250001,山田 太郎,yamada@example.com,3.5\n20250001,佐藤 花子,sato@example.com,\n20250003,鈴木 次郎,suzuki@example.com,abc\n"""
    data = {
        'file': (io.BytesIO(csv_content.encode('utf-8')), 'students.csv')
    }
    response = client.post(
        "/api/v1/admin/students/import",
        headers={"Authorization": f"Bearer {token}"},
        content_type='multipart/form-data',
        data=data
    )
    res_json = response.get_json()
    assert response.status_code == 200
    assert res_json["imported"] == 1
    assert len(res_json["errors"]) == 2
    assert any("student_idが既に存在" in e["error"] for e in res_json["errors"])
    assert any("gpaは数値" in e["error"] or "全カラム必須" in e["error"] for e in res_json["errors"])
