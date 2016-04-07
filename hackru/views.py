#!venv/bin/python
from flask import redirect, url_for, render_template, flash, request, send_from_directory
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
from flask_mail import Message
from hackru import app, lm, db, mail
from werkzeug import secure_filename
from oauth import OAuthSignIn
from models import User
import os, smtplib


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return render_template('500.html', error=str(e))


@app.route('/logout')
@login_required
def logout():
    try:
        app.logger.info("{}[{}] at {} logged out".format(
            current_user.name, current_user.id, request.remote_addr))
        logout_user()
        return redirect(url_for('index'))

    except Exception as e:
        return render_template('500.html', error=str(e))


@app.route('/dashboard', methods=['GET'])
@login_required
def dash():
    try:
        if current_user.confirmed > 0:
            if request.method == 'GET':
                return render_template('dashboard.html',
                                        name=current_user.name)
        else:
            return redirect(url_for('register'))

    except Exception as e:
        return render_template('500.html', error=str(e))


@app.route('/confirmstatus', methods=['GET'])
@login_required
def confirm_status():
    try:
        if current_user.confirmed > 0:
            if request.method == 'GET':
		if current_user.id > app.config["WAVE_LIMIT"]:
		    return render_template('404.html')
                return render_template('change-confirming-status.html')
        else:
            return redirect(url_for('register'))

    except Exception as e:
        return render_template('500.html', error=str(e))


@app.route('/confirmed', methods=['GET'])
@login_required
def confirm():
    try:
        if current_user.confirmed > 0:
            if request.method == 'GET':
		if current_user.id > app.config["WAVE_LIMIT"]:
		    return render_template('404.html')
                if current_user.confirmed != 2:
                    current_user.confirmed = 2
                    db.session.commit()

		    #msg = Message("HackRU X Important Information",
				  #sender="team@hackru.org", # Change this
				  #recipients=[current_user.email])
		    #msg.html = render_template('important_info.html')
		    #mail.send(msg)

                    app.logger.info("{}[{}] at {} confirmed attendance".format(
                        current_user.name, current_user.id, request.remote_addr))
                return render_template('confirmed.html')
        else:
            return redirect(url_for('register'))

    except Exception as e:
        return render_template('500.html', error=str(e))


@app.route('/notattending', methods=['GET'])
@login_required
def not_attending():
    try:
        if current_user.confirmed > 0:
            if request.method == 'GET':
		if current_user.id > app.config["WAVE_LIMIT"]:
		    return render_template('404.html')
                if current_user.confirmed != 3:
                    current_user.confirmed = 3
                    db.session.commit()
                    app.logger.info("{}[{}] at {} confirmed lack of attendance".format(
                        current_user.name, current_user.id, request.remote_addr))
                return render_template('not-attending.html')
        else:
            return redirect(url_for('register'))

    except Exception as e:
        return render_template('500.html', error=str(e))


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    try:
        if current_user.confirmed == 0:
            if request.method == 'GET':
                github = current_user.github
                resume = current_user.resume
                comments = current_user.comments
                if github is None: github = ""
                if comments is None: comments = ""
                if resume is None: resume = ""
                else: resume = resume[resume.index("_")+1:]
                return render_template('registration.html',
                                        github=github,
                                        resume=resume,
                                        comments=comments)
            if request.method == 'POST':

                if not 'check' in request.form: # User must check MLH box
                    return render_template('registration.html',
                            error="Please agree to the Code of Conduct.")

                # Upload file handling
                file = request.files['resume']
                if file:
                    if allowed_file(file.filename):
                        upload_file_handler(file)
                    else:
                        return render_template('registration.html',
                            error="Please upload a PDF, TXT, DOC, or DOCX")
                else:
                    flash("Successfully updated account info!")

                if request.form:
                        github = request.form.get('github')
                        comments = request.form.get('comments')

                """ for load testing
                elif request.json:
                    github = request.json.get('github')
                    comments = request.json.get('comments')
                """

                if github is None: github = ""
                else: current_user.github = github

                if comments is None: comments = ""
                else: current_user.comments = comments

                # Set user to registered
                current_user.confirmed = 1

                db.session.commit()

                app.logger.info("{}[{}] at {} registered successfully".format(
                    current_user.name, current_user.id, request.remote_addr))

                return render_template('signup-good.html')

        else:
            return redirect(url_for('dash'))

    except Exception as e:
        if e.code is not None and int(e.code) == 413:
            return render_template('413.html')
        else:
            return render_template('500.html', error=str(e))


@app.route('/stats/<provider>', methods=['GET'])
@login_required
def stats(provider):
    try:
        if current_user.is_admin:
            oauth = OAuthSignIn.get_provider(provider)
            users = oauth.get_users()
            
            # Dietary Restriction counters
            glutenfree = 0
            vegan = 0
            vegetarian = 0
            eatall = 0
            count = 0
            hi = 'hi'
            miscdiet = []
            
            # Shirt Sizes
            shirts = {
                'wXS': 0,
                'wS': 0,
                'wM': 0,
                'wL': 0,
                'wXL': 0,
                'uXS': 0,
                'uS': 0,
                'uM': 0,
                'uL': 0,
                'uXL': 0
            }

            # Schools
            stony = 0

            for user in users:
                count += 1
                if user['dietary_restrictions'] == 'Gluten-Free':
                    glutenfree += 1
                elif user['dietary_restrictions'] == 'Vegan':
                    vegan += 1
                elif user['dietary_restrictions'] == 'Vegetarian':
                    vegetarian += 1
                elif user['dietary_restrictions'] == 'None':
                    eatall += 1
                else:
                    miscdiet.append(user['dietary_restrictions'])
                if user['shirt_size'] == "Women's - XS":
                    shirts['wXS'] += 1
                elif user['shirt_size'] == "Women's - S":
                    shirts['wS'] += 1
                elif user['shirt_size'] == "Women's - M":
                    shirts['wM'] += 1
                elif user['shirt_size'] == "Women's - L":
                    shirts['wL'] += 1
                elif user['shirt_size'] == "Women's - XL":
                    shirts['wXL'] += 1
                elif user['shirt_size'] == "Unisex - XS":
                    shirts['uXS'] += 1
                elif user['shirt_size'] == "Unisex - S":
                    shirts['uS'] += 1
                elif user['shirt_size'] == "Unisex - M":
                    shirts['uM'] += 1
                elif user['shirt_size'] == "Unisex - L":
                    shirts['uL'] += 1
                elif user['shirt_size'] == "Unisex - XL":
                    shirts['uXL'] += 1
                if user['school']['name'] == "Stony Brook University":
                    stony += 1
            
            return render_template('stats.html', 
                                   users=users, 
                                   count=count, 
                                   glutenfree=glutenfree, 
                                   vegan=vegan, 
                                   vegetarian=vegetarian, 
                                   eatall=eatall, 
                                   miscdiet=miscdiet,
                                   shirts=shirts,
                                   stony=stony,
                                   current_user=current_user
            )
        else:
            return redirect(url_for('index'))

    except Exception as e:
        return render_template('500.html', error=str(e))


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():

    try:
        if current_user.confirmed > 0:
            if request.method == 'GET':
                github = current_user.github
                resume = current_user.resume
                comments = current_user.comments

                if github is None: github = ""
                if comments is None: comments = ""
                if resume is None: resume = ""
                else: resume = resume[resume.index("_")+1:]

                return render_template('manage.html',
                                        github=github,
                                        resume=resume,
                                        comments=comments)
            if request.method == 'POST':

                if request.form:
                    github = request.form.get('github')
                    comments = request.form.get('comments')

                """ For load testing
                elif request.json:
                    github = request.json.get('github')
                    comments = request.json.get('comments')
                """

                # Upload file handling
                file = request.files['resume']
                if file:
                    if allowed_file(file.filename):
                        upload_file_handler(file)
                    else:
                        resume = current_user.resume
                        if resume is None: resume = ""
                        else: resume = resume[resume.index("_")+1:]
                        return render_template('manage.html',
                            github = github,
                            comments = comments,
                            resume = resume,
                            error="Please upload a PDF, TXT, DOC, or DOCX")
                else:
                    flash("Successfully updated account info!")

                if github is None: github = ""
                else: current_user.github = github

                if comments is None: comments = ""
                else: current_user.comments = comments

		if request.form.get('check') == 'mentor' and not current_user.is_mentor:
		    current_user.is_mentor = True # Check mentor box
		elif request.form.get('check') is None and current_user.is_mentor:
		    current_user.is_mentor = False # Uncheck mentor box

                db.session.commit()

                app.logger.info("{}[{}] at {} updated account information".format(
                    current_user.name, current_user.id, request.remote_addr))

                return redirect(url_for('dash'))
        else:
            return redirect(url_for('register'))

    except Exception as e:
        if e.code is not None and int(e.code) == 413:
            return render_template('413.html')
        else:
            return render_template('500.html', error=str(e))


@app.route('/resumes/<res>', methods=['GET'])
@login_required
def resumes(res):
    if res == current_user.resume:
	return send_from_directory(app.config["UPLOAD_FOLDER"], res)
    return render_template('404.html')


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    try:
        if not current_user.is_anonymous:
            return redirect(url_for('index'))
        oauth = OAuthSignIn.get_provider(provider)
        return oauth.authorize()

    except Exception as e:
        return render_template('500.html', error=str(e))


@app.route('/callback/<provider>')
def oauth_callback(provider):
    try:
        if not current_user.is_anonymous:
            return redirect(url_for('index'))
        oauth = OAuthSignIn.get_provider(provider)
        mlh_id, name, email = oauth.callback()
        if mlh_id is None:
            flash('Authentication failed.')
            return redirect(url_for('index'))
        user = User.query.filter_by(mlh_id=mlh_id).first()
        if not user:
            # Create, add and login new user. Redirect to /register
            user = User(mlh_id=mlh_id, name=name, email=email)
            db.session.add(user)
            db.session.commit()
            login_user(user, True)
            app.logger.info("{}[{}] at {} logged in for the first time".format(
                current_user.name, current_user.id, request.remote_addr))
            return redirect(url_for('register'))
        else:
            # Login new user. Redirect to /
            login_user(user, True)
            app.logger.info("{}[{}] at {} logged in".format(
                current_user.name, current_user.id, request.remote_addr))
            return redirect(url_for('index'))

    except Exception as e:
        return render_template('500.html', error=str(e))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def upload_file_handler(file):
    # Save file
    filename = str(current_user.mlh_id) + "_" + secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    current_user.resume = filename
    # Delete old resume
    path = os.path.abspath(app.config['UPLOAD_FOLDER'])
    list = os.listdir(path)
    for item in list:
        id = int(item.split('_')[0])
        if id == int(current_user.mlh_id) and filename != item:
            os.remove(os.path.join(path, item))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(413)
def file_too_large(e):
    return render_template('413.html'), 413


@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500


#@app.errorhandler(Exception)
#def unhandled_exception(e):
#    return render_template('500.html'), 500


@app.route('/email')
def lelxd():
    msg = Message("HackRU X Important Information",
	sender="HackRU",
	recipients=["sakib.jalal@gmail.com"])
    msg.html = render_template('important_info.html')
    try:
	mail.send(msg)
	return "woo!"
    except Exception as e:
	return str(e)


""" Dummy route for load testing
@app.route('/test', methods=["POST"])
def test():
    if request.method == 'POST':
    	email = request.json.get("email")
    	mlh_id = request.json.get("mlh_id")
    	name = request.json.get("name")
    	user = User(mlh_id=mlh_id, name=name, email=email)
   	db.session.add(user)
   	db.session.commit()
   	login_user(user, True)
    	return render_template('index.html')
    else:
	return render_template('index.html')
"""

