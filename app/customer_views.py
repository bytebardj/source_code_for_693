from app import app                    # Import the Flask application instance named 'app' from the 'app' module            
from flask import render_template      # Import necessary modules from Flask
from flask import request
from flask import redirect
from flask import url_for, jsonify
from flask import session
from datetime import datetime          # Import datetime module for date and time manipulation
import mysql.connector                 # Import MySQL Connector module
import connect                         # Import the connect module containing database connection details
from flask_hashing import Hashing  
    # Import the Hashing class from Flask Hashing extension
import base64
from werkzeug.utils import secure_filename
import os
import re
from datetime import datetime, timedelta, date
from dateutil import relativedelta
import schedule
import time
from decimal import *
from flask_mail import Mail, Message



hashing = Hashing(app)  #create an instance of hashing
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta


mail = Mail(app)


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'



UPLOAD_FOLDER = 'app/static/assets/img'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser, \
    password=connect.dbpass, host=connect.dbhost, auth_plugin='mysql_native_password',\
    database=connect.dbname, autocommit=True)
    dbconn = connection.cursor()
    return dbconn


  
@app.route("/customer/dashboard")
def customer_dashboard():
    # Check if user is logged in
    if 'loggedin' in session:
        role = session.get('role')  # Get the user's role from the session
        cart = session.get('cart', {})
      
       
    
        # Redirect based on user's role
        if role == 4:  
            # Get the user's ID from the session
            user_id = session.get('user_id')

            # Get a cursor object to interact with the database
            cursor = getCursor()

            # Execute a SQL query to fetch the customer's details including depot_id
            cursor.execute('SELECT * FROM customers WHERE user_id = %s', (user_id,))
            customer_details = cursor.fetchone()

           

            # Execute a SQL query to fetch the customer's role 
            cursor.execute('''SELECT roles.role_name, CONCAT (customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                           FROM roles 
                           INNER JOIN users ON roles.role_id = users.role_id 
                           INNER JOIN customers ON customers.user_id = users.user_id 
                           WHERE users.user_id = %s''', (user_id,))
            customer_info = cursor.fetchone()

            if customer_details:
                # Extract depot_id from customer's details
                depot_id = customer_details[6]
                # Extract balance from customer's details
                balance = customer_details[8]

                # Execute a SQL query to fetch the location based on depot_id
                cursor.execute('SELECT location FROM depots WHERE depot_id = %s', (depot_id,))
                location_result = cursor.fetchone()

                if location_result:
                    location = location_result[0]
                else:
                    location = "Location not found"
                
                # Fetch payment methods
                cursor.execute('SELECT DISTINCT card_number, card_holder_name, expiry_date FROM payment_methods WHERE user_id = %s', (user_id,))
                payment_methods = cursor.fetchall()

                # Process payment methods to mask the card numbers
                for i, payment_method in enumerate(payment_methods):
                    card_number = payment_method[0]
                    masked_card_number = '**** **** **** ' + card_number[-4:]
                    payment_methods[i] = (masked_card_number, payment_method[1], payment_method[2])
                
                # Fetch the 3 most recent orders
                cursor.execute('''
                    SELECT 
                        orders.order_id,
                        orders.order_date,
                        ost.order_status_type_name AS delivery_status,
                        ROUND((SUM(order_lines.product_quantity * products.product_price * IFNULL(promotion_types.discount, 1)) + IFNULL(shippments.shippment_price, 0)), 2) AS total_amount
                    FROM 
                        orders 
                    LEFT JOIN (
                        SELECT 
                            order_id, 
                            MAX(order_status_type_id) AS latest_status_id 
                        FROM 
                            order_assignments 
                        GROUP BY 
                            order_id
                    ) oa ON orders.order_id = oa.order_id
                    LEFT JOIN order_status_types ost ON oa.latest_status_id = ost.order_status_type_id
                    LEFT JOIN order_lines ON order_lines.order_id = orders.order_id
                    LEFT JOIN products ON products.product_id = order_lines.product_id
                    LEFT JOIN promotion_types ON promotion_types.promotion_type_id = products.promotion_type_id
                    LEFT JOIN shippments ON shippments.shippment_id = orders.shippment_id
                    WHERE 
                        orders.user_id = %s
                    GROUP BY 
                        orders.order_id, orders.order_date, ost.order_status_type_name, shippments.shippment_price
                    ORDER BY 
                        orders.order_date DESC,
                        orders.order_id DESC
                    LIMIT 3
                ''', (user_id,))
                recent_orders = cursor.fetchall()


                # Fetch the 3 most recent news

                cursor.execute('''SELECT 
                                    news.news_id,
                                    news.title,
                                    news.publish_date,
                                    CONCAT(staff.given_name, ' ', staff.family_name) AS full_name
                                FROM 
                                    news
                                INNER JOIN 
                                    staff ON news.created_by = staff.user_id
                                WHERE 
                                    news.depot_id IN (0, %s)
                                ORDER BY 
                                    news.publish_date DESC,
                                    news.news_id DESC
                                LIMIT 3''', (customer_details[6],))
                recent_news = cursor.fetchall()

                cursor.execute('''SELECT subscription_records.*,
                                CONCAT(customers.title, " ", customers.given_name, " ", customers.family_name) as full_name, boxes.box_name
                                FROM subscription_records 
                                LEFT JOIN customers ON subscription_records.user_id = customers.user_id
                                LEFT JOIN products ON subscription_records.product_id = products.product_id
                                LEFT JOIN boxes ON products.SKU = boxes.SKU
                                WHERE subscription_records.subscription_status ='active' AND subscription_records.user_id = %s
                               ORDER BY subscription_records.record_id DESC
                               LIMIT 3
                               ;''', (user_id,))
                recent_subscription = cursor.fetchall()

                # Render the customer dashboard template with location data

                return render_template('customer-dashboard.html',recent_subscription=recent_subscription,  role=role, customer_details=customer_details, customer_info=customer_info, location=location, balance=balance, cart=cart, payment_methods=payment_methods, recent_orders=recent_orders, recent_news=recent_news)

            else:
                msg="Customer details not found"
                # Handle case where customer details are not found
                return render_template('error.html', msg=msg)
        else:
            # Redirect to the error page since the user's role doesn't match any predefined roles
            return redirect(url_for('error'))
    # User is not logged in redirect to home page
    return redirect(url_for('logout'))
  
@app.route('/customer/profileupdate',methods= ['get','post'])
def customer_profileupdate():
    role = session.get('role')
    user_id = session.get('user_id')
    cursor=getCursor()
    cart = session.get('cart', {})

    cursor.execute('''SELECT roles.role_name, CONCAT (customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                           FROM roles INNER JOIN users ON roles.role_id = users.role_id 
                           INNER JOIN customers ON customers.user_id = users.user_id 
                           WHERE users.user_id = %s''', (user_id,))
    customer_info = cursor.fetchone()
    if 'loggedin' in session and role == 4: 
        if request.method=='GET':
            msg=''

            cursor=getCursor()
            cursor.execute('select * from customers where user_id=%s',(user_id,))
            profileinfo= cursor.fetchone()
            cursor.execute("""SELECT pic FROM customers WHERE user_id = %s""", (user_id,))
            profile_image_url = cursor.fetchone()

            cursor=getCursor()
            cursor.execute('select * from depots')
            depot_all=cursor.fetchall()
            return render_template("customer-profile-update.html", location=session['location'][0], role=role, customer_info=customer_info,depot_all=depot_all,profileinfo=profileinfo,msg=msg,profile_image_url= profile_image_url, cart=cart)
        else:
            title = request.form['title']
            first_name = request.form['first_name']
            family_name = request.form['family_name']
            phone_number = request.form['phone']
            email = request.form['email']
            address = request.form['address']
            city=request.form['city']
            files = request.files.getlist('image1')

            cursor=getCursor()
            cursor.execute('select * from depots')
            depot_all=cursor.fetchall()

            if files:

                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        fixed_filepath = filepath.replace("\\","/")
                        file.save(fixed_filepath)

                        cursor = getCursor()
                        cursor.execute("UPDATE customers set title=%s,given_name=%s,family_name=%s,email=%s,customer_address=%s,city=%s,phone_number=%s,pic=%s where user_id=%s",(title,first_name,family_name,email,address,city,phone_number,fixed_filepath,user_id,))
                        cursor.execute("""SELECT pic FROM customers WHERE user_id = %s""", (user_id,))
    
                        profile_image_url = cursor.fetchone()
                        msg="Profile has been successfully updated!"

                        return redirect(url_for("customer_profile", msg=msg))

                    else: #if no pic uploaded, then no need to update image in database
                        cursor = getCursor()
                        cursor.execute("UPDATE customers set title=%s,given_name=%s,family_name=%s,email=%s,customer_address=%s,city=%s,phone_number=%s where user_id=%s",(title,first_name,family_name,email,address,city,phone_number,user_id,))
                        msg="Profile has been successfully updated!"

                        cursor.execute("""SELECT pic FROM customers WHERE user_id = %s""", (user_id,))
                        profile_image_url = cursor.fetchone()

                        return redirect(url_for("customer_profile", msg=msg))
    else:
            # Redirect to an error page or homepage if the user's role doesn't match the expected role
        return redirect(url_for('logout'))
    
@app.route("/customer/deleteimg")
def customer_deleteimg():
    cart = session.get('cart', {})
    cursor=getCursor()
    user_id = session['user_id']
    cursor.execute("""SELECT roles.role_name, CONCAT(customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                              FROM roles
                              INNER JOIN users ON roles.role_id = users.role_id 
                              INNER JOIN customers ON customers.user_id = users.user_id 
                              WHERE users.user_id = %s""", (user_id,))
    customer_info = cursor.fetchone()
    cursor.execute("update customers set pic=%s where user_id=%s",("app/static/assets/img/avatar.jpg",user_id,))
    msg="Image has been successfully deleted!"
    cursor=getCursor()
    cursor.execute('select * from depots')
    depot_all=cursor.fetchall()
    return render_template("customer-profile-update.html", location=session['location'][0], customer_info=customer_info,depot_all=depot_all,profileinfo="",msg=msg,profile_image_url='',cart=cart)



# @app.route("/customer/profile")
# def customer_profile():
#     cursor =  getCursor()
#     role = session.get('role_id')
#     #if 'loggedin' in session and role == 4:

  
#         #user_id = session['user_id']
     
#     cursor.execute("""select c.*,d.location, u.status from customers as c
#                            join depots as d
#                             on c.city=d.depot_id
#                             join users as u
#                             on u.user_id=c.user_id
#                             where c.user_id=%s
#                             """, (10,))

#     profile = cursor.fetchone()

#     cursor.execute("""SELECT pic FROM customers WHERE user_id = %s""", (10,))
#     profile_image_url = cursor.fetchone()
    
#     return render_template ('customer_profile.html', profile=profile, profile_image_url=profile_image_url)
    

#     # else:
#     #     return redirect(url_for('login'))
@app.route("/customer/profile")
def customer_profile():
    role = session.get('role')
    cart = session.get('cart', {})
    # Check if user is logged in
    if 'loggedin' in session and role==4:
        if request.args.get('msg'):
            msg = request.args.get('msg')
        else: 
            msg = ''
        user_id = session.get('user_id')
        cursor = getCursor()
        cursor.execute("""SELECT c.*, d.location, u.status FROM customers AS c
                            JOIN depots AS d ON c.city = d.depot_id
                            JOIN users AS u ON u.user_id = c.user_id
                            WHERE c.user_id = %s""", (user_id,))
        
        profile = cursor.fetchone()

        cursor.execute("""SELECT pic FROM customers WHERE user_id = %s""", (user_id,))
        profile_image_url = cursor.fetchone()

        # Fetch additional customer information to include in the context
        cursor.execute("""SELECT roles.role_name, CONCAT(customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                            FROM roles
                            INNER JOIN users ON roles.role_id = users.role_id 
                            INNER JOIN customers ON customers.user_id = users.user_id 
                            WHERE users.user_id = %s""", (user_id,))
        customer_info = cursor.fetchone()

        return render_template('customer_profile.html', location=session['location'][0], msg=msg, role=role, profile=profile, profile_image_url=profile_image_url, customer_info=customer_info,cart=cart)
        
        #else:
            # Redirect to an error page or homepage if the user's role doesn't match the expected role
        #    return redirect(url_for('error'))
    
    # If the user is not logged in, redirect to the homepage or login page
    return redirect(url_for('logout'))

@app.route('/customer/password_update', methods=['GET', 'POST'])
def customer_password_update():
    role = session.get('role')
    cart = session.get('cart', {})

    # Check if user is logged in
    if 'loggedin' not in session or session.get('role') != 4:
        return redirect(url_for('logout'))

    user_id = session['user_id']
    msg = ''
    
    # Establish database connection
    cursor = getCursor()

    # Fetch additional customer information to include for the use of extend base-dashboard.html
    cursor.execute("""SELECT roles.role_name, CONCAT(customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                        FROM roles
                        INNER JOIN users ON roles.role_id = users.role_id 
                        INNER JOIN customers ON customers.user_id = users.user_id 
                        WHERE users.user_id = %s""", (user_id,))
    customer_info = cursor.fetchone()

    if request.method == 'POST':
        old_password = request.form.get('oldPassword')
        new_password = request.form.get('newPassword')
        confirm_password = request.form.get('confirmPassword')

        # Fetch the old hashed password from the database
        cursor.execute('SELECT password_hashed FROM users WHERE user_id = %s', (user_id,))
        stored_password_hash = cursor.fetchone()[0]

        # Validate the old password
        if not hashing.check_value(stored_password_hash, old_password, salt='c639'):
            msg = 'Old password is incorrect!'
        elif not new_password or not confirm_password:
            msg = 'Please fill all the fields!'
        elif new_password != confirm_password:
            msg = 'New password and confirm password do not match!'
        elif not (len(new_password) >= 8 and re.search(r'[A-Z]', new_password) and re.search(r'\d', new_password)):
            msg = 'Password must be at least 8 characters long and contain an uppercase letter and a number.'
        else:
            hashed_new_password = hashing.hash_value(new_password, salt='c639')
            cursor.execute('UPDATE users SET password_hashed = %s WHERE user_id = %s', (hashed_new_password, user_id))
            msg = 'Password has been successfully updated!'
            return redirect(url_for('customer_profile',msg=msg,location=session['location'][0], role=role,customer_info=customer_info,cart=cart))  # Redirect to the customer profile page after successful update

    if not customer_info:
        return render_template('error.html', error="manager details not found")

    return render_template('customer_password_update.html', location=session['location'][0], msg=msg,customer_info=customer_info,cart=cart, role=role) 

    

@app.route('/customer/subscription', methods=['GET', 'POST'])
def customer_subscription():
    cart = session.get('cart', {})
        # Check if user is logged in
    today = date.today()

    if 'loggedin' in session:
        role = session.get('role')
        
        msg = ''
        # Redirect based on user's role
        if role == 4:  
            user_id = session['user_id']
            cursor=getCursor()
            cursor.execute("""SELECT roles.role_name, CONCAT(customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                              FROM roles
                              INNER JOIN users ON roles.role_id = users.role_id 
                              INNER JOIN customers ON customers.user_id = users.user_id 
                              WHERE users.user_id = %s""", (user_id,))
            customer_info = cursor.fetchone()

                #get available boxes info for that customer
            cursor.execute('select city from customers where user_id=%s',(user_id,))
            mydepot_id = cursor.fetchone()
                
            cursor.execute("""
                              select p.product_id,b.box_name,u.unit_name,p.depot_id,p.product_price from boxes as b 
                                join units as u on b.unit=u.unit_id
                                join products as p on b.SKU=p.SKU
                                 where p.depot_id=%s """,(mydepot_id[0],))
            all_box = cursor.fetchall()

            if request.method == 'GET':


                cursor.execute("""
                                select sr.record_id,sr.product_id,b.box_name,p.product_price,sr.quantity,sr.sub_type,sr.sub_date,sr.subscription_status 
                                from subscription_records as sr 
                                join products as p on sr.product_id=p.product_id
                                join boxes as b on b.SKU= p.SKU 
                                where user_id = %s""",(user_id,))
                my_sub = cursor.fetchall()

                my_sub_all =[]

                for sub in my_sub:
                    date1 = today
                    date2 = sub[6]
                            
                        # Calculate the difference between the two dates
                    difference = relativedelta(date2, date1)     
                    df= difference.days                      
                        
                    if sub[5] =='Weekly' and sub[7] != 'Cancelled':
                      
                        for i in range(1,8):
                            if (df +i) % 7 == 0:
                                sub_next_payday  = today + timedelta(days=i) 
                                my_sub_all.append((sub[0],sub[1],sub[2],sub[3],sub[4],sub[5],sub[6],sub[7],sub_next_payday))

                    elif sub[5] =='Biweekly'and sub[7] != 'Cancelled':

                        for i in range(1,15):
                            if (df +i) % 14 == 0:
                                sub_next_payday  = today + timedelta(days=i) 
                                my_sub_all.append((sub[0],sub[1],sub[2],sub[3],sub[4],sub[5],sub[6],sub[7],sub_next_payday))
                      
                    elif sub[5] =='Monthly'and sub[7] != 'Cancelled':
                        for i in range(1,31):
                            if (df +i) % 30 == 0:
                                sub_next_payday  = today + timedelta(days=i) 
                                my_sub_all.append((sub[0],sub[1],sub[2],sub[3],sub[4],sub[5],sub[6],sub[7],sub_next_payday))

                    else:
                        my_sub_all.append((sub[0],sub[1],sub[2],sub[3],sub[4],sub[5],sub[6],sub[7],''))


                return render_template('customer_subscription.html',all_box= all_box,customer_info=customer_info,my_sub_all=my_sub_all,location=session['location'][0], role=role, msg=msg,cart=cart)
            elif request.method == 'POST':
                new_subscription = request.form['subscriptiontype']
                record_id1 = request.form['record_id']
                box=request.form['box']

                cursor=getCursor()
                cursor.execute('update subscription_records set product_id=%s,sub_type=%s where record_id=%s',(box,new_subscription,record_id1,))


            #default info needed
                user_id = session['user_id']
                cursor=getCursor()
                cursor.execute("""SELECT roles.role_name, CONCAT(customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                                        FROM roles
                                        INNER JOIN users ON roles.role_id = users.role_id 
                                        INNER JOIN customers ON customers.user_id = users.user_id 
                                        WHERE users.user_id = %s""", (user_id,))
                customer_info = cursor.fetchone()
                cursor.execute("""
                                select sr.record_id,sr.product_id,b.box_name,p.product_price,sr.quantity,sr.sub_type,sr.sub_date,sr.subscription_status 
                                from subscription_records as sr 
                                join products as p on sr.product_id=p.product_id
                                join boxes as b on b.SKU= p.SKU 
                                where user_id = %s""",(user_id,))
                my_sub = cursor.fetchall()

                my_sub_all =[]

                for sub in my_sub:
                    date1 = today
                    date2 = sub[6]
                                        
                    # Calculate the difference between the two dates
                    difference = relativedelta(date2, date1)     
                    df= difference.days                      
                                    
                    if sub[5] =='Weekly' and sub[7] != 'Cancelled':
                                
                        for i in range(1,8):
                            if (df +i) % 7 == 0:
                                sub_next_payday  = today + timedelta(days=i) 
                                my_sub_all.append((sub[0],sub[1],sub[2],sub[3],sub[4],sub[5],sub[6],sub[7],sub_next_payday))

                    elif sub[5] =='Biweekly'and sub[7] != 'Cancelled':

                        for i in range(1,15):
                            if (df +i) % 14 == 0:
                                sub_next_payday  = today + timedelta(days=i) 
                                my_sub_all.append((sub[0],sub[1],sub[2],sub[3],sub[4],sub[5],sub[6],sub[7],sub_next_payday))
                                
                    elif sub[5] =='Monthly'and sub[7] != 'Cancelled':
                        for i in range(1,31):
                            if (df +i) % 30 == 0:
                                sub_next_payday  = today + timedelta(days=i) 
                                my_sub_all.append((sub[0],sub[1],sub[2],sub[3],sub[4],sub[5],sub[6],sub[7],sub_next_payday))

                    else:
                        my_sub_all.append((sub[0],sub[1],sub[2],sub[3],sub[4],sub[5],sub[6],sub[7],''))
                msg= 'You have successfully updated the subscription!'

                return render_template('customer_subscription.html',all_box=all_box,customer_info=customer_info,my_sub_all=my_sub_all,location=session['location'][0], role=role, msg=msg,cart=cart)




@app.route('/customer/cancelsubscription/<record_id1>')
def customer_cancelsubscription(record_id1):
    cart = session.get('cart', {})
    cursor=getCursor()
    cursor.execute('update subscription_records set subscription_status =%s where record_id =%s',('Cancelled',record_id1,))
    today = date.today()
    role = session.get('role')


#default info needed
    user_id = session['user_id']
    cursor=getCursor()
    cursor.execute("""SELECT roles.role_name, CONCAT(customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                              FROM roles
                              INNER JOIN users ON roles.role_id = users.role_id 
                              INNER JOIN customers ON customers.user_id = users.user_id 
                              WHERE users.user_id = %s""", (user_id,))
    customer_info = cursor.fetchone()
    msg = 'Your subscription has been cancelled'
    cursor.execute("""
                                select sr.record_id,sr.product_id,b.box_name,p.product_price,sr.quantity,sr.sub_type,sr.sub_date,sr.subscription_status 
                                from subscription_records as sr 
                                join products as p on sr.product_id=p.product_id
                                join boxes as b on b.SKU= p.SKU 
                                where user_id = %s""",(user_id,))
    my_sub = cursor.fetchall()

    my_sub_all =[]

    for sub in my_sub:
        date1 = today
        date2 = sub[6]
                            
        # Calculate the difference between the two dates
        difference = relativedelta(date2, date1)     
        df= difference.days                      
                        
        if sub[5] =='Weekly' and sub[7] != 'Cancelled':
                      
            for i in range(1,8):
                if (df +i) % 7 == 0:
                    sub_next_payday  = today + timedelta(days=i) 
                    my_sub_all.append((sub[0],sub[1],sub[2],sub[3],sub[4],sub[5],sub[6],sub[7],sub_next_payday))

        elif sub[5] =='Biweekly'and sub[7] != 'Cancelled':

            for i in range(1,15):
                if (df +i) % 14 == 0:
                    sub_next_payday  = today + timedelta(days=i) 
                    my_sub_all.append((sub[0],sub[1],sub[2],sub[3],sub[4],sub[5],sub[6],sub[7],sub_next_payday))

        elif sub[5] =='Monthly'and sub[7] != 'Cancelled':
            for i in range(1,31):
                if (df +i) % 30 == 0:
                    sub_next_payday  = today + timedelta(days=i) 
                    my_sub_all.append((sub[0],sub[1],sub[2],sub[3],sub[4],sub[5],sub[6],sub[7],sub_next_payday))
                      

        else:
            my_sub_all.append((sub[0],sub[1],sub[2],sub[3],sub[4],sub[5],sub[6],sub[7],''))


    return redirect(url_for('customer_subscription',msg=msg))

# http://localhost:5000/customer/rma - this will be the customer request return merchandise authorization (request refund) page
@app.route("/customer/rma", methods=['GET', 'POST'])
def return_authorization():
    # Get the database cursor
    cursor = getCursor()
    # Retrieve the user ID and role from the session
    user_id = session['user_id']
    role = session.get('role')
    cart = session.get('cart', {})
    # Check if the user is logged in and has the specific role (role == 4)
    if 'loggedin' in session and role == 4:
        if request.args.get('msg'):
            # Retrieve the message from the request arguments if it exists
            msg = request.args.get('msg')
        else: 
            msg = ''
        # Query customer information, including location and user status
        cursor.execute("""SELECT c.*, d.location, u.status FROM customers AS c
                          JOIN depots AS d ON c.city = d.depot_id
                          JOIN users AS u ON u.user_id = c.user_id
                          WHERE c.user_id = %s""", (user_id,))
        
        profile = cursor.fetchone()


        # Fetch additional customer information to include in the context
        cursor.execute("""SELECT roles.role_name, CONCAT(customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                          FROM roles
                          INNER JOIN users ON roles.role_id = users.role_id 
                          INNER JOIN customers ON customers.user_id = users.user_id 
                          WHERE users.user_id = %s""", (user_id,))
        customer_info = cursor.fetchone()

        # Query information on completed orders
        cursor.execute('''SELECT orders.*, payments.amount, ROUND(SUM(order_lines.product_quantity * products.product_price * IFNULL(promotion_types.discount, 1)), 2) AS total_product_cost
                FROM orders
                LEFT JOIN payments ON orders.payment_id = payments.payment_id
                LEFT JOIN (
                    SELECT 
                        order_id, 
                        MAX(order_status_type_id) AS max_order_status
                    FROM 
                        order_assignments
                    GROUP BY 
                        order_id
                ) AS order_status_subquery ON orders.order_id = order_status_subquery.order_id
                LEFT JOIN order_lines ON order_lines.order_id = orders.order_id
                LEFT JOIN products ON products.product_id = order_lines.product_id
                LEFT JOIN promotion_types ON promotion_types.promotion_type_id = products.promotion_type_id
                WHERE order_status_subquery.max_order_status = 4 AND orders.order_id NOT IN (SELECT order_id FROM return_authorization) AND orders.user_id = %s
                GROUP BY orders.order_id, orders.payment_id, payments.amount''', (user_id,))
        completed_order = cursor.fetchall()

        # Retrieve the selected order ID from the form, if it exists
        selected_order_id = request.form.get('selected_order_id', '')

        # If an order ID is selected, query the details of that order
        if selected_order_id:
            cursor.execute('''SELECT order_lines.order_id, order_lines.product_id, order_lines.product_quantity, products.SKU, 
                        COALESCE(product.product_name, boxes.box_name) AS product_name, ROUND(products.product_price * IFNULL(promotion_types.discount, 1), 2) AS actual_price, COALESCE(unit1.unit_name, unit2.unit_name) AS unit
                        FROM order_lines 
                        LEFT JOIN products on order_lines.product_id=products.product_id
                        LEFT JOIN product on products.SKU=product.SKU
                        LEFT JOIN boxes on products.SKU=boxes.SKU
                        LEFT JOIN units AS unit1 ON product.unit = unit1.unit_id
                        LEFT JOIN units AS unit2 ON boxes.unit = unit2.unit_id
                        LEFT JOIN promotion_types ON products.promotion_type_id = promotion_types.promotion_type_id
                        WHERE order_lines.order_id = %s;
                        ''', (selected_order_id,))
            order_detail = cursor.fetchall()
        else:
            order_detail = None
        # Render the return authorization template, passing the relevant context data
        return render_template('customer-return_authorization.html', order_detail=order_detail, completed_order=completed_order, selected_order_id=selected_order_id, location=session['location'][0], msg=msg, role=role, profile=profile, customer_info=customer_info, user_id=user_id,cart=cart)
    else:
        # If user is not logged in or doesn't have the required role, redirect to home page
        return redirect(url_for('logout'))
    
# http://localhost:5000/customer/return-form - this will be the customer return form page
@app.route("/customer/return-form", methods=['GET', 'POST'])
def return_form():
    cart = session.get('cart', {})
    # Get the database cursor
    cursor = getCursor()
    # Get the selected order ID from the form
    selected_order_id = request.form.get('selected_order_id')
    # Query the details of the selected order
    cursor.execute('''SELECT order_lines.order_id, order_lines.product_id, order_lines.product_quantity,
                       products.SKU, product.product_name, products.product_price, units.unit_name
                       FROM order_lines 
                       LEFT JOIN products on order_lines.product_id=products.product_id
                       LEFT JOIN product on products.SKU=product.SKU
                       LEFT JOIN units on product.unit=units.unit_id
                       WHERE order_lines.order_id = %s;''', (selected_order_id,))
    # Fetch all rows from the executed query
    order_detail = cursor.fetchall()
    # Get the return reason from the form
    return_reason = request.form.get('return_reason')
    # Get the current date
    nowdate = datetime.now()
    # Insert a new return authorization record
    cursor.execute('''INSERT INTO return_authorization (order_id, applied_date, return_status, return_reason) 
                      VALUES (%s, %s, "pending", %s);''', (selected_order_id, nowdate, return_reason))
    # Commit the transaction to the database
    connection.commit() 
    # Get the last inserted form ID from the return_authorization table
    cursor.execute('SELECT form_id FROM return_authorization ORDER BY form_id DESC LIMIT 1;')
    last_form_id_row = cursor.fetchone()
    last_form_id = last_form_id_row[0] 
    # Loop through each product in the order detail
    for detail in order_detail:
        product_id = detail[1]
        return_quantity = request.form.get(f'{product_id}')
        # If a return quantity is provided for the product, insert it into the return_form table
        if return_quantity:
            cursor.execute('''INSERT INTO return_form (form_id, product_id, return_quantity) 
                              VALUES (%s, %s, %s);''', (last_form_id, product_id, return_quantity))
            # Commit the transaction to the database
            connection.commit() 
    # Set a success message
    msg = 'Your refund request has been successfully submitted. We will take care of the rest!'
    # Redirect to the return_authorization view with the success message
    return redirect(url_for('return_authorization', msg=msg,cart=cart))

@app.route('/customer/request-status', methods=['GET', 'POST'])
def request_status():
    cart = session.get('cart', {})
    # Get the database cursor
    cursor = getCursor()
    # Retrieve the user ID and role from the session
    user_id = session['user_id']
    role = session.get('role')

    # Check if the user is logged in and has the specific role (role == 4)
    if 'loggedin' in session and role == 4:
        if request.args.get('msg'):
            # Retrieve the message from the request arguments if it exists
            msg = request.args.get('msg')
        else:
            msg = ''
        # Query customer information, including location and user status
        cursor.execute("""SELECT c.*, d.location, u.status FROM customers AS c
                          JOIN depots AS d ON c.city = d.depot_id
                          JOIN users AS u ON u.user_id = c.user_id
                          WHERE c.user_id = %s""", (user_id,))
        
        profile = cursor.fetchone()

        # Fetch additional customer information to include in the context
        cursor.execute("""SELECT roles.role_name, CONCAT(customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                          FROM roles
                          INNER JOIN users ON roles.role_id = users.role_id 
                          INNER JOIN customers ON customers.user_id = users.user_id 
                          WHERE users.user_id = %s""", (user_id,))
        customer_info = cursor.fetchone()
        
        if request.method == 'GET':
            user_id = session['user_id']
            status_filter = request.args.get('status_filter')
            
            if status_filter:
                cursor.execute('''SELECT * FROM return_authorization 
                                  LEFT JOIN orders ON return_authorization.order_id = orders.order_id
                                  WHERE orders.user_id = %s AND return_authorization.return_status = %s''', 
                               (user_id, status_filter))
            else:
                cursor.execute('''SELECT * FROM return_authorization 
                                  LEFT JOIN orders ON return_authorization.order_id = orders.order_id
                                  WHERE orders.user_id = %s''', 
                               (user_id,))
            list_request = cursor.fetchall()

            return render_template('customer-request_status.html', list_request=list_request, location=session['location'][0], msg=msg, role=role, profile=profile, customer_info=customer_info, user_id=user_id,cart=cart)
        else:
            form_id = request.form.get('form_id')
            cursor.execute('''SELECT return_authorization.*, customers.family_name, customers.given_name, return_form.*, products.*,
                              COALESCE(product.product_name, boxes.box_name) AS product_name, COALESCE(product.product_des, boxes.box_des) AS description,
                              ROUND(products.product_price * IFNULL(promotion_types.discount, 1), 2) AS actual_price
                              FROM return_authorization 
                              LEFT JOIN return_form ON return_authorization.form_id = return_form.form_id
                              LEFT JOIN orders ON return_authorization.order_id = orders.order_id
                              LEFT JOIN customers ON orders.user_id = customers.user_id
                              LEFT JOIN products ON return_form.product_id = products.product_id
                              LEFT JOIN product ON products.SKU = product.SKU
                              LEFT JOIN boxes ON products.SKU = boxes.SKU
                              LEFT JOIN promotion_types ON products.promotion_type_id = promotion_types.promotion_type_id
                              WHERE return_authorization.form_id = %s''', (form_id,))
            request_detail = cursor.fetchall()

            return render_template('customer-request_detail.html', request_detail=request_detail, location=session['location'][0], msg=msg, role=role, profile=profile, customer_info=customer_info, user_id=user_id,cart=cart)
    else:
        # If user is not logged in or doesn't have the required role, redirect to home page
        return redirect(url_for('logout'))
    
@app.route('/customer/orders', methods=['GET', 'POST'])
def customer_orders():
    msg = request.args.get('msg', '')
    role = session.get('role')
    user_id = session.get('user_id')
    cart = session.get('cart', {})
    cursor = getCursor()

    # Execute a SQL query to fetch the customer's role, full name, and profile picture
    cursor.execute('''SELECT roles.role_name, CONCAT(customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                       FROM roles 
                       INNER JOIN users ON roles.role_id = users.role_id 
                       INNER JOIN customers ON customers.user_id = users.user_id 
                       WHERE customers.user_id = %s''', (user_id,))
    customer_info = cursor.fetchone()  # Fetch the result of the query

    # Execute a SQL query to fetch all distinct order status types
    cursor.execute('''SELECT DISTINCT order_status_type_name FROM order_status_types''')
    order_status = [row[0] for row in cursor.fetchall()]  # Create a list of order status types
    if 'Pending' not in order_status:  # Add 'Pending' to the list if it's not already there
        order_status.append('Pending')

    # Check if the user is logged in and has the specific role (role == 4)
    if 'loggedin' in session and role == 4:
        if request.method == 'POST':  # Handle form submission
            searchinput = request.form.get('searchinput', '').strip()  # Get the search input from the form
            selected_order_status = request.form.get('order_status')  # Get the selected order status from the form
        else:  # Handle URL parameters
            searchinput = request.args.get('searchinput', '').strip()  # Get the search input from the URL
            selected_order_status = request.args.get('order_status')  # Get the selected order status from the URL

        sort_by = request.args.get('sort_by', 'order_date')  # Get the sorting column, default to 'order_date'
        reverse = request.args.get('reverse', 'False') == 'True'  # Determine if sorting should be in reverse order

        order_by_clause = f"ORDER BY {sort_by} {'DESC' if reverse else 'ASC'}"  # Construct the SQL ORDER BY clause

        # Construct the SQL query to fetch order details
        query = f'''SELECT 
                        orders.order_id,
                        orders.order_date,
                        GROUP_CONCAT(CONCAT(COALESCE(boxes.box_name, product.product_name), ' x ', order_lines.product_quantity) SEPARATOR ', ') AS product_details,
                        COALESCE(MAX(order_status_types.order_status_type_name), 'Pending') AS delivery_status,
                        SUM(order_lines.product_quantity * products.product_price) AS total_amount
                    FROM 
                        orders 
                        LEFT JOIN order_lines ON orders.order_id = order_lines.order_id
                        LEFT JOIN products ON order_lines.product_id = products.product_id
                        LEFT JOIN product ON products.SKU = product.SKU
                        LEFT JOIN order_status_types ON order_status_types.order_status_type_id = (
                            SELECT order_status_type_id 
                            FROM order_assignments 
                            WHERE order_assignments.order_id = orders.order_id
                            ORDER BY order_assignments.start_date DESC
                            LIMIT 1
                        )
                        LEFT JOIN payments ON payments.payment_id = orders.payment_id
                        LEFT JOIN boxes ON boxes.SKU = products.SKU
                    WHERE 
                        orders.user_id = %s'''

        params = [user_id]  # Initialize the parameters list with the user ID

        # Add a condition to the query if search input is provided
        if searchinput:
            query += ''' AND orders.order_id IN (
                            SELECT order_lines.order_id 
                            FROM order_lines 
                            LEFT JOIN products ON order_lines.product_id = products.product_id
                            LEFT JOIN product ON products.sku = product.sku
                            WHERE product.product_name LIKE %s)'''
            params.append(f'%{searchinput}%')  # Add the search input to the parameters list

        # Add a condition to the query if a specific order status is selected
        if selected_order_status:
            query += " AND COALESCE(order_status_types.order_status_type_name, 'Pending') = %s"
            params.append(selected_order_status)  # Add the selected order status to the parameters list

        query += f" GROUP BY orders.order_id, orders.order_date, payments.amount {order_by_clause} LIMIT 1000"  # Add GROUP BY and ORDER BY clauses to the query

        cursor.execute(query, params)  # Execute the query with the parameters
        orders = cursor.fetchall()  # Fetch all results

        order_details = []
        for order in orders:  # Loop through each order to fetch its details
            cursor.execute('''SELECT 
                                COALESCE(boxes.box_name, product.product_name) AS product_name,
                                products.product_price,
                                order_lines.product_quantity,
                                (order_lines.product_quantity * products.product_price) AS line_total
                            FROM 
                                order_lines
                                LEFT JOIN products ON products.product_id = order_lines.product_id
                                LEFT JOIN product ON products.SKU = product.SKU
                                LEFT JOIN boxes ON products.SKU = boxes.SKU
                            WHERE 
                                order_lines.order_id = %s''', (order[0],))
            order_lines = cursor.fetchall()  # Fetch all order lines for the current order
            order_details.append({
                'order_id': order[0],
                'order_date': order[1],
                'product_details': order[2],
                'delivery_status': order[3],
                'total_amount': order[4],
                'order_lines': order_lines
            })

        # Render the customer-orders.html template with the fetched data
        return render_template('customer-orders.html', location=session['location'][0], orders=order_details, role=role, customer_info=customer_info, order_status=order_status, searchinput=searchinput, selected_order_status=selected_order_status, msg=msg, sort_by=sort_by, reverse=reverse, cart=cart)
    else:
        return redirect('logout')  # Redirect to logout if the user is not logged in or doesn't have the specific role

@app.route('/customer/orders_<order_id>')
def customer_order_detail(order_id):
    msg = request.args.get('msg', '')
    role = session.get('role')
    user_id = session.get('user_id')
    cart = session.get('cart', {})
    cursor = getCursor()

    # Check if the user is logged in and has the specific role (role == 4)
    if 'loggedin' in session and role == 4:
        # Execute a SQL query to fetch the customer's role, full name, and profile picture
        cursor.execute("""SELECT roles.role_name, CONCAT (customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                           FROM roles 
                           INNER JOIN users ON roles.role_id = users.role_id 
                           INNER JOIN customers ON customers.user_id = users.user_id 
                           WHERE users.user_id = %s""", (user_id,))
        customer_info = cursor.fetchone()  # Fetch the result of the query

        # Execute a SQL query to fetch order details including status and total amount
        cursor.execute("""
                        SELECT 
                        orders.order_id,
                        orders.order_date,
                        COALESCE(ost.order_status_type_name, 'Pending') AS delivery_status,
                        payments.amount AS total_amount
                    FROM 
                        orders 
                        LEFT JOIN (
                            SELECT order_status_type_id, order_id 
                            FROM order_assignments 
                            WHERE order_id = %s
                            ORDER BY start_date DESC
                            LIMIT 1
                        ) latest_assignment ON orders.order_id = latest_assignment.order_id
                        LEFT JOIN order_status_types ost ON latest_assignment.order_status_type_id = ost.order_status_type_id
                        LEFT JOIN payments ON payments.payment_id = orders.payment_id
                    WHERE 
                        orders.order_id = %s
                       """, (order_id, order_id))
        theorder = cursor.fetchone()  # Fetch the result of the query

        # Execute a SQL query to fetch all order lines for the current order
        cursor.execute('''SELECT 
                            COALESCE(boxes.box_name, product.product_name) AS product_name,
                            products.product_price,
                            order_lines.product_quantity,
                            (order_lines.product_quantity * products.product_price) AS line_total
                        FROM 
                            order_lines
                            LEFT JOIN products ON products.product_id = order_lines.product_id
                            LEFT JOIN product ON products.SKU = product.SKU
                            LEFT JOIN boxes ON products.SKU = boxes.SKU
                        WHERE 
                            order_lines.order_id = %s''', (order_id,))
        order_lines = cursor.fetchall()  # Fetch all results

        # Calculate the total amount based on order lines
        total_amount = sum(line[3] for line in order_lines)

        # Define the order statuses
        order_statuses = [
            {"id": 0, "name": "Pending"},
            {"id": 1, "name": "Preparing"},
            {"id": 2, "name": "Ready for delivery"},
            {"id": 3, "name": "On delivery vehicle"},
            {"id": 4, "name": "Delivered"}
        ]

        # Render the customer-order_detail.html template with the fetched data
        return render_template('customer-order_detail.html', location=session['location'][0], customer_info=customer_info, role=role, theorder=theorder, order_lines=order_lines, total_amount=total_amount, msg=msg, order_statuses=order_statuses, cart=cart)       
    else: 
        return redirect(url_for('logout'))  # Redirect to logout if the user is not logged in or doesn't have the specific role

@app.route('/customer/receipts_<receipt_id>')
def customer_receipt_detail(receipt_id):
    msg = request.args.get('msg', '')
    role = session.get('role')
    user_id = session.get('user_id')
    cursor = getCursor()
    cart = session.get('cart', {})

    # Check if the user is logged in and has the specific role (role == 4)
    if 'loggedin' in session and role == 4:
        # Execute a SQL query to fetch the customer's role, full name, and profile picture
        cursor.execute("""SELECT roles.role_name, CONCAT(customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                           FROM roles 
                           INNER JOIN users ON roles.role_id = users.role_id 
                           INNER JOIN customers ON customers.user_id = users.user_id 
                           WHERE users.user_id = %s""", (user_id,))
        customer_info = cursor.fetchone()  # Fetch the result of the query

        # Execute a SQL query to fetch receipt details including customer information, payment, and shipment details
        cursor.execute("""SELECT
                        CONCAT(customers.given_name, " ", customers.family_name) AS full_name,
                        customers.customer_address,
                        customers.phone_number,
                        customers.email,
                        payments.payment_date,
                        orders.order_id,
                        receipts.gst,
                        orders.order_date,
                        shippments.shippment_price,
                        payments.amount
                    FROM 
                        orders 
                        LEFT JOIN payments ON payments.payment_id = orders.payment_id
                        LEFT JOIN receipts ON orders.order_id = receipts.order_id
                        LEFT JOIN customers ON customers.user_id = orders.user_id
                        LEFT JOIN shippments ON shippments.shippment_id = orders.shippment_id
                    WHERE 
                        receipts.receipt_id = %s AND orders.user_id = %s
                       """, (receipt_id, user_id))
        thereceipt = cursor.fetchone()  # Fetch the result of the query

        # Execute a SQL query to fetch all order lines for the current order
        cursor.execute('''SELECT 
                            COALESCE(boxes.box_name, product.product_name) AS product_name,
                            products.product_price,
                            order_lines.product_quantity,
                            (products.product_price * order_lines.product_quantity) AS subtotal,
                            COALESCE(box_units.unit_name, product_units.unit_name) AS unit_name
                        FROM 
                            order_lines
                            LEFT JOIN products ON products.product_id = order_lines.product_id
                            LEFT JOIN product ON products.SKU = product.SKU
                            LEFT JOIN units AS product_units ON product_units.unit_id = product.unit
                            LEFT JOIN boxes ON products.SKU = boxes.SKU
                            LEFT JOIN units AS box_units ON box_units.unit_id = boxes.unit
                        WHERE 
                            order_lines.order_id = %s''', (thereceipt[5],)) 
        order_lines = cursor.fetchall()  # Fetch all results

        # Calculate the total amount based on order lines
        total_amount = sum(line[3] for line in order_lines)

        # Render the customer-receipt_detail.html template with the fetched data
        return render_template('customer-receipt_detail.html', total_amount=total_amount, location=session['location'][0], customer_info=customer_info, role=role, thereceipt=thereceipt, order_lines=order_lines, msg=msg, cart=cart)       
    else: 
        return redirect(url_for('logout'))

@app.route('/customer/news', methods=['GET', 'POST'])
def customer_news():
    role = session.get('role')
    user_id = session.get('user_id')
    cursor = getCursor()

    cursor.execute('''SELECT roles.role_name, CONCAT(customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                      FROM roles 
                      INNER JOIN users ON roles.role_id = users.role_id 
                      INNER JOIN customers ON customers.user_id = users.user_id 
                      WHERE users.user_id = %s''', (user_id,))
    customer_info = cursor.fetchone()

    depot_name = session['location']

    cursor.execute('SELECT depot_id FROM depots WHERE location = %s;', (depot_name[0],))
    depot_id = cursor.fetchone()

    if 'loggedin' in session and role == 4:
        if request.method == 'POST':
            searchinput = request.form.get('searchinput', '').strip()
            order = request.form.get('order')
        else:
            searchinput = request.args.get('searchinput', '').strip()
            order = request.args.get('order')

        # Fetch news data based on the search query
        if searchinput:
            # Perform search in the database based on the title search input
            cursor.execute('''SELECT * FROM news 
                              WHERE depot_id IN (0, %s) AND title LIKE %s
                              ORDER BY publish_date {}, news_id {}'''.format(order or 'DESC', order or 'DESC'), (depot_id[0],'%' + searchinput + '%',))
            news_list = cursor.fetchall()
        else:
            # If no search input is provided, fetch all news
            cursor.execute('SELECT * FROM news WHERE depot_id IN (0, %s) ORDER BY publish_date {}, news_id {}'.format(order or 'DESC', order or 'DESC'), (depot_id[0],))
            news_list = cursor.fetchall()

        # Render template with the list of news
        return render_template('customer-news.html', customer_info=customer_info, role=role, news_list=news_list, searchinput=searchinput, order=order)
    else:
        # If user is not logged in or doesn't have the required role, redirect to home page
        return redirect(url_for('logout'))


@app.route('/customer/news/<int:news_id>', methods=['GET'])
def customer_news_details(news_id):
    role = session.get('role')
    user_id = session.get('user_id')
    cursor = getCursor()

    cursor.execute('''SELECT roles.role_name, CONCAT(customers.given_name, " ", customers.family_name) AS full_name, customers.pic
                      FROM roles 
                      INNER JOIN users ON roles.role_id = users.role_id 
                      INNER JOIN customers ON customers.user_id = users.user_id 
                      WHERE users.user_id = %s''', (user_id,))
    customer_info = cursor.fetchone()

    if 'loggedin' in session and role == 4:
        cursor.execute('''SELECT news.*, CONCAT(staff.given_name, ' ', staff.family_name) AS full_name
                   FROM news 
                   INNER JOIN staff ON news.created_by = staff.user_id
                   WHERE news_id = %s''', (news_id,))
        news_item = cursor.fetchone()

        if news_item:
            return render_template('customer-news_details.html', news_item=news_item, customer_info=customer_info, role=role)
        else:
            return redirect(url_for('error', msg='News not found'))   
    else:
        # If user is not logged in or doesn't have the required role, redirect to home page
        return redirect(url_for('logout'))                          


@app.route('/customer/cancel-order')
def customer_cancel_order():

   

    user_id = session.get('user_id')
    print(' user_id')

    order_id = request.args.get('order_id')
    cursor = getCursor()

    cursor.execute("""SELECT payment_id FROM orders WHERE order_id = %s""", (order_id,))
    payment_id = cursor.fetchone()

    cursor.execute("""UPDATE payments SET status = 'Canceled' WHERE payment_id = %s""", (payment_id[0],))

    cursor.execute('SELECT amount FROM payments WHERE payment_id = %s;', (payment_id[0],))
    payment_amount = cursor.fetchone()


    cursor.execute("""SELECT balance FROM customers WHERE user_id = %s""", (user_id,))
    balance = cursor.fetchone()

    updated_balance = balance[0] + payment_amount[0]

    cursor.execute("""UPDATE customers SET balance = %s WHERE user_id = %s""", (updated_balance, user_id))


    msg = 'Order has been cancled successfully.'
    return redirect( url_for('customer_orders'))




def get_order_details(order_id):
    cursor = getCursor()
    cursor.execute("""SELECT o.product_id, o.product_quantity, pro.SKU FROM order_lines AS o LEFT JOIN products AS pro ON pro.product_id = o.product_id WHERE order_id = %s
    """, (order_id,))
    order_details = cursor.fetchall()

    return order_details



@app.route('/customer/re-order', methods=["POST"])
def customer_re_order():
    
    if 'loggedin' in session:
        order_id = request.args.get('order_id')
        order_details = get_order_details(order_id)
        
        if 'cart' not in session:
            session['cart'] = {}
        cart = session['cart']
        
        for item in order_details:
            sku = item[2]
            quantity = item[1]
            
            if sku in cart:
                cart[sku]['quantity'] += quantity
            else:
                product_details = get_product_details(sku)
                cart[sku] = {
                    'name': product_details[1],
                    'price': product_details[2] * product_details[17],
                    'image_url': product_details[4],
                    'quantity': quantity,
                    'stock': product_details[16],
                    'unit': product_details[3],
                    'pro_id': product_details[18]
                }
        
        session['cart'] = cart
        session.modified = True
        return redirect(url_for('cus_product_checkout'))
    else:
        return redirect(url_for('homepage'))
    


def get_product_details(sku):

    location = session.get('location') 
  
    cursor=getCursor()

    if 'Auckland' in location:

    
        cursor.execute("""SELECT pro.SKU, p.product_name, pro.product_price, u.unit_name, p.pic, pro.product_category_id, b.pic, b.box_name, us.unit_name, p.product_des, b.box_des, p.product_origins, b.product_origins, g.giftcard_name, g.pic, g.giftcard_des, s.quantity, prom.discount, pro.product_id FROM products AS pro LEFT JOIN product AS p ON p.SKU = pro.SKU LEFT JOIN units AS u ON u.unit_id = p.unit LEFT JOIN boxes AS b ON b.SKU = pro.SKU LEFT JOIN units AS us ON us.unit_id = b.unit LEFT JOIN giftcards AS g ON pro.SKU = g.SKU LEFT JOIN stock AS s ON s.product_id = pro.product_id LEFT JOIN promotion_types AS prom ON pro.promotion_type_id = prom.promotion_type_id WHERE pro.SKU = %s AND pro.product_status =1 AND pro.depot_id = '1'""", (sku,)) 

        product = cursor.fetchone()
    elif 'Christchurch' in location:

    
        cursor.execute("""SELECT pro.SKU, p.product_name, pro.product_price, u.unit_name, p.pic, pro.product_category_id, b.pic, b.box_name, us.unit_name, p.product_des, b.box_des, p.product_origins, b.product_origins, g.giftcard_name, g.pic, g.giftcard_des, s.quantity, prom.discount, pro.product_id FROM products AS pro LEFT JOIN product AS p ON p.SKU = pro.SKU LEFT JOIN units AS u ON u.unit_id = p.unit LEFT JOIN boxes AS b ON b.SKU = pro.SKU LEFT JOIN units AS us ON us.unit_id = b.unit LEFT JOIN giftcards AS g ON pro.SKU = g.SKU LEFT JOIN stock AS s ON s.product_id = pro.product_id LEFT JOIN promotion_types AS prom ON pro.promotion_type_id = prom.promotion_type_id WHERE pro.SKU = %s AND pro.product_status =1 AND pro.depot_id = '2'""", (sku,)) 

        product = cursor.fetchone()
    elif 'Wellington' in location:

        cursor.execute("""SELECT pro.SKU, p.product_name, pro.product_price, u.unit_name, p.pic, pro.product_category_id, b.pic, b.box_name, us.unit_name, p.product_des, b.box_des, p.product_origins, b.product_origins, g.giftcard_name, g.pic, g.giftcard_des, s.quantity, prom.discount, pro.product_id FROM products AS pro LEFT JOIN product AS p ON p.SKU = pro.SKU LEFT JOIN units AS u ON u.unit_id = p.unit LEFT JOIN boxes AS b ON b.SKU = pro.SKU LEFT JOIN units AS us ON us.unit_id = b.unit LEFT JOIN giftcards AS g ON pro.SKU = g.SKU LEFT JOIN stock AS s ON s.product_id = pro.product_id LEFT JOIN promotion_types AS prom ON pro.promotion_type_id = prom.promotion_type_id WHERE pro.SKU = %s AND pro.product_status =1 AND pro.depot_id = '3'""", (sku,)) 

        product = cursor.fetchone()
    elif 'Hamilton' in location:

    
        cursor.execute("""SELECT pro.SKU, p.product_name, pro.product_price, u.unit_name, p.pic, pro.product_category_id, b.pic, b.box_name, us.unit_name, p.product_des, b.box_des, p.product_origins, b.product_origins, g.giftcard_name, g.pic, g.giftcard_des, s.quantity, prom.discount, pro.product_id FROM products AS pro LEFT JOIN product AS p ON p.SKU = pro.SKU LEFT JOIN units AS u ON u.unit_id = p.unit LEFT JOIN boxes AS b ON b.SKU = pro.SKU LEFT JOIN units AS us ON us.unit_id = b.unit LEFT JOIN giftcards AS g ON pro.SKU = g.SKU LEFT JOIN stock AS s ON s.product_id = pro.product_id LEFT JOIN promotion_types AS prom ON pro.promotion_type_id = prom.promotion_type_id WHERE pro.SKU = %s AND pro.product_status =1 AND pro.depot_id = '4'""", (sku,)) 

        product = cursor.fetchone()
    elif 'Invercargill' in location:

        cursor.execute("""SELECT pro.SKU, p.product_name, pro.product_price, u.unit_name, p.pic, pro.product_category_id, b.pic, b.box_name, us.unit_name, p.product_des, b.box_des, p.product_origins, b.product_origins, g.giftcard_name, g.pic, g.giftcard_des, s.quantity, prom.discount, pro.product_id FROM products AS pro LEFT JOIN product AS p ON p.SKU = pro.SKU LEFT JOIN units AS u ON u.unit_id = p.unit LEFT JOIN boxes AS b ON b.SKU = pro.SKU LEFT JOIN units AS us ON us.unit_id = b.unit LEFT JOIN giftcards AS g ON pro.SKU = g.SKU LEFT JOIN stock AS s ON s.product_id = pro.product_id LEFT JOIN promotion_types AS prom ON pro.promotion_type_id = prom.promotion_type_id WHERE pro.SKU = %s AND pro.product_status =1 AND pro.depot_id = '5'""", (sku,)) 

        product = cursor.fetchone()

    return product



