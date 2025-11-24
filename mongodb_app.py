from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# MongoDB 연결
MONGODB_URI = "mongodb+srv://attendance_user:Ilovekwu123!@attendance-cluster.n2vufnx.mongodb.net/?appName=attendance-cluster"

def get_db():
    client = MongoClient(MONGODB_URI)
    # attendance_db 데이터베이스 사용 (없으면 자동 생성)
    return client.attendance_db

def initialize_database():
    """데이터베이스 초기화 - 테이블(컬렉션)과 샘플 데이터 생성"""
    try:
        db = get_db()
        
        # 샘플 학생 데이터
        sample_students = [
            {
                "student_id": "20240001",
                "name": "김철수", 
                "major": "컴퓨터공학과",
                "created_at": datetime.now()
            },
            {
                "student_id": "20240002",
                "name": "이영희",
                "major": "경영학과", 
                "created_at": datetime.now()
            },
            {
                "student_id": "20240003",
                "name": "박민수",
                "major": "전자공학과",
                "created_at": datetime.now()
            },
            {
                "student_id": "20240004",
                "name": "정수진",
                "major": "디자인학과",
                "created_at": datetime.now()
            },
            {
                "student_id": "20240005",
                "name": "최윤호",
                "major": "영어영문학과",
                "created_at": datetime.now()
            }
        ]
        
        # 샘플 주차 데이터
        sample_weeks = [
            {"week_id": 1, "week_name": "1주차"},
            {"week_id": 2, "week_name": "2주차"},
            {"week_id": 3, "week_name": "3주차"},
            {"week_id": 4, "week_name": "4주차"},
            {"week_id": 5, "week_name": "5주차"},
            {"week_id": 6, "week_name": "6주차"},
            {"week_id": 7, "week_name": "7주차"}
        ]
        
        # 샘플 출석 데이터
        sample_attendance = [
            {
                "student_id": "20240001",
                "week_id": 1,
                "status": "출석",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timestamp": datetime.now()
            },
            {
                "student_id": "20240002", 
                "week_id": 1,
                "status": "출석",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timestamp": datetime.now()
            },
            {
                "student_id": "20240003", 
                "week_id": 1,
                "status": "지각",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timestamp": datetime.now()
            }
        ]
        
        # 기존 데이터 삭제
        db.students.delete_many({})
        db.weeks.delete_many({})
        db.attendance.delete_many({})
        
        # 새 데이터 삽입
        db.students.insert_many(sample_students)
        db.weeks.insert_many(sample_weeks) 
        db.attendance.insert_many(sample_attendance)
        
        return True
    except Exception as e:
        print(f"데이터베이스 초기화 실패: {e}")
        return False

@app.route('/')
def home():
    return jsonify({
        "message": "🎓 출석 관리 시스템 API",
        "status": "작동중",
        "database": "MongoDB"
    })

@app.route('/api/init-db', methods=['POST'])
def init_db():
    """데이터베이스 초기화 API"""
    success = initialize_database()
    if success:
        return jsonify({
            "success": True,
            "message": "✅ 데이터베이스 초기화 완료!",
            "collections": ["students", "weeks", "attendance"]
        })
    else:
        return jsonify({
            "success": False, 
            "error": "데이터베이스 초기화 실패"
        })

@app.route('/api/students', methods=['GET'])
def get_students():
    try:
        db = get_db()
        students = list(db.students.find().sort("student_id", 1))
        for student in students:
            student['_id'] = str(student['_id'])
        return jsonify({
            "success": True, 
            "data": students,
            "count": len(students)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/attendance-board', methods=['GET'])
def get_attendance_board():
    """출석부 전체 데이터 """
    try:
        db = get_db()
        
        students = list(db.students.find().sort("student_id", 1))
        weeks = list(db.weeks.find().sort("week_id", 1))
        attendance = list(db.attendance.find())
        
        result = {
            "weeks": weeks,
            "students": []
        }
        
        for student in students:
            student_data = {
                "student_id": student["student_id"],
                "name": student["name"],
                "student_number": student["student_id"],
                "major": student["major"],
                "attendance": {}
            }
            
            for week in weeks:
                # 해당 학생의 해당 주차 출석 기록 찾기
                week_attendance = next(
                    (a for a in attendance if a["student_id"] == student["student_id"] and a["week_id"] == week["week_id"]),
                    None
                )
                status = week_attendance["status"] if week_attendance else "결석"
                student_data["attendance"][week["week_id"]] = status
            
            student_data['_id'] = str(student['_id'])
            result["students"].append(student_data)
        
        return jsonify({"success": True, "data": result})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/attendance/check', methods=['POST'])
def check_attendance():
    """출석 체크"""
    try:
        data = request.json
        db = get_db()
        
        attendance_record = {
            "student_id": data.get('student_id'),
            "week_id": data.get('week_id', 1),
            "status": data.get('status', '출석'),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now()
        }
        
        # 기존 기록 업데이트 또는 새로 추가
        db.attendance.update_one(
            {
                "student_id": attendance_record["student_id"],
                "week_id": attendance_record["week_id"]
            },
            {"$set": attendance_record},
            upsert=True
        )
        
        return jsonify({"success": True, "message": "출석이 체크되었습니다"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)