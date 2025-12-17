# 仮研究室配属マッチングアルゴリズム（Gale-Shapley法＋GPA＋特別希望枠）

import random
from typing import List, Dict, Optional

# --- テストデータ定義 ---

class Student:
    def __init__(self, student_id, name, gpa, preferences):
        self.student_id = student_id
        self.name = name
        self.gpa = gpa
        self.preferences = preferences  # 研究室IDの希望順位リスト
        self.assignment = None  # 配属先研究室ID
        self.satisfaction = None  # 納得度

class Laboratory:
    def __init__(self, lab_id, name, capacity, special_students=None):
        self.lab_id = lab_id
        self.name = name
        self.capacity = capacity
        self.special_students = special_students or []  # 優先枠学生IDリスト
        self.assigned_students = []  # 配属学生IDリスト

# サンプル学生データ
students = []
names = ['田中', '佐藤', '鈴木', '高橋', '伊藤', '渡辺', '山本', '中村', '小林', '加藤', '吉田', '山田', '佐々木', '斎藤', '松本', '井上', '木村', '林', '清水', '山口', '森', '池田', '橋本', '阿部', '石井', '福田', '大野', '岡田', '三浦', '藤田', '西村']
num_students = 30
num_labs = 6
for i in range(num_students):
    sid = f'S{str(i+1).zfill(2)}'
    name = names[i % len(names)]
    gpa = round(2.5 + 1.5 * (i % 5) / 4 + 0.1 * (i % 3), 2)  # GPA: 2.5〜4.0程度でばらつき
    # 希望順位はランダム
    prefs = [f'L{j+1}' for j in range(num_labs)]
    random.shuffle(prefs)
    students.append(Student(sid, name, gpa, prefs[:num_labs]))  # 全研究室分希望

# サンプル研究室データ（L1はS03を特別希望）
laboratories = []
lab_names = ['情報工学研究室', '物理学研究室', '化学研究室', '生物学研究室', '機械工学研究室', '電気電子研究室']
for i in range(num_labs):
    lid = f'L{i+1}'
    name = lab_names[i % len(lab_names)]
    capacity = 5  # 定員5名
    # 特別希望学生は0～2名でランダム
    num_special = random.randint(0, 2)
    special_students = [f'S{str(j+1).zfill(2)}' for j in random.sample(range(num_students), num_special)] if num_special > 0 else []
    laboratories.append(Laboratory(lid, name, capacity, special_students=special_students))

# --- マッチングアルゴリズム ---
def match_students(students: List[Student], laboratories: List[Laboratory]):
    # 研究室ID→Laboratoryオブジェクト辞書
    lab_dict = {lab.lab_id: lab for lab in laboratories}
    # 未配属学生リスト
    unassigned = students[:]

    print("--- 特別希望枠の配属 ---")
    for lab in laboratories:
        for sid in lab.special_students:
            student = next((s for s in unassigned if s.student_id == sid), None)
            if student and len(lab.assigned_students) < lab.capacity:
                lab.assigned_students.append(student.student_id)
                student.assignment = lab.lab_id
                unassigned.remove(student)
                print(f"{lab.name}が特別希望：{student.name}（GPA:{student.gpa}）を優先配属")

    print("\n--- 学生希望順による配属（Gale-Shapley法） ---")
    while unassigned:
        for student in unassigned[:]:
            for lab_id in student.preferences:
                lab = lab_dict[lab_id]
                if len(lab.assigned_students) < lab.capacity:
                    lab.assigned_students.append(student.student_id)
                    student.assignment = lab.lab_id
                    unassigned.remove(student)
                    print(f"{student.name}（GPA:{student.gpa}）が{lab.name}に希望順位{student.preferences.index(lab_id)+1}で仮配属")
                    break
            # どこにも入れなかった場合は未配属

    print("\n--- 定員超過時のGPA優先選抜 ---")
    for lab in laboratories:
        if len(lab.assigned_students) > lab.capacity:
            assigned_objs = [s for s in students if s.student_id in lab.assigned_students]
            assigned_objs.sort(key=lambda s: (-s.gpa, student.preferences.index(lab.lab_id)))
            selected = assigned_objs[:lab.capacity]
            print(f"{lab.name}で定員超過。GPA順で選抜:")
            for s in assigned_objs:
                mark = "◎" if s in selected else "×"
                print(f"  {mark} {s.name}（GPA:{s.gpa}）")
            lab.assigned_students = [s.student_id for s in selected]
            for s in assigned_objs[lab.capacity:]:
                s.assignment = None

    # 4. 納得度算出
    for student in students:
        if student.assignment and student.assignment in student.preferences:
            rank = student.preferences.index(student.assignment) + 1
            student.satisfaction = int(100 * (1 - (rank - 1) / len(student.preferences)))
        else:
            student.satisfaction = 0

    return students, laboratories

# --- 実行＆結果表示 ---
if __name__ == "__main__":
    # マッチング前に各学生の希望順位を表示
    print("【学生ごとの希望順位】")
    lab_id_to_name = {lab.lab_id: lab.name for lab in laboratories}
    students_sorted = sorted(students, key=lambda s: -s.gpa)
    for s in students_sorted:
        prefs_str = ', '.join([f"{lab_id_to_name.get(lid, lid)}({lid})" for lid in s.preferences])
        print(f"{s.name}（GPA:{s.gpa}）: {prefs_str}")

    matched_students, matched_labs = match_students(students, laboratories)
    print("\n【学生ごとの配属結果】")
    matched_students_sorted = sorted(matched_students, key=lambda s: -s.gpa)
    for s in matched_students_sorted:
        print(f"{s.name}（GPA:{s.gpa}）→ {s.assignment or '未配属'} 納得度:{s.satisfaction}%")
    print("\n【研究室ごとの配属学生】")
    for lab in matched_labs:
        names = [s.name for s in students if s.student_id in lab.assigned_students]
        print(f"{lab.name}（定員:{lab.capacity}）: {', '.join(names)}")
