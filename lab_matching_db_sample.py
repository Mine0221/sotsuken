# Flask-SQLAlchemyモデルを前提としたマッチングロジック移植用サンプル
# DBから学生・研究室データを取得し、配属結果をDBに保存する形

from app import db, Student, Laboratory  # 既存のapp.pyモデルを利用
from sqlalchemy.orm import joinedload

# Studentモデルにpreferencesリレーションがなければ以下をapp.pyに追加してください:
# preferences = db.relationship('Preference', backref='student', lazy='joined')

# --- マッチングロジック（DBモデルベース） ---
def match_students_db():
    # 1. データ取得
    students = Student.query.options(joinedload(Student.preferences)).all()
    laboratories = Laboratory.query.all()
    lab_dict = {lab.id: lab for lab in laboratories}
    unassigned = students[:]

    # 2. 特別希望枠の配属
    for lab in laboratories:
        for sid in lab.special_students:  # special_studentsは学生IDリスト
            student = next((s for s in unassigned if s.id == sid), None)
            if student and len(lab.assigned_students) < lab.capacity:
                lab.assigned_students.append(student.id)
                student.assignment = lab.id
                unassigned.remove(student)

    # 3. 学生希望順による配属
    while unassigned:
        for student in unassigned[:]:
            for pref in student.preferences:  # Preferenceモデルで lab_id を持つ
                lab = lab_dict.get(pref.lab_id)
                if lab and len(lab.assigned_students) < lab.capacity:
                    lab.assigned_students.append(student.id)
                    student.assignment = lab.id
                    unassigned.remove(student)
                    break

    # 4. 定員超過時のGPA優先選抜
    for lab in laboratories:
        if len(lab.assigned_students) > lab.capacity:
            assigned_objs = [s for s in students if s.id in lab.assigned_students]
            assigned_objs.sort(key=lambda s: (-s.gpa, [p.lab_id for p in s.preferences].index(lab.id)))
            selected = assigned_objs[:lab.capacity]
            lab.assigned_students = [s.id for s in selected]
            for s in assigned_objs[lab.capacity:]:
                s.assignment = None

    # 5. 納得度算出
    for student in students:
        if student.assignment and any(p.lab_id == student.assignment for p in student.preferences):
            rank = next(i for i, p in enumerate(student.preferences) if p.lab_id == student.assignment) + 1
            student.satisfaction = int(100 * (1 - (rank - 1) / len(student.preferences)))
        else:
            student.satisfaction = 0

    # 6. DBへ保存
    for student in students:
        db.session.add(student)
    for lab in laboratories:
        db.session.add(lab)
    db.session.commit()

    return students, laboratories

# --- 実行例（Flask context内で呼び出し） ---
if __name__ == "__main__":
    from app import app
    with app.app_context():
        matched_students, matched_labs = match_students_db()
        print("【学生ごとの配属結果】")
        for s in sorted(matched_students, key=lambda s: -s.gpa):
            print(f"{s.name}（GPA:{s.gpa}）→ {s.assignment or '未配属'} 納得度:{s.satisfaction}%")
        print("\n【研究室ごとの配属学生】")
        for lab in matched_labs:
            names = [s.name for s in matched_students if s.id in lab.assigned_students]
            print(f"{lab.name}（定員:{lab.capacity}）: {', '.join(names)}")
