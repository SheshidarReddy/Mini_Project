from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mess_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class Student(db.Model):
    roll_number = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    batch = db.Column(db.String(10), nullable=False)
    mess_dues = db.Column(db.Float, default=0.0)
    attendance = db.relationship('Attendance', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(20), db.ForeignKey('student.roll_number'), nullable=False)
    month = db.Column(db.String(20), nullable=False)
    days = db.Column(db.Integer, nullable=False)

class Admin(db.Model):
    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(200), nullable=False)

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Insert demo data if tables are empty
        if not Admin.query.first():
            demo_admin = Admin(
                username='admin',
                password=generate_password_hash('admin123')
            )
            db.session.add(demo_admin)
        
        if not Student.query.first():
            demo_students = [
                Student(
                    roll_number='2023001',
                    name='John Doe',
                    password=generate_password_hash('student123'),
                    batch='2023',
                    mess_dues=0.0
                ),
                Student(
                    roll_number='2023002',
                    name='Jane Smith',
                    password=generate_password_hash('student123'),
                    batch='2023',
                    mess_dues=1500.0
                ),
                Student(
                    roll_number='2024001',
                    name='Bob Johnson',
                    password=generate_password_hash('student123'),
                    batch='2024',
                    mess_dues=800.0
                )
            ]
            db.session.add_all(demo_students)
        
        if not Attendance.query.first():
            demo_attendance = [
                Attendance(roll_number='2023001', month='April 2025', days=28),
                Attendance(roll_number='2023001', month='March 2025', days=30),
                Attendance(roll_number='2023002', month='April 2025', days=25),
                Attendance(roll_number='2024001', month='April 2025', days=27)
            ]
            db.session.add_all(demo_attendance)
        
        db.session.commit()

init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        student = Student.query.filter_by(roll_number=username).first()
        
        if student and check_password_hash(student.password, password):
            session['user_type'] = 'student'
            session['roll_number'] = username
            session['student_name'] = student.name
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials')
            
    return render_template('student_login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password, password):
            session['user_type'] = 'admin'
            session['username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials')
            
    return render_template('admin_login.html')

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('student_login'))
    
    student = Student.query.filter_by(roll_number=session['roll_number']).first()
    attendance = Attendance.query.filter_by(roll_number=session['roll_number']).all()
    attendance_by_month = {att.month: att.days for att in attendance}
    
    return render_template('student_dashboard.html',
                        student_name=student.name,
                        roll_number=student.roll_number,
                        mess_dues=student.mess_dues,
                        attendance_by_month=attendance_by_month)

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    batches = db.session.query(Student.batch).distinct().all()
    batches = [batch[0] for batch in batches]
    
    selected_batch = request.args.get('batch', '')
    students = Student.query.filter_by(batch=selected_batch).all() if selected_batch else []
    students_for_attendance = Student.query.all()
    
    return render_template('admin_dashboard.html',
                        batches=batches,
                        selected_batch=selected_batch,
                        students=[(s.roll_number, s.name) for s in students],
                        students_for_attendance=[(s.roll_number, s.name) for s in students_for_attendance])

@app.route('/update_attendance', methods=['POST'])
def update_attendance():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    month = request.form['month']
    
    for student in Student.query.all():
        days = request.form.get(f'attendance_{student.roll_number}')
        if days:
            # Delete existing attendance for this month
            Attendance.query.filter_by(roll_number=student.roll_number, month=month).delete()
            # Add new attendance
            attendance = Attendance(roll_number=student.roll_number, month=month, days=int(days))
            db.session.add(attendance)
            # Update mess dues (₹100 per day for demo)
            student.mess_dues += int(days) * 100
    
    db.session.commit()
    flash('Attendance updated successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/add_student', methods=['POST'])
def add_student():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    roll_number = request.form['roll_number']
    name = request.form['name']
    password = generate_password_hash(request.form['password'])
    batch = request.form['batch']
    
    try:
        new_student = Student(roll_number=roll_number, name=name, password=password, batch=batch, mess_dues=0.0)
        db.session.add(new_student)
        db.session.commit()
        flash('Student added successfully')
    except:
        db.session.rollback()
        flash('Roll number already exists')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_student', methods=['POST'])
def delete_student():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login'))
    
    roll_number = request.form['roll_number']
    Attendance.query.filter_by(roll_number=roll_number).delete()
    Student.query.filter_by(roll_number=roll_number).delete()
    db.session.commit()
    flash('Student deleted successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)