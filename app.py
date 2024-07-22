from datetime import datetime, timedelta
from flask import Flask, render_template, url_for, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
import bcrypt
import logging
import random
from flask_mail import Mail, Message

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_POER'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jntd8025@gmail.com'
app.config['MAIL_PASSWORD'] = 'ekje xkkq bvzg hfoo'
app.config['MAIL_USE_SSL'] = False

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=4)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1234@localhost/tbs'
app.secret_key = 'your_secret_key'

db = SQLAlchemy(app)
mail=Mail(app)


class Registration(db.Model):
    
    sno = db.Column(db.Integer, primary_key=True, nullable=False)
    fname = db.Column(db.String(32), nullable=False)
    lname = db.Column(db.String(32), nullable=False)
    date_of_birth = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(32), nullable=False)
    repassword = db.Column(db.String(32), nullable=False)
    mobile = db.Column(db.String(32), nullable=False, unique=True)
    license = db.Column(db.String(32), nullable=False, default='User')
    gender = db.Column(db.String(32), nullable=False)

class Bookings(db.Model):
    booking_id = db.Column(db.Integer, nullable=False, primary_key=True,)
    pickup_address = db.Column(db.String(32), nullable=False)
    date = db.Column(db.String(32), nullable=False)
    time = db.Column(db.String(32), nullable=False)
    dropoff_address = db.Column(db.String(32), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('registration.sno'), nullable=False,)
    user = db.relationship('Registration', backref = db.backref('bookings', lazy=True))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    driver_name = db.Column(db.String(32), nullable=False,)
    driver_phone = db.Column(db.String(32), nullable=False,)
    status = db.Column(db.String(32), nullable=False, default='Pending')



@app.route("/register", methods = ['GET', 'POST'])
def register():

    if(request.method=='POST'):
        fname =  request.form.get('fname')
        lname =  request.form.get('lname')
        date_of_birth = request.form.get('dob')
        email =  request.form.get('email')
        password =  request.form.get('password')
        repassword =  request.form.get('repassword')
        mobile =  request.form.get('mobile')
        license =  request.form.get('license')
        gender =  request.form.get('gender')
        
        if password != repassword:
            flash('Password do not match!!')
            return render_template('register.html', fname = fname, lname = lname, date_of_birth = date_of_birth, email = email, mobile = mobile, license=license, gender=gender)
        
        existing_user = Registration.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists! Please use a different email .', 'error')
            return render_template('register.html', fname = fname, lname = lname, date_of_birth = date_of_birth, mobile = mobile, license=license, gender=gender)

        existing_user = Registration.query.filter_by(mobile=mobile).first()
        if existing_user:
            flash('Mobile number already exists! Please use a different mobile number .', 'error')
            return render_template('register.html', fname = fname, lname = lname, date_of_birth = date_of_birth, email = email, license=license, gender=gender)
        
        session['registration_data'] = {
            'fname': fname,
            'lname': lname,
            'date_of_birth': date_of_birth,
            'email': email,
            'password': password,
            'repassword': repassword,
            'mobile': mobile,
            'license': license,
            'gender': gender
        }
        session['otp'] = random.randint(1000,9999)
        msg = Message('OTP', sender='jntd8025@gmail.com', recipients=[email])
        msg.body = 'Hi ' + fname +" "+ lname + '\nYour Email OTP is: '+ str(session['otp'])
        mail.send(msg)
        flash('OTP Sent to your entered email.')
        return redirect(url_for('verify_email'))

    return render_template('register.html')

@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    
    if request.method=='POST':
        get_otp = request.form['otp']
        if 'otp' in session and session['otp']==int(get_otp):
            flash('Email Verified.')
            reg_data = session['registration_data']
            if reg_data:
                hashed_password = bcrypt.hashpw(reg_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                entry = Registration(
                    fname=reg_data['fname'],
                    lname=reg_data['lname'],
                    date_of_birth=reg_data['date_of_birth'],
                    email=reg_data['email'],
                    password=hashed_password,
                    repassword=reg_data['repassword'],
                    mobile=reg_data['mobile'],
                    license=reg_data['license'],
                    gender=reg_data['gender']
                )
                try:
                    db.session.add(entry)
                    db.session.commit()
                    flash('Registration Successful. Thank You!', 'success')
                    session.pop('otp', None)
                    session.pop('registration_data', None)
                    session.pop('otp_sent', None)
                    return redirect(url_for('login'))
                except Exception as e:
                    db.session.rollback()
                    flash('Registration failed. Please try again later.', 'error')
            else:
                flash('Registration data is missing. Please try registering again.', 'error')
                return redirect(url_for('register'))
        else:
            flash('Invalid OTP!')
            return render_template('verify_email.html', email=session.get('registration_data', {}).get('email'))
        
    return render_template('verify_email.html', email=session.get('registration_data', {}).get('email'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    admin = {'admin@admin.com':'admin'}

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email in admin and admin[email] == password:
            session['email'] = email
            session.permanent=True
            return redirect(url_for('admin'))
        else:
            user = Registration.query.filter_by(email=email).first()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                session['email'] = user.email
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Invalid user!!')

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'email' not in session:

        flash('Login first!')
        return redirect(url_for('login'))
    
    user = Registration.query.filter_by(email=session['email']).first()

    if user is None:
        flash('User not found!', 'error')
        return redirect(url_for('login'))
    
    if request.method=='POST':
        pickup_address = request.form.get('pickup_address')
        pickup_date = request.form.get('pickup_date')
        pickup_time = request.form.get('pickup_time')
        dropoff_address = request.form.get('dropoff_address')

        pickup_datetime_str = f"{pickup_date} {pickup_time}"
        pickup_date_time = datetime.strptime(pickup_datetime_str, '%Y-%m-%d %H:%M')

        if pickup_date_time < datetime.now():
            flash('Booking cannot be in past!', 'error')
            return render_template('dashboard.html', user=user, pickup_address = pickup_address, date = pickup_date, time = pickup_time, dropoff_address = dropoff_address)
        else:
            entry = Bookings(pickup_address = pickup_address, date = pickup_date, time = pickup_time, dropoff_address = dropoff_address, user_id=user.sno, created_at=datetime.now(),driver_name='--', driver_phone='--', status='Pending' )

            db.session.add(entry)
            db.session.commit()
            flash('Booking Successful!')

        user_bookings = Bookings.query.filter_by(user_id=user.sno).order_by(desc(Bookings.booking_id)).all()
    else:
        user_bookings = Bookings.query.filter_by(user_id=user.sno).order_by(desc(Bookings.booking_id)).all()


    return render_template('dashboard.html', user=user, bookings=user_bookings)

@app.route('/editform/<int:booking_id>', methods=['GET', 'POST'])
def editform(booking_id):
    if 'email' not in session:

        flash('Login first!')
        return redirect(url_for('login'))
    bookings = Bookings.query.get_or_404(booking_id)

    return render_template('editform.html', bookings=bookings)

@app.route('/update/<booking_id>', methods=['GET', 'POST'])
def update(booking_id):
    booking = Bookings.query.get_or_404(booking_id)
    user = Registration.query.filter_by(email=session.get('email')).first()

    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('login'))

    if request.method=='POST':
        booking.pickup_address = request.form.get('pickup_address')
        booking.date = request.form.get('pickup_date')
        booking.time = request.form.get('pickup_time')
        booking.dropoff_address = request.form.get('dropoff_address')
        booking.driver_name = '--'
        booking.driver_phone = '--'
        booking.status = 'Pending'

        pickup_datetime_str = f"{booking.date} {booking.time}"
        pickup_date_time = datetime.strptime(pickup_datetime_str, '%Y-%m-%d %H:%M')

        if pickup_date_time < datetime.now():
            flash('Booking cannot be in past!', 'error')
        else:
            try:
                db.session.commit()
                flash('Booking updated successfully!')
                return redirect(url_for('dashboard'))
            except Exception as e:
                db.session.rollback()  # Rollback the session in case of error
                flash('Error updating booking: ' + str(e), 'error')
    
    return render_template('dashboard.html', user=user, booking=booking)

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('Logout Successfully.')
    return redirect('/login')

@app.route("/admin", methods=['GET', 'POST'])
def admin():
    if 'email' in session:
        staffs = Registration.query.filter(Registration.license != 'User').count()
        users = Registration.query.filter(Registration.license == 'User').count()
        bookings = Bookings.query.filter(Bookings.booking_id).count()
        if session['email'] == 'admin@admin.com':
            return render_template('admin.html', staffs=staffs, users=users, bookings=bookings)
        else:
            flash('Access denied. Admin only!')
            return redirect(url_for('dashboard'))
    else:
        flash('Access denied. Login First!')
        return redirect(url_for('login'))

@app.route("/bookings", methods=['GET', 'POST'])
def bookings():
    if 'email' in session:
        if session['email'] == 'admin@admin.com':
            bookings = Bookings.query.order_by(desc(Bookings.booking_id)).all()
            staffs = Registration.query.filter(Registration.license != 'User').all()

            return render_template('bookings.html', bookings=bookings, staffs=staffs)
        else:
            flash('Access denied. Admins only!')
            return redirect(url_for('dashboard'))
    else:
        flash('Access denied. Login first!')
        return redirect(url_for('login'))

@app.route("/users", methods=['GET', 'POST'])
def users():
    if 'email' in session:
        if session['email'] == 'admin@admin.com':
            users = Registration.query.filter_by(license='User').order_by(desc(Registration.sno)).all()
            return render_template('users.html', users=users)
        else:
            flash('Access denied. Admins only!')
            return redirect(url_for('dashboard'))
    else:
        flash('Access denied. Login first!')
        return redirect(url_for('login'))

@app.route("/staffs", methods=['GET', 'POST'])
def staffs():
    if 'email' in session:
        if session['email'] == 'admin@admin.com':
            staffs = Registration.query.filter(Registration.license != 'User').order_by(desc(Registration.sno)).all()
            return render_template('staffs.html', staffs=staffs)
        else:
            flash('Access denied. Admins only!')
            return redirect(url_for('dashboard'))
    else:
        flash('Access denied. Login first!')
        return redirect(url_for('login'))

@app.route('/assign_driver/<int:booking_id>', methods=['GET', 'POST'])
def assign_driver(booking_id):
    if 'email' not in session:

        flash('Login first!')
        return redirect(url_for('login'))
        
    booking = Bookings.query.get_or_404(booking_id)
    driver_name = request.form.get('assign_driver')

    driver_fname, driver_lname = driver_name.split()

    driver = Registration.query.filter_by(fname=driver_fname, lname=driver_lname).first()

    if driver:
        booking.driver_name = driver_name
        booking.driver_phone = driver.mobile
        booking.status = 'Booking Confirmed'
        
        db.session.commit()
        flash('Driver assigned successfully.')
    else:
        flash('Error assigning driver', 'error')
        return redirect(url_for('bookings'))

    return render_template('bookings.html')

@app.route("/user-registration", methods=['GET', 'POST'])
def uregistration():
    if(request.method=='POST'):
        fname =  request.form.get('fname')
        lname =  request.form.get('lname')
        date_of_birth = request.form.get('dob')
        email =  request.form.get('email')
        password =  request.form.get('password')
        repassword =  request.form.get('repassword')
        mobile =  request.form.get('mobile')
        license = request.form.get('license')
        gender =  request.form.get('gender')
        
        if password != repassword:
                flash('Password do not match!!')
                return render_template('user-registration.html', fname = fname, lname = lname, date_of_birth = date_of_birth, email = email, mobile = mobile, license=license, gender=gender)
        
        existing_user = Registration.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists! Please use a different email .', 'error')
            return render_template('user-registration.html', fname = fname, lname = lname, date_of_birth = date_of_birth, mobile = mobile, license=license, gender=gender)

        existing_user = Registration.query.filter_by(mobile=mobile).first()
        if existing_user:
            flash('Mobile number already exists! Please use a different mobile number .', 'error')
            return render_template('user-registration.html', fname = fname, lname = lname, date_of_birth = date_of_birth, email = email, license=license, gender=gender)
        
        session['registration_data'] = {
            'fname': fname,
            'lname': lname,
            'date_of_birth': date_of_birth,
            'email': email,
            'password': password,
            'repassword': repassword,
            'mobile': mobile,
            'license': license,
            'gender': gender
        }
        session['otp'] = random.randint(1000,9999)
        msg = Message('OTP', sender='jntd8025@gmail.com', recipients=[email])
        msg.body = 'Hi ' + fname +" "+ lname + '\nYour Email OTP is: '+ str(session['otp'])
        mail.send(msg)
        flash('OTP Sent to your entered email.')
        return redirect(url_for('verify_email'))

    
    return render_template('user-registration.html')

@app.route('/delete_booking/<int:booking_id>', methods=['POST'])
def delete_booking(booking_id):
    booking = Bookings.query.get_or_404(booking_id)
    
    try:
        db.session.delete(booking)
        db.session.commit()
        flash('Booking deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting booking: ' + str(e), 'error')
    
    if 'email' in session:
        user = Registration.query.filter_by(email=session['email']).first()
        if user:
            return redirect(url_for('dashboard'))

    return redirect(url_for('admin'))  # Redirect to the admin panel or wherever appropriate

@app.route('/delete_user/<int:sno>', methods=['POST'])
def delete_user(sno):
    user = Registration.query.get_or_404(sno)
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting booking: ' + str(e), 'error')
        
    return redirect(url_for('admin'))  # Redirect to the admin panel or wherever appropriate
@app.route('/delete_staff/<int:sno>', methods=['POST'])
def delete_staff(sno):
    staff = Registration.query.get_or_404(sno)
    
    try:
        db.session.delete(staff)
        db.session.commit()
        flash('Staff deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting booking: ' + str(e), 'error')
    
    return redirect(url_for('admin'))  # Redirect to the admin panel or wherever appropriate


@app.route("/")
def home():
    staffs = Registration.query.filter(Registration.license != 'User').count()
    users = Registration.query.filter(Registration.license == 'User').count()
    bookings = Bookings.query.filter(Bookings.booking_id).count()

    

    return render_template('index.html', staffs=staffs, bookings=bookings, users= users)

@app.route("/flight")
def flight():

    return render_template('flight.html')

@app.route("/train")
def train():
        
        return render_template('train.html')

@app.route("/hotels", methods=['GET', 'POST'])
def hotels():
        
        return render_template('hotels.html')

@app.route("/homestays")
def homestays():

    return render_template('homestays.html')

@app.route("/buses")
def buses():
    return render_template('buses.html')

@app.route("/cabs", methods=['GET', 'POST'])
def cabs():

    return render_template('cabs.html')
if __name__ == '__main__':
    app.run(debug=True)
