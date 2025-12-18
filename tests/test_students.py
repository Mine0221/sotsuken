import json

def test_create_student_success(client):
    # 正常系: 学生新規登録
    data = {
        "student_id": "20250001",
        "name": "山田 太郎",
        "email": "yamada@example.com",
        "gpa": 3.6
    }
    response = client.post("/api/v1/students", data=json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    res_json = response.get_json()
    assert res_json["student_id"] == "20250001"
    assert "学生を登録しました" in res_json["message"]

def test_create_student_duplicate_id(client):
    # 異常系: student_id重複
    data = {
        "student_id": "20250001",
        "name": "山田 太郎",
        "email": "yamada@example.com"
    }
    client.post("/api/v1/students", data=json.dumps(data), content_type="application/json")
    response = client.post("/api/v1/students", data=json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    res_json = response.get_json()
    assert "student_idは既に存在します" in res_json["message"]

def test_create_student_missing_field(client):
    # 異常系: 必須項目不足
    data = {
        "student_id": "20250002",
        "name": "佐藤 次郎"
    }
    response = client.post("/api/v1/students", data=json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    res_json = response.get_json()
    assert "は必須です" in res_json["message"]
