from flask import Flask, render_template, request, redirect, url_for, jsonify, g
import MySQLdb

app = Flask(__name__)

# 資料庫連接配置
def get_db():
    if 'db' not in g:
        g.db = MySQLdb.connect(
            host="localhost",
            user="root",
            passwd="# 你的 MySQL 密碼",  
            db="# 你的 db",
            charset='utf8mb4'
        )
    return g.db

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    student_id = request.form.get('studentID')
    password = request.form.get('password')
    role = request.form.get('role')
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        if role == 'admin':
            cursor.execute("SELECT adminID FROM admin WHERE adminID=%s AND password=%s", (student_id, password))
            admin = cursor.fetchone()
            if admin:
                return redirect(url_for('admin_home'))
            else:
                return "Invalid admin credentials", 401
        
        elif role == 'student':
            cursor.execute("SELECT studentID FROM student WHERE studentID=%s AND password=%s", (student_id, password))
            student = cursor.fetchone()
            if student:
                return redirect(url_for('student_home', student_id=student_id))
            else:
                return "Invalid student credentials", 401
        
    except Exception as e:
        return str(e), 500

    return redirect(url_for('index'))


@app.route('/admin_home')
def admin_home():
    return render_template('admin_home.html')

@app.route('/student_home/<student_id>')
def student_home(student_id):
    return render_template('student_home.html', student_id=student_id)

@app.route('/admin_createG')
def admin_createG():
    return render_template('admin_createG.html')

@app.route('/admin_editG')
def admin_editG():
    return render_template('admin_editG.html')

@app.route('/admin_workslot')
def admin_workslot():
    return render_template('admin_workslot.html')

@app.route('/student_createG')
def student_createG():
    return render_template('student_createG.html')

@app.route('/student_editG/<student_id>')
def student_editG(student_id):
    return render_template('student_editG.html', student_id=student_id)

@app.route('/student_workslot/<student_id>')
def student_workslot(student_id):
    return render_template('student_workslot.html', student_id=student_id)

@app.route('/api/students', methods=['GET'])
def get_students():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT studentID, studentName FROM student")
    students = cursor.fetchall()
    return jsonify(students)

@app.route('/api/teams', methods=['GET'])
def get_teams():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT teamID, teamName, member1, member2, member3 FROM teams")
    teams = cursor.fetchall()
    return jsonify(teams)

@app.route('/api/teams/<int:team_id>', methods=['GET'])
def get_team(team_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT teamName, member1, member2, member3 FROM teams WHERE teamID=%s", (team_id,))
    team = cursor.fetchone()
    if team:
        return jsonify({
            'teamName': team[0],
            'member1': team[1],
            'member2': team[2],
            'member3': team[3]
        })
    else:
        return jsonify({'error': 'Team not found'}), 404

@app.route('/api/teams', methods=['POST'])
def create_team():
    data = request.json
    team_name = data.get('teamName')
    member1 = data.get('member1')
    member2 = data.get('member2')
    member3 = data.get('member3')

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO teams (teamName, member1, member2, member3)
            VALUES (%s, %s, %s, %s)
        """, (team_name, member1, member2, member3))
        db.commit()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/teams/<int:team_id>', methods=['PUT'])
def update_team(team_id):
    data = request.json
    team_name = data.get('teamName')
    member1 = data.get('member1')
    member2 = data.get('member2')
    member3 = data.get('member3')

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE teams
            SET teamName=%s, member1=%s, member2=%s, member3=%s
            WHERE teamID=%s
        """, (team_name, member1, member2, member3, team_id))
        db.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/teams/<int:team_id>', methods=['DELETE'])
def delete_team(team_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM teams WHERE teamID=%s", (team_id,))
        db.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/schedules', methods=['GET'])
def get_schedules():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT time, day, firstChoice, secondChoice FROM schedules")
    schedules = cursor.fetchall()
    return jsonify([{
        'time': schedule[0],
        'day': schedule[1],
        'firstChoice': schedule[2],
        'secondChoice': schedule[3]
    } for schedule in schedules])

@app.route('/api/schedules', methods=['POST'])
def save_schedules():
    schedules = request.json
    db = get_db()
    cursor = db.cursor()
    try:
        # 清除現有排班
        cursor.execute("DELETE FROM schedules")
        
        # 插入新排班
        for schedule in schedules:
            cursor.execute("""
                INSERT INTO schedules (time, day, firstChoice, secondChoice)
                VALUES (%s, %s, %s, %s)
            """, (schedule['time'], schedule['day'], schedule['firstChoice'], schedule['secondChoice']))
        
        db.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/student_team/<student_id>', methods=['GET'])
def get_student_team(student_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT teamID, teamName, member1, member2, member3 
        FROM teams 
        WHERE member1=%s OR member2=%s OR member3=%s
    """, (student_id, student_id, student_id))
    team = cursor.fetchone()
    if team:
        return jsonify({
            'teamID': team[0],
            'teamName': team[1],
            'member1': team[2],
            'member2': team[3],
            'member3': team[4]
        })
    else:
        return jsonify({'error': 'Team not found'}), 404

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(debug=True)
