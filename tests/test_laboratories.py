import json

def test_create_laboratory_success(client):
    # 正常系: 研究室新規登録
    data = {
        "lab_name": "研究室C",
        "teacher_name": "高橋",
        "capacity": 5,
        "field_tag": "情報"
    }
    response = client.post("/api/v1/laboratories", data=json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    res_json = response.get_json()
    assert "lab_id" in res_json
    assert "研究室を登録しました" in res_json["message"]

def test_create_laboratory_duplicate_name(client):
    # 異常系: 研究室名重複
    data = {
        "lab_name": "研究室D",
        "teacher_name": "佐々木",
        "capacity": 8,
        "field_tag": "AI"
    }
    client.post("/api/v1/laboratories", data=json.dumps(data), content_type="application/json")
    response = client.post("/api/v1/laboratories", data=json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    res_json = response.get_json()
    assert "既に存在します" in res_json["message"]

def test_create_laboratory_missing_field(client):
    # 異常系: 必須項目不足
    data = {
        "lab_name": "研究室E",
        "teacher_name": "山本"
    }
    response = client.post("/api/v1/laboratories", data=json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    res_json = response.get_json()
    assert "は必須です" in res_json["message"]

def test_get_laboratories(client):
    # 研究室一覧取得
    data = {
        "lab_name": "研究室F",
        "teacher_name": "井上",
        "capacity": 6,
        "field_tag": "ロボティクス"
    }
    client.post("/api/v1/laboratories", data=json.dumps(data), content_type="application/json")
    response = client.get("/api/v1/laboratories")
    assert response.status_code == 200
    res_json = response.get_json()
    assert "labs" in res_json
    assert any(lab["lab_name"] == "研究室F" for lab in res_json["labs"])

def test_delete_laboratory_success(client):
    # 研究室削除
    data = {
        "lab_name": "研究室G",
        "teacher_name": "小林",
        "capacity": 4,
        "field_tag": "AI"
    }
    res = client.post("/api/v1/laboratories", data=json.dumps(data), content_type="application/json")
    lab_id = res.get_json()["lab_id"]
    response = client.delete(f"/api/v1/laboratories/{lab_id}")
    assert response.status_code == 200
    res_json = response.get_json()
    assert "削除しました" in res_json["message"]

def test_delete_laboratory_not_found(client):
    # 存在しない研究室削除
    response = client.delete("/api/v1/laboratories/LAB99")
    assert response.status_code == 404
    res_json = response.get_json()
    assert "見つかりません" in res_json["message"]
