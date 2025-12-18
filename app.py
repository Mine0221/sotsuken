
# Flask本体とCORS（クロスオリジン対応）、SQLAlchemy、Flask-Migrateをインポート
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.exceptions import BadRequest
# 認証用
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import datetime



# Flaskアプリケーション初期化

app = Flask(__name__)
# SQLiteデータベース設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sotsuken.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# JWT設定
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # 本番は安全な値に変更
# SQLAlchemy初期化
db = SQLAlchemy(app)
# Flask-Migrate初期化
migrate = Migrate(app, db)
# CORS有効化（フロントエンドと別ドメインでもAPI利用可能に）
CORS(app)
# JWT初期化
jwt = JWTManager(app)

# 独自バリデーション例外
class ValidationError(Exception):
    pass

# --- DBモデル定義 ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # ハッシュ化推奨
    role = db.Column(db.String(16), nullable=False)  # 'student', 'teacher', 'admin' など
    student_id = db.Column(db.String(16), db.ForeignKey('students.student_id'), nullable=True)
class Laboratory(db.Model):
    __tablename__ = 'laboratories'
    lab_id = db.Column(db.String(16), primary_key=True)
    lab_name = db.Column(db.String(64), unique=True, nullable=False)
    teacher_name = db.Column(db.String(64), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    field_tag = db.Column(db.String(64), nullable=True)
    # 配属学生リレーション
    students = db.relationship('Student', backref='laboratory', lazy='dynamic')
    # 特別希望学生リレーション（中間テーブルで正規化）
    special_students = db.relationship('LabSpecialStudent', backref='laboratory', lazy='dynamic')

class LabSpecialStudent(db.Model):
    __tablename__ = 'lab_special_students'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lab_id = db.Column(db.String(16), db.ForeignKey('laboratories.lab_id'))
    student_id = db.Column(db.String(16), db.ForeignKey('students.student_id'))

class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    gpa = db.Column(db.Float, nullable=True)
    assigned_lab = db.Column(db.String(16), db.ForeignKey('laboratories.lab_id'))
    satisfaction = db.Column(db.Integer, nullable=True)  # 納得度
    preferences = db.relationship('Preference', backref='student', lazy='joined')

class Preference(db.Model):
    __tablename__ = 'preferences'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(16), db.ForeignKey('students.student_id'))
    lab_id = db.Column(db.String(16), db.ForeignKey('laboratories.lab_id'))
    rank = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint('student_id', 'lab_id', name='uq_student_lab'),)

# --- マッチング履歴テーブル ---
class MatchingResult(db.Model):
    __tablename__ = 'matching_results'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_id = db.Column(db.String(64), nullable=False, index=True)  # 実行単位ID
    executed_at = db.Column(db.DateTime, nullable=False)
    version = db.Column(db.String(32), nullable=True)
    student_id = db.Column(db.String(16), db.ForeignKey('students.student_id'))
    assigned_lab = db.Column(db.String(16), db.ForeignKey('laboratories.lab_id'))
    satisfaction = db.Column(db.Integer, nullable=True)
    summary = db.Column(db.Text, nullable=True)  # サマリ情報（JSON等）


# --- DBマイグレーション用コマンド例 ---
# flask db init
# flask db migrate -m "init"
# flask db upgrade

# --- ダミーデータ（本来はDBで管理） ---
labs = [
    {"lab_id": "LAB01", "lab_name": "研究室A", "teacher_name": "佐藤", "capacity": 10, "field_tag": "AI"},
    {"lab_id": "LAB02", "lab_name": "研究室B", "teacher_name": "鈴木", "capacity": 8, "field_tag": "ロボティクス"}
]
students = [
    {"student_id": "20250001", "name": "山田 太郎", "email": "yamada@example.com", "gpa": 3.6, "assigned_lab": "LAB01"}
]
preferences = {
    "20250001": [
        {"lab_id": "LAB01", "rank": 1},
        {"lab_id": "LAB02", "rank": 2}
    ]

}

# ===== 共通エラーハンドラ（113行目） =====
@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify({"error": "Bad Request", "message": str(e)}), 400

class ValidationError(Exception):
    pass

@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": "Validation Error", "message": str(e)}), 400

@app.errorhandler(404)
def handle_not_found(e):
    return jsonify({"error": "Not Found", "message": str(e)}), 404

@app.errorhandler(500)
def handle_internal_error(e):
    return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


# --- ユーザ登録API ---
@app.route('/api/v1/auth/register', methods=['POST'])
def register_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    student_id = data.get('student_id')
    # 必須項目チェック
    if not email or not password or not role:
        raise ValidationError('email, password, roleは必須です')
    # email重複チェック
    if User.query.filter_by(email=email).first():
        raise ValidationError('このemailは既に登録されています')
    # role値検証
    allowed_roles = ['student', 'teacher', 'admin']
    if role not in allowed_roles:
        raise ValidationError(f"roleは{allowed_roles}のいずれかで指定してください")
    # studentロールの場合はstudent_id必須
    if role == 'student':
        if not student_id:
            raise ValidationError('studentロールの場合はstudent_idが必須です')
        # student_idが存在するかチェック
        if not Student.query.filter_by(student_id=student_id).first():
            raise ValidationError('指定されたstudent_idの学生が存在しません')
    else:
        student_id = None
    # パスワードハッシュ化
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, role=role, student_id=student_id)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'user_id': new_user.id, 'message': 'ユーザを登録しました'}), 201

# --- ログインAPI（JWT発行） ---
@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        from werkzeug.exceptions import Unauthorized
        raise Unauthorized('認証に失敗しました')
    access_token = create_access_token(identity={
        'user_id': user.id,
        'email': user.email,
        'role': user.role,
        'student_id': user.student_id
    }, expires_delta=datetime.timedelta(hours=2))
    return jsonify({'access_token': access_token, 'role': user.role})

# --- 認証保護・権限制御のサンプルAPI ---
def role_required(roles):
    def wrapper(fn):
        from functools import wraps
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            identity = get_jwt_identity()
            if identity and identity.get('role') in roles:
                return fn(*args, **kwargs)
            from werkzeug.exceptions import Forbidden
            raise Forbidden('権限がありません')
        return decorated
    return wrapper

# 例: 管理者のみアクセス可能なAPI
@app.route('/api/v1/admin/secure', methods=['GET'])
@role_required(['admin'])
def admin_only_api():
    return jsonify({'message': '管理者専用APIです'})

# 例: 学生のみアクセス可能なAPI
@app.route('/api/v1/student/secure', methods=['GET'])
@role_required(['student'])
def student_only_api():
    return jsonify({'message': '学生専用APIです'})

#--- 研究室一覧取得API ---
@app.route('/api/v1/laboratories', methods=['GET'])
def get_laboratories():
    """研究室一覧取得API
    ---
    parameters:
      - name: page
        in: query
        type: integer
      - name: per_page
        in: query
        type: integer
      - name: field_tag
        in: query
        type: string
    responses:
      200:
        description: 研究室一覧
    """
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    field_tag = request.args.get('field_tag')
    query = Laboratory.query
    if field_tag:
        query = query.filter_by(field_tag=field_tag)
    total = query.count()
    labs = query.offset((page - 1) * per_page).limit(per_page).all()
    labs_list = [
        {
            "lab_id": lab.lab_id,
            "lab_name": lab.lab_name,
            "teacher_name": lab.teacher_name,
            "capacity": lab.capacity,
            "field_tag": lab.field_tag
        }
        for lab in labs
    ]
    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "labs": labs_list
    })

# --- パスワードリセットAPI ---
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import decode_token

# パスワードリセットリクエストAPI
@app.route('/api/v1/auth/request_password_reset', methods=['POST'])
def request_password_reset():
    data = request.json
    email = data.get('email')
    if not email:
        raise ValidationError('emailは必須です')
    user = User.query.filter_by(email=email).first()
    if not user:
        from werkzeug.exceptions import NotFound
        raise NotFound('ユーザーが見つかりません')
    # JWTトークンをリセット用に発行（有効期限10分）
    reset_token = create_access_token(identity={'user_id': user.id, 'email': user.email}, expires_delta=datetime.timedelta(minutes=10))
    # 本来はメール送信だが、今回はAPIで返却
    return jsonify({'reset_token': reset_token, 'message': 'パスワードリセット用トークンを発行しました'})

# パスワードリセット実行API
@app.route('/api/v1/auth/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    reset_token = data.get('reset_token')
    new_password = data.get('new_password')
    if not reset_token or not new_password:
        raise ValidationError('reset_tokenとnew_passwordは必須です')
    try:
        decoded = decode_token(reset_token)
        identity = decoded['sub'] if 'sub' in decoded else decoded['identity']
        user_id = identity['user_id'] if isinstance(identity, dict) else identity
    except Exception:
        from werkzeug.exceptions import Unauthorized
        raise Unauthorized('トークンが不正または期限切れです')
    user = User.query.filter_by(id=user_id).first()
    if not user:
        from werkzeug.exceptions import NotFound
        raise NotFound('ユーザーが見つかりません')
    # パスワードハッシュ化（本番は強度の高い方式を推奨）
    user.password = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({'message': 'パスワードをリセットしました'})

# --- 研究室API ---
# 研究室新規作成API（DB連携）
@app.route('/api/v1/laboratories', methods=['POST'])
def create_laboratory():
    data = request.json
    required = ["lab_name", "teacher_name", "capacity", "field_tag"]
    for key in required:
        if key not in data:
            raise ValidationError(f"{key}は必須です")
    if not isinstance(data["capacity"], int) or data["capacity"] < 1:
        raise ValidationError("capacityは1以上の整数で入力してください")
    if Laboratory.query.filter_by(lab_name=data["lab_name"]).first():
        raise ValidationError("研究室名は既に存在します")
    # --- OpenAPI仕様雛形（Swagger UI等で利用可） ---
    # from flask_swagger_ui import get_swaggerui_blueprint
    # SWAGGER_URL = '/swagger'
    # API_URL = '/static/swagger.json'
    # swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL)
    # app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    # lab_id自動生成（例: LAB+連番）
    last_lab = Laboratory.query.order_by(Laboratory.lab_id.desc()).first()
    next_id = 1
    if last_lab and last_lab.lab_id.startswith("LAB"):
        try:
            next_id = int(last_lab.lab_id[3:]) + 1
        except:
            pass
    lab_id = f"LAB{next_id:02d}"
    new_lab = Laboratory(
        lab_id=lab_id,
        lab_name=data["lab_name"],
        teacher_name=data["teacher_name"],
        capacity=data["capacity"],
        field_tag=data["field_tag"]
    )
    db.session.add(new_lab)
    db.session.commit()
    return jsonify({"lab_id": new_lab.lab_id, "message": "研究室を登録しました"}), 201

# 研究室削除API（DB連携）
@app.route('/api/v1/laboratories/<lab_id>', methods=['DELETE'])
def delete_laboratory(lab_id):
    lab = Laboratory.query.filter_by(lab_id=lab_id).first()
    if not lab:
        from werkzeug.exceptions import NotFound
        raise NotFound("研究室が見つかりません")
    db.session.delete(lab)
    db.session.commit()
    return jsonify({"message": f"{lab.lab_name} を削除しました"})




# --- 学生API ---
# 学生一覧取得API（DB連携）
@app.route('/api/v1/students', methods=['GET'])
def get_students():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    query = Student.query
    total = query.count()
    students = query.offset((page - 1) * per_page).limit(per_page).all()
    students_list = [
        {
            "student_id": s.student_id,
            "name": s.name,
            "email": s.email,
            "gpa": s.gpa,
            "assigned_lab": s.assigned_lab
        }
        for s in students
    ]
    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "students": students_list
    })

# --- 学生新規登録API ---
@app.route('/api/v1/students', methods=['POST'])
def create_student():
    data = request.json
    required = ["student_id", "name", "email"]
    for key in required:
        if key not in data:
            raise ValidationError(f"{key}は必須です")
    if Student.query.filter_by(student_id=data["student_id"]).first():
        raise ValidationError("student_idは既に存在します")
    new_student = Student(
        student_id=data["student_id"],
        name=data["name"],
        email=data["email"],
        gpa=data.get("gpa"),
        assigned_lab=None
    )
    db.session.add(new_student)
    db.session.commit()
    return jsonify({"student_id": new_student.student_id, "message": "学生を登録しました"}), 201

# --- 学生情報更新API ---
@app.route('/api/v1/students/<student_id>', methods=['PUT', 'PATCH'])
def update_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        from werkzeug.exceptions import NotFound
        raise NotFound("学生が見つかりません")
    data = request.json
    for key in ["name", "email", "gpa", "assigned_lab"]:
        if key in data:
            setattr(student, key, data[key])
    db.session.commit()
    return jsonify({"student_id": student.student_id, "message": "学生情報を更新しました"})

# --- 学生削除API ---
@app.route('/api/v1/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        from werkzeug.exceptions import NotFound
        raise NotFound("学生が見つかりません")
    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": f"{student.name} を削除しました"})

# --- 学生の希望一覧取得API（REST設計） ---
@app.route('/api/v1/students/<student_id>/preferences', methods=['GET'])
def get_student_preferences(student_id):
    prefs = Preference.query.filter_by(student_id=student_id).order_by(Preference.rank).all()
    prefs_list = [
        {"lab_id": p.lab_id, "rank": p.rank}
        for p in prefs
    ]
    return jsonify(prefs_list)

# --- 学生の配属結果取得API ---
@app.route('/api/v1/students/<student_id>/assignment', methods=['GET'])
def get_student_assignment(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        from werkzeug.exceptions import NotFound
        raise NotFound("学生が見つかりません")
    return jsonify({
        "student_id": student.student_id,
        "assigned_lab": student.assigned_lab,
        "satisfaction": student.satisfaction
    })

# --- 学生の納得度・マッチング履歴取得API ---
@app.route('/api/v1/students/<student_id>/matching_history', methods=['GET'])
def get_student_matching_history(student_id):
    results = MatchingResult.query.filter_by(student_id=student_id).order_by(MatchingResult.executed_at.desc()).all()
    history = [
        {
            "batch_id": r.batch_id,
            "executed_at": r.executed_at.isoformat() if r.executed_at else None,
            "assigned_lab": r.assigned_lab,
            "satisfaction": r.satisfaction,
            "summary": r.summary
        }
        for r in results
    ]
    return jsonify(history)

# 学生詳細取得API（DB連携）
@app.route('/api/v1/students/<student_id>', methods=['GET'])
def get_student_detail(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        from werkzeug.exceptions import NotFound
        raise NotFound("学生が見つかりません")
    return jsonify({
        "student_id": student.student_id,
        "name": student.name,
        "email": student.email,
        "gpa": student.gpa,
        "assigned_lab": student.assigned_lab
    })



# --- 希望API ---
# 学生の希望取得API（DB連携）
@app.route('/api/v1/preferences/<student_id>', methods=['GET'])
def get_preferences(student_id):
    prefs = Preference.query.filter_by(student_id=student_id).order_by(Preference.rank).all()
    prefs_list = [
        {"lab_id": p.lab_id, "rank": p.rank}
        for p in prefs
    ]
    return jsonify(prefs_list)

# 学生の希望登録API（DB連携）
@app.route('/api/v1/preferences', methods=['POST'])
def set_preferences():
    data = request.json
    student_id = data.get("student_id")
    prefs = data.get("preferences")
    if not student_id or not isinstance(prefs, list):
        raise ValidationError("student_idとpreferencesは必須です")
    # 既存の希望を削除
    Preference.query.filter_by(student_id=student_id).delete()
    # 新しい希望を追加
    for pref in prefs:
        lab_id = pref.get("lab_id")
        rank = pref.get("rank")
        if not lab_id or not isinstance(rank, int):
            continue
        db.session.add(Preference(student_id=student_id, lab_id=lab_id, rank=rank))
    db.session.commit()
    return jsonify({"message": "希望を登録しました"})


# --- マッチングAPI ---
# マッチング実行API（管理者用）
@app.route('/api/v1/admin/matching/run', methods=['POST'])
def run_matching():
    # --- DBからデータ取得 ---
    students = Student.query.all()
    laboratories = Laboratory.query.all()
    if not students:
        raise ValidationError("学生データが存在しません")
    if not laboratories:
        raise ValidationError("研究室データが存在しません")
    lab_dict = {lab.lab_id: lab for lab in laboratories}
    # 各研究室の割当学生リストを初期化
    lab_assignments = {lab.lab_id: [] for lab in laboratories}
    # 学生ごとに希望順位リストを取得
    student_prefs = {}
    for s in students:
        prefs = Preference.query.filter_by(student_id=s.student_id).order_by(Preference.rank).all()
        student_prefs[s.student_id] = [p.lab_id for p in prefs]
    # 未配属学生リスト
    unassigned = students[:]

    # --- 学生希望順・GPA優先で配属 ---
    # 1. 希望順位順に各学生が応募
    while unassigned:
        for student in unassigned[:]:
            prefs = student_prefs.get(student.student_id, [])
            for lab_id in prefs:
                if len(lab_assignments[lab_id]) < lab_dict[lab_id].capacity:
                    lab_assignments[lab_id].append(student)
                    student.assigned_lab = lab_id
                    unassigned.remove(student)
                    break
            # どこにも入れなかった場合は未配属

    # 2. 定員超過時のGPA優先選抜
    for lab_id, assigned in lab_assignments.items():
        if len(assigned) > lab_dict[lab_id].capacity:
            # GPA順で定員分だけ残す
            assigned.sort(key=lambda s: (-s.gpa, student_prefs[s.student_id].index(lab_id) if lab_id in student_prefs[s.student_id] else 99))
            selected = assigned[:lab_dict[lab_id].capacity]
            lab_assignments[lab_id] = selected
            # 落選者は未配属
            for s in assigned[lab_dict[lab_id].capacity:]:
                s.assigned_lab = None

    # 3. DBへ保存
    for s in students:
        db.session.add(s)
    db.session.commit()

    return jsonify({"message": "マッチングを実行しました", "result_id": "20251211-001"})

# マッチング結果取得API
@app.route('/api/v1/matching/results', methods=['GET'])
def get_matching_results():
    # ダミー結果（本来はマッチング結果テーブルから取得）
    results = [
        {"student_id": s["student_id"], "name": s["name"], "assigned_lab": s["assigned_lab"], "lab_name": next((l["lab_name"] for l in labs if l["lab_id"] == s["assigned_lab"]), None)}
        for s in students
    ]
    return jsonify(results)


# --- インポートAPI ---
# 学生データCSVインポートAPI（管理者用・ダミー）
@app.route('/api/v1/admin/students/import', methods=['POST'])
def import_students():
    # ファイル処理は省略（本来はCSVを受け取りDBに登録）
    return jsonify({"imported": 0, "errors": [{"row": 12, "error": "学籍番号が重複しています"}]})


# --- バックアップAPI ---
# バックアップダウンロードAPI（管理者用・ダミー）
@app.route('/api/v1/admin/backup', methods=['GET'])
def download_backup():
    # ダミー応答（本来はバックアップファイルを返す）
    return jsonify({"message": "バックアップダウンロード（ダミー）"})

# データリストアAPI（管理者用・ダミー）
@app.route('/api/v1/admin/restore', methods=['POST'])
def restore_backup():
    # ダミー応答（本来はアップロードファイルからDBを復元）
    return jsonify({"message": "データリストア（ダミー）"})


# --- アプリ起動 ---
if __name__ == '__main__':
    app.run(debug=True)
