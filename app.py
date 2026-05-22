import csv
from sklearn.preprocessing import LabelEncoder
from flask import Flask, render_template, request, flash, redirect, url_for, session,jsonify,send_file
import numpy as np
import mysql.connector
import cv2, os
import pandas as pd
import pickle
import smtplib
import datetime
import time
import random
from PIL import Image
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length
from werkzeug.security import check_password_hash, generate_password_hash  # For secure password handling
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms import StringField, DateField
import cv2
from flask import Response
import re
import tkinter as tk
from tkinter import messagebox
import cv2
from ultralytics import YOLO
from docx import Document
from PyPDF2 import PdfReader
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from yolo_webcam import live_webcam_detection

mydb = mysql.connector.connect(host="localhost", user="root", port="3306", passwd="", database="face_biometric")
cursor = mydb.cursor()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'navya'
app.config["TRAINING_IMAGE_PATH"] = os.path.join(os.getcwd(), "TrainingImage")
app.config["TRAINED_MODEL_FOLDER_PATH"] = os.path.join(os.getcwd(), "Trained_Model")
app.config["TRAINED_MODEL_PATH"] = os.path.join(os.getcwd(), "Trained_Model" , "Trainner.yml")

if not os.path.exists(app.config["TRAINING_IMAGE_PATH"]):
    os.makedirs(app.config["TRAINING_IMAGE_PATH"])

if not os.path.exists(app.config["TRAINED_MODEL_FOLDER_PATH"]):
    os.makedirs(app.config["TRAINED_MODEL_FOLDER_PATH"])

class CreateExamForm(FlaskForm):
    exam_name = StringField('Exam Name', validators=[DataRequired()])  # Exam name field
    exam_date = DateField('Exam Date', format='%Y-%m-%d', validators=[DataRequired()])  # Exam date field


# Load the saved YOLO model from your local system
model_path = 'yolov8_saved_model.pt' 
model = YOLO(model_path)  # Load the YOLO model

# Variables to track the previous x-coordinate and height of the person's head
previous_x = None
previous_height = None
sender_address = 'cse.takeoff@gmail.com'
sender_pass = 'digkagfgyxcjltup'

def send_mail(subject,receiver_address, mail_content):
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = subject
    message.attach(MIMEText(mail_content, 'plain'))
    ses = smtplib.SMTP('smtp.gmail.com', 587)
    ses.starttls()
    ses.login(sender_address, sender_pass)
    text = message.as_string()
    ses.sendmail(sender_address, receiver_address, text)
    ses.quit()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/portfolio_details')
def portfolio_details():
    return render_template('portfolio-details.html')


@app.route('/Add_student', methods=["GET", "POST"])
def Add_student():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        pwd = request.form['pwd']
        cpwd = request.form['cpwd']
        pno = request.form['pno']
        addr = request.form['addr']
        uname = request.form['uname']
        otp1 = random.randint(0000, 9999)
        ts = time.time()
        date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        sql = "select * from user_registration"
        result = pd.read_sql_query(sql, mydb)
        email1 = result['email'].values
        # print(email1)
        if email in email1:
            flash("Email already existed", "warning")
            return render_template('add_student.html')
        if pwd == cpwd:
            cam = cv2.VideoCapture(0)
            harcascadePath = r"haarcascade\haarcascade_frontalface_default.xml"
            detector = cv2.CascadeClassifier(harcascadePath)
            sampleNum = 0

            

            while (True):
                ret, img = cam.read()
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = detector.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    # incrementing sample number
                    sampleNum = sampleNum + 1
                    # saving the captured face in the dataset folder TrainingImage
                    cv2.imwrite("TrainingImage/ " + name + "." + str(otp1) + '.' + str(sampleNum) + ".jpg",
                                gray[y:y + h, x:x + w])
                    # display the frame

                else:
                    cv2.imshow('frame', img)
                if cv2.waitKey(100) & 0xFF == ord('q'):
                    break
                elif sampleNum > 350:
                    break

            cam.release()
            cv2.destroyAllWindows()
            sql = "INSERT INTO user_registration (sid,name,email,uname,pwd,pno,addr,d1) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
            val = (otp1, name, email, uname, pwd, pno, addr, date)
            cursor.execute(sql, val)
            mydb.commit()
            # training()
            # msg = 'Your Exam Id is: '
            # t = 'Regards,'
            # t1 = 'Online Student Authentication and Proctoring System.'
            # mail_content = 'Dear ' + name +','+'\n'+msg  + str(otp1) +'\n'+ '\n' + t + '\n' + t1
            # sender_address = 'cse.takeoff@gmail.com'
            # sender_pass = 'digkagfgyxcjltup'
            # receiver_address = email
            # message = MIMEMultipart()
            # message['From'] = sender_address
            # message['To'] = receiver_address
            # message['Subject'] = 'Online Student Authentication and Proctoring System.'
            # message.attach(MIMEText(mail_content, 'plain'))
            # ses = smtplib.SMTP('smtp.gmail.com', 587)
            # ses.starttls()
            # ses.login(sender_address, sender_pass)
            # text = message.as_string()
            # ses.sendmail(sender_address, receiver_address, text)
            # ses.quit()
            flash("Successfully Registered", "warning")
            return render_template('add_student.html')
        else:
            flash("password and confirm password not same", "warning")
            return render_template('add_student.html')

    return render_template('add_student.html')


@app.route('/Add_faculty', methods=["GET", "POST"])
def Add_faculty():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        department = request.form['department']
        emp_id = request.form['emp_id']
        pwd = request.form['pwd']
        cpwd = request.form['cpwd']
        mobile = request.form['mobile']
        otp1 = random.randint(1000, 9999)  # random 4-digit OTP
        ts = time.time()
        date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')

        # Validate mobile number (should be exactly 10 digits)
        if not re.match(r'^\d{10}$', mobile):
            flash("Mobile number must be exactly 10 digits", "warning")
            return render_template('add_faculty.html')

        # Validate username (only letters and spaces allowed)
        if not re.match(r'^[A-Za-z ]+$', fullname):
            flash("Username should only contain letters and spaces", "warning")
            return render_template('add_faculty.html')

        # Validate department (only letters and spaces allowed)
        if not re.match(r'^[A-Za-z ]+$', department):
            flash("Department should only contain letters and spaces", "warning")
            return render_template('add_faculty.html')

        # Check if the email already exists in the database
        sql = "SELECT * FROM faculty_registration"
        result = pd.read_sql_query(sql, mydb)
        email1 = result['email'].values
        
        if email in email1:
            flash("Email already existed", "warning")
            return render_template('add_faculty.html')

        # Check if password and confirm password match
        if pwd == cpwd:
            # Insert faculty details into the database
            sql = "INSERT INTO faculty_registration (otp, username, email, department, emp_id, pwd, mobile, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            val = (otp1, fullname, email, department, emp_id, pwd, mobile, date)
            cursor.execute(sql, val)
            mydb.commit()

            # Send confirmation email with OTP
            msg = f'Dear {fullname},\n\nYour Faculty ID is: {emp_id}\nYour OTP is: {otp1}\n\nRegards,\nOnline Faculty Authentication System'

            send_mail("Faculty Registration", email, msg)

            flash("Faculty successfully registered", "success")
            return redirect('Add_faculty')

        else:
            flash("Password and confirm password do not match", "warning")
            return render_template('add_faculty.html')

    return render_template('add_faculty.html')


@app.route('/faculty/profile/<emp_id>', methods=['GET'])
def faculty_profile(emp_id):
    sql = "SELECT * from faculty_registration WHERE emp_id=%s"
    cursor.execute(sql, (emp_id,))
    faculty_data = cursor.fetchone()

    if faculty_data:
        return render_template('faculty_profile.html', faculty_data=faculty_data)
    else:
        flash("Faculty not found", "warning")
        return redirect(url_for('faculty_home'))



# Example Login Form using Flask-WTF
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    user_type = SelectField('User Type', choices=[('1', 'Admin'), ('2', 'User')], validators=[DataRequired()])
# Admin login route
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


@app.route('/adminlogin', methods=["GET", "POST"])
def adminlogin():
    form = LoginForm()  # Initialize the form

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        # Perform your authentication logic here
        if username == 'admin' and password == 'admin':  # Hardcoded check for simplicity
            # flash("Welcome Admin", "success")
            return redirect(url_for('adminhome'))
        else:
            flash("Invalid Admin Credentials", "danger")

    return render_template('admin_login.html', form=form)  # Pass form object to the template

@app.route('/studentlogin', methods=['GET', 'POST'])
def studentlogin():
    form = LoginForm()  # Initialize the form
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Use parameterized queries to prevent SQL injection
        sql = "SELECT * FROM user_registration WHERE uname=%s AND pwd=%s"
        cursor.execute(sql, (username, password))
        results = cursor.fetchall()

        if not results:
            flash("Invalid Email / Password", "danger")
            return render_template('studentlogin.html', form=form)  # Render the same page with the form

        # Set session variables upon successful login
        if len(results) > 0:
            
            recognizer = cv2.face.LBPHFaceRecognizer_create()  # cv2.createLBPHFaceRecognizer()
            recognizer.read(r"Trained_Model\Trainner.yml")
            harcascadePath = r"Haarcascade\haarcascade_frontalface_default.xml"
            faceCascade = cv2.CascadeClassifier(harcascadePath)
            global cam
            cam = cv2.VideoCapture(0)
            font = cv2.FONT_HERSHEY_SIMPLEX
            pkl_file = open('label_encoder.pkl', 'rb')
            le = pickle.load(pkl_file)
            pkl_file.close()
            global tt
            count = []
            flag = 0
            det = 0
            global val_data, global_stop
            global_stop = False
            while True:
                _, frame = cam.read()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = faceCascade.detectMultiScale(gray, 1.2, 5)
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (225, 0, 0), 2)
                    Id, conf = recognizer.predict(gray[y:y + h, x:x + w])
                    print(conf)
                    if (conf > 38):
                        flag += 1
                        person_name = "Unknown"
                        if flag==20:
                            flash("Unknown detection", "danger")
                            return render_template("studentlogin.html")
                    else:
                        det+=1
                        tt = le.inverse_transform([Id])
                        person_name=str(tt[0])

                        if det == 10:
                            cam.release()
                            cv2.destroyAllWindows()
                            session['sid'] = results[0][1]  # Assuming ID is in the second column
                            session['name'] = results[0][2]  # Assuming Name is in the third column
                            session['email'] = results[0][3]  # Assuming Email is in the fourth column
                            flash(f"Welcome, {session['name']}", "success")  # Flash success message

                            return redirect(url_for('studenthome'))  # Redirect to the student home page  
                    cv2.putText(frame,str(person_name), (x, y + h),font, 1, (255, 255, 255), 2)
                
                cv2.imshow('im', frame)
                if (cv2.waitKey(1) == ord('q')):
                    break

               
                
    return render_template('studentlogin.html', form=form)  # Pass form object to the template


@app.route('/studenthome')
def studenthome():
    return render_template('studenthome.html')



@app.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    form = LoginForm()  # Initialize the form

    if form.validate_on_submit():  # Only proceed if the form is submitted and valid
        username = form.username.data
        password = form.password.data

        # Perform your authentication logic here (use parameterized queries to prevent SQL injection)
        sql = "SELECT * FROM faculty_registration WHERE username=%s"
        cursor.execute(sql, (username,))  # Use tuple for parameterized query
        results = cursor.fetchall()
        print("sql_information:", results)

        if not results:
            flash("Invalid Username / Password", "danger")
            return redirect(url_for('faculty_login'))

        # Assuming the password is stored in plain text in the database (not hashed)
        stored_password = results[0][5]  # Assuming the password is in the 6th column (index 5)

        # Compare the entered password with the stored plain-text password
        if stored_password == password:
            session['fid'] = results[0][0]  # Assuming faculty ID is in the first column (index 0)
            session['name'] = results[0][1]  # Assuming faculty name is in the second column (index 1)
            session['email'] = results[0][2]  # Assuming faculty email is in the fourth column (index 3)
            session['username'] = username  # Assuming faculty email is in the fourth column (index 3)
            flash("Welcome, " + results[0][1], "success")  # Display faculty name
            return redirect(url_for('faculty_home'))  # Redirect to faculty home page
        else:
            flash("Invalid Username / Password", "danger")
            return redirect(url_for('faculty_login'))

    return render_template('faculty_login.html', form=form)  # Return the login page if form is not submitted
            

@app.route('/studentlogin', methods=['GET','POST'])
def student():
    pass

# Admin Home Route
@app.route('/adminhome', methods=['GET','POST'])
def adminhome():
    # adminlogout = 'admin_logged_in' in session
    # flash("Welcome Admin", "success")
    return render_template('adminhome.html')

# Admin Home Route
@app.route('/faculty_home', methods=['GET','POST'])
def faculty_home():
    # adminlogout = 'admin_logged_in' in session
    # flash("Welcome Faculty", "success")
    return render_template('faculty_home.html')





@app.route('/adminlogout')
def adminlogout():
    # Logic for logging out the admin (e.g., clearing session or cookies)
    flash("Successfully logged out", "success")
    return redirect(url_for('adminlogin'))


@app.route('/view_registrations')
def view_registrations():
    sql = "select * from user_registration  "
    x = pd.read_sql_query(sql, mydb)
    x = x.drop(['pwd'], axis=1)

    return render_template('view_registrations.html', row_val=x.values.tolist())


@app.route('/training', methods=['POST', 'GET'])
def training():
    le = LabelEncoder()
    faces, Id = getImagesAndLabels("TrainingImage")
    Id = le.fit_transform(Id)
    output = open('label_encoder.pkl', 'wb')
    pickle.dump(le, output)
    output.close()
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(Id))
    recognizer.save("Trained_Model/Trainner.yml")
    flash("Model Trained Successfully", "success")
    return render_template('adminhome.html')


def getImagesAndLabels(path):
    imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
    faces = []
    Ids = []
    for imagePath in imagePaths:
        if imagePath.endswith(".jpg") is False:
            continue
        pilImage = Image.open(imagePath).convert('L')
        imageNp = np.array(pilImage, 'uint8')
        Id = str(os.path.split(imagePath)[-1].split(".")[0])
        faces.append(imageNp)
        Ids.append(Id)
    return faces, Ids


@app.route('/add_question', methods=["GET","POST"])
def add_question():
    return render_template('add_question.html')

@app.route('/qsnback', methods=["GET","POST"])
def qsnback():
    if request.method == 'POST':
        qsn = request.form['qsn']
        opt1 = request.form['opt1']
        opt2 = request.form['opt2']
        opt3 = request.form['opt3']
        opt4 = request.form['opt4']
        ans = request.form['ans']
        sub = request.form['sub']
        
        # For exam_paper table, we assume 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'hh', and 'i' are the columns.
        # You might need to adjust the data being inserted based on your specific requirement.
        # Here, I will assume you want to store the question and options in the 'b', 'c', 'd', 'e', 'f' columns.
        # Adjust this part based on your table's requirements.

        a = '1'  # Just a placeholder, update as necessary
        b = qsn  # The question text
        c = opt1  # Option 1
        d = opt2  # Option 2
        e = opt3  # Option 3
        f = opt4  # Option 4
        g = ans   # The correct answer (this is just an example; adapt based on your needs)

        # Insert into qsn_ans table
        sql_qsn_ans = "INSERT INTO qsn_ans(qsn,opt1,opt2,opt3,opt4,ans,username,subject) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        val_qsn_ans = (qsn, opt1, opt2, opt3, opt4, ans, session['username'],sub)
        cursor.execute(sql_qsn_ans, val_qsn_ans)
        mydb.commit()

        flash("Question added", "info")
        return render_template('add_question.html')
    
    return render_template('add_question.html')


@app.route('/view_questions')
def view_questions():
    # email=session.get('email')
    sql = "select * from qsn_ans "
    x = pd.read_sql_query(sql, mydb)
    x = x.drop(['id'], axis=1)
    return render_template('viewqsn.html', row_val=x.values.tolist())

@app.route('/viewqsn_faculty')
def viewqsn_faculty():
    # email=session.get('email')
    sql = "select hh,i from exam_paper where username='"+session['username']+"' order by id desc limit 1"
    x = pd.read_sql_query(sql, mydb)
    return render_template('viewqsn_faculty.html', row_val=x.values.tolist())

@app.route('/view_papers/<exam>')
def view_papers(exam):
    sql = "select * from exam_paper where username='"+session['username']+"' and hh='"+exam+"' order by id desc"
    x = pd.read_sql_query(sql, mydb)
    x = x.drop(['id'], axis=1)
    return render_template('view_papers.html', row_val=x.values.tolist())






@app.route('/create_exam_back', methods=["POST", "GET"])
def create_exam_back():
    if request.method == 'POST':
        exam_name = request.form['exam_name']  
        exam_date = request.form['exam_date']
        sub = request.form['course_code']
        # Select random questions from the database
        s = "SELECT * FROM qsn_ans where username='"+session['username']+"' and subject='"+sub+"' ORDER BY RAND()"
        questions = pd.read_sql_query(s, mydb)

        print(len(questions))
        v = len(questions)

        # Insert the exam paper data into the database
        for i in range(v):
            sql = """
            INSERT INTO exam_paper (a, b, c, d, e, f, g, hh, i, username) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                questions.values[i][0], questions.values[i][1], questions.values[i][2],
                questions.values[i][3], questions.values[i][4], questions.values[i][5],
                questions.values[i][6], exam_name, exam_date, session['username']
            ))
        mydb.commit()
        flash("Exam paper created successfully!", "success")
        return redirect(url_for('create_exam_back'))  # Redirect to avoid form resubmission
    
    data_query = "select subject from qsn_ans where username = '"+session['username']+"' group by subject"
    data = pd.read_sql_query(data_query, mydb)
    return render_template('create_exam.html', data=data.values.tolist())



@app.route('/view_exam')
def view_exam():
    mydb.cursor().execute('set sql_mode=""')
    sql = "SELECT * FROM exam_paper WHERE i >= CURRENT_DATE() GROUP BY hh"
    x = pd.read_sql_query(sql, mydb)
    x = x.drop(['a', 'b', 'c', 'd', 'e', 'f', 'g'], axis=1)
    
    # Add an index to each row
    x['index'] = range(1, len(x) + 1)
    
    # Pass the data to the template
    return render_template('view_exam.html', row_val=x.to_dict(orient='records'))


def TrackImages():
    global val_data, global_stop , head_status,cam
    head, label = live_webcam_detection()
    val_data = label
    head_status = head

# Route for live webcam feed
def gen_frames():
    camera = cv2.VideoCapture(0)  # Use the default webcam
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/take_test/<s>/<s1>/<s2>')
def take_test(s=0, s1="", s2=""):
    sid=session.get("sid")
    s="select count(*) from results where sid='"+str(sid)+"' and ename='"+str(s1)+"' and edate='"+str(s2)+"' "
    y=pd.read_sql_query(s,mydb)
    count=y.values[0][0]
    
    if count==0:
        sql = "select * from exam_paper where hh='" + s1 + "' and i='" + s2 + "'"
        x = pd.read_sql_query(sql, mydb)
        ans = x['g']
        # x=x.drop(['id','a','hh','g','hh','i'],axis=1)
        row1 = len(x.values.tolist())
        # print(x)
        dd = row1
        global tt, cam

        t1 = threading.Thread(target=TrackImages)
        t1.start()
        return render_template("take_test.html", s=s, s1=s1, s2=s2, row_val=x.values.tolist(), r1=row1, a=ans)
    else:
        flash("You have already attempted the exam","warning")
        return render_template("view_exam.html")


@app.route('/textback', methods=['GET','POST'])
def textback():
    # Initialize camera at the start if needed
    if request.method == 'POST':
        lenn = request.form['dpr']
        s1 = request.form['s1']
        s2 = request.form['s2']
        sid = session.get('sid')
        email = session.get('email')
        name = session.get('name')

        # Check if cam is initialized before calling release()
        if 'cam' in globals() and cam.isOpened():
            cam.release()
            cv2.destroyAllWindows()

        # val_data = "some_value"  # You should compute or assign this based on your logic

        for ss in range(0, int(lenn)):
            sss = "myans" + str(ss)
            ca = "currans" + str(ss)

            ca1 = request.form[ca]
            sss1 = request.form[sss]

            # Insert query using val_data
            sql = "INSERT INTO results(sid, sname, semail, ename, edate, ca, ua, status,head_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            print(sql)
            cursor.execute(sql , (str(sid), str(name), str(email), str(s1), str(s2), str(ca1), str(sss1), val_data,head_status))
            mydb.commit()

        # Insert into finalresults using val_data
        sql1 = "INSERT INTO finalresults(sid, semail, ename, edate, ca, ua, status , head_status) VALUES ('" + str(sid) + "','" + str(email) + "','" + str(s1) + "','" + str(s2) + "',(SELECT count(*) FROM results WHERE ca = ua AND sid = '" + str(sid) + "' AND ename = '" + str(s1) + "' AND edate = '" + str(s2) + "'),(SELECT count(*) FROM results WHERE sid = '" + str(sid) + "' AND ename = '" + str(s1) + "' AND edate = '" + str(s2) + "'),'" + str(val_data) + "','" + str(head_status) + "')"
        print(sql1)
        cursor.execute(sql1)
        mydb.commit()

        flash("Your answers submitted. Exam Completed!", "warning")

    return render_template("view_exam.html")



@app.route('/exam_results')
def exam_results():
    mydb.cursor().execute('set sql_mode=""')
    sql = "SELECT * FROM exam_paper GROUP BY hh order by id desc"
    x = pd.read_sql_query(sql, mydb)
    x = x.drop(['a', 'b', 'c', 'd', 'e', 'f', 'g'], axis=1)
    print(x.values.tolist())  # Debug output
    return render_template('exam_results.html', row_val=x.values.tolist())


@app.route('/exam_results_back')
def exam_results_back():
    s = request.args.get('s', default=0, type=int)
    s1 = request.args.get('s1', default="", type=str)
    s2 = request.args.get('s2', default="", type=str)
    
    if not s1 or not s2:
        return "Invalid parameters", 400
    
    sq = "SELECT * FROM finalresults WHERE ename=%s AND edate=%s"
    x = pd.read_sql_query(sq, mydb, params=(s1, s2))
    return render_template("exam_results1.html", row_val=x.values.tolist())



@app.route('/reply_mail/<s>/<s1>/<s2>/<s3>/<s4>/')
def reply_mail(s=0, s1="", s2="",s3="",s4=""):
    if s4=="Cell Phone":
        msg = 'Cell Phone detected in the exam hall. Please do not use any electronic devices during the exam.'
        t = 'Regards,'
        t1 = 'Online Student Examination System.'
        mail_content = f'Dear {s},\n\n{msg}\n\n{t},\n{t1}'
    else:
        msg = 'You are authenticated and you can view your results'
        t = 'Regards,'
        t1 = 'Online Student Examination System.'
        mail_content = f'Dear {s},\n\n{msg}\n\n{t},\n{t1}'

    send_mail("Exam Results", s2, mail_content)
    return render_template("exam_results1.html")

@app.route('/view_result')
def view_result():
    sid = session.get('sid')

    sq = "SELECT * FROM finalresults WHERE sid='" + str(sid) + "' AND status != 'Cell Phone'"
    x = pd.read_sql_query(sq, mydb)

    # Drop the unnecessary columns
    x = x.drop(['id', 'sid', 'semail', 'status'], axis=1)

    # Convert the DataFrame into a list of dictionaries
    data = x.to_dict(orient='records')

    return render_template("view_result.html", row_val=data)

# Set up Google API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# Assuming genai is configured properly
import google.generativeai as genai
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-flash-latest')

def generate_mcqs(text, number, tone):
    print("===========")
    
    print(GOOGLE_API_KEY)
    prompt = f"""
    Text: {text}
    
    You are an expert MCQ maker. Given the above text, create a quiz of {number} multiple choice questions in {tone} tone.
    Format like the example:
    
    1: Question?
    a) Option 1
    b) Option 2
    c) Option 3
    d) Option 4
    Correct answer: x
    """
    
    for attempt in range(3):  # Retry up to 3 times
        try:
            response = model.generate_content(prompt)
            quiz = response.text
            
            # Parse generated quiz
            mcqs = quiz.split('\n\n')
            quiz_data = []
            answer_key = {}
            for mcq in mcqs:
                lines = mcq.split('\n')
                if len(lines) < 5:
                    continue
                question = lines[0].strip()
                options = {chr(ord('a') + i): line[3:].strip() for i, line in enumerate(lines[1:5])}
                correct = lines[5][14:].strip()
                quiz_data.append({"Question": question, "Options": options})
                answer_key[question] = correct
                
            return quiz_data, answer_key
        
        except Exception as e:
            if "500" in str(e):
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                return None, None
    
    return None, None
# def parse_question(question_str):
#     # Make sure question_str is a string
#     if not isinstance(question_str, str):
#         print(f"Invalid input: {question_str}")
#         return None

#     # Regex to separate the question from the options
#     match = re.match(r"\*\*(\d+):\s*(.*?)\*\*\s*a\) (.*?)\nb\) (.*?)\nc\) (.*?)\nd\) (.*)", question_str, re.DOTALL)
    
#     if match:
#         question = match.group(2)  # Extract the question
#         opt1 = match.group(3)      # Option a
#         opt2 = match.group(4)      # Option b
#         opt3 = match.group(5)      # Option c
#         opt4 = match.group(6)      # Option d
#         return question, opt1, opt2, opt3, opt4
#     else:
#         print(f"Failed to parse: {question_str}")
#     return None  # If no match found
# Function to parse the dictionary-based quiz data
def parse_question_data(quiz_entry):
    # Extracting the question and options from the dictionary
    question = quiz_entry['Question']
    options = quiz_entry['Options']
    
    # Ensure options are correctly extracted, defaulting to empty string if missing
    opt1 = options.get('a', '')
    opt2 = options.get('b', '')
    opt3 = options.get('c', '')
    opt4 = options.get('d', '')
    
    return question, opt1, opt2, opt3, opt4

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if request.method == "POST":
        text = None
        file = request.files["file"]
        sub = request.form["sub"]
        txt = request.form["txt"]
        number_of_questions = int(request.form["number_of_questions"])
        tone = request.form["tone"]

        
        # File or URL or Text Area content retrieval
        if file:
            text = file.read().decode("utf-8")
        elif txt:
            text = txt

        # Generate MCQs
        quiz_data, answer_key = generate_mcqs(text, number_of_questions, tone)
        print(answer_key)
        if quiz_data:
            session['quiz_data'] = quiz_data
            session['answer_key'] = answer_key
            for i, quiz_entry in enumerate(quiz_data):
                parsed_data = parse_question_data(quiz_entry)
                
                if parsed_data:
                    question, opt1, opt2, opt3, opt4 = parsed_data
                    answer = answer_key[question]
                    answer = answer.split(' ')[-1]  # Extract the answer from the string
                    print(answer)
                    cursor.execute('''
                    INSERT INTO qsn_ans (qsn, opt1, opt2, opt3, opt4, ans, username, subject)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    ''', (question, opt1, opt2, opt3, opt4, answer, session['username'], sub))
            mydb.commit()
            print("data stored successfully")
            return render_template("add_question2.html", quiz_data=quiz_data)
            

        else:
            flash("Failed to generate MCQs.")
            return redirect(url_for("prediction"))

    return render_template("add_question2.html")

@app.route("/download/<format>")
def download(format):
    quiz_data = session.get("quiz_data", [])
    answer_key = session.get("answer_key", {})

    if format == "pdf":
        pdf_file = SimpleDocTemplate('mcqs.pdf', pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        for mcq in quiz_data:
            elements.append(Paragraph(mcq['Question'], styles['Heading1']))
            for option, text in mcq['Options'].items():
                elements.append(Paragraph(f"{option}) {text}", styles['Normal']))
            elements.append(Paragraph("", styles['Normal']))

        pdf_file.build(elements)
        return send_file("mcqs.pdf", as_attachment=True)

    elif format == "word":
        document = Document()
        for mcq in quiz_data:
            document.add_heading(mcq['Question'], level=1)
            for option, text in mcq['Options'].items():
                document.add_paragraph(f"{option}) {text}")
            document.add_paragraph()

        document.save("mcqs.docx")
        return send_file("mcqs.docx", as_attachment=True)

    elif format == "answer_key":
        answer_key_doc = Document()
        answer_key_doc.add_heading("Answer Key", level=1)
        for question, answer in answer_key.items():
            answer_key_doc.add_paragraph(f"{question} - Correct answer: {answer}")

        answer_key_doc.save("answer_key.docx")
        return send_file("answer_key.docx", as_attachment=True)

    return redirect(url_for("results"))

if __name__ == '__main__':
    app.run(debug=True , host='0.0.0.0')
