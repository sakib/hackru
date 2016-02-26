#!venv/bin/python
from flask import redirect, url_for, render_template, flash, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import login_user, logout_user, current_user, login_required
from oauth import OAuthSignIn
from models import User
from hackru import app, lm, db
from werkzeug import secure_filename
import os


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logout')
@login_required
def logout():
    app.logger.info("{}[{}] at {} logged out".format(
        current_user.name, current_user.id, request.remote_addr))
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard', methods=['GET'])
@login_required
def dash():
    if current_user.confirmed > 0:
        if request.method == 'GET':
            return render_template('dashboard.html',
                                    name=current_user.name)
    else:
        return redirect(url_for('register'))


@app.route('/confirmstatus', methods=['GET'])
@login_required
def confirm_status():
    if current_user.confirmed > 0:
        if request.method == 'GET':
            return render_template('change-confirming-status.html')
    else:
        return redirect(url_for('register'))


@app.route('/confirmed', methods=['GET'])
@login_required
def confirm():
    if current_user.confirmed > 0:
        if request.method == 'GET':
            if current_user.confirmed != 2:
                current_user.confirmed = 2
                db.session.commit()
                app.logger.info("{}[{}] at {} confirmed attendance".format(
                    current_user.name, current_user.id, request.remote_addr))
            return render_template('confirmed.html')
    else:
        return redirect(url_for('register'))


@app.route('/notattending', methods=['GET'])
@login_required
def not_attending():
    if current_user.confirmed > 0:
        if request.method == 'GET':
            if current_user.confirmed != 3:
                current_user.confirmed = 3
                db.session.commit()
                app.logger.info("{}[{}] at {} confirmed lack of attendance".format(
                    current_user.name, current_user.id, request.remote_addr))
            return render_template('not-attending.html')
    else:
        return redirect(url_for('register'))


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():

    if current_user.confirmed == 0:
        if request.method == 'GET':
            github = current_user.github
            resume = current_user.resume
            comments = current_user.comments
            if github is None: github = ""
            if comments is None: comments = ""
            if resume is None: resume = ""
            return render_template('registration.html',
                                    github=github,
                                    resume=resume,
                                    comments=comments)
        if request.method == 'POST':

            if not 'check' in request.form: # User must check MLH box
                return render_template('registration.html',
                        error="Please agree to the Code of Conduct.")

            github = request.form.get('github')
            comments = request.form.get('comments')

            if github is None: github = ""
            else: current_user.github = github

            if comments is None: comments = ""
            else: current_user.comments = comments

            # Set user to registered
            current_user.confirmed = 1

            # Upload file handling
            file = request.files['resume']
            if file:
                upload_file_handler(file)

            db.session.commit()

            app.logger.info("{}[{}] at {} registered successfully".format(
                current_user.name, current_user.id, request.remote_addr))

            return render_template('signup-good.html')

    else:
        return redirect(url_for('dash'))


@app.route('/stats/<provider>', methods=['GET'])
@login_required
def stats(provider):
    if current_user.is_admin:
        oauth = OAuthSignIn.get_provider(provider)
        users = oauth.get_users()
        return render_template('stats.html', users=users)
    else:
        return redirect(url_for('index'))


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():

    print "nerds"

    if current_user.confirmed > 0:
        if request.method == 'GET':
            github = current_user.github
            resume = current_user.resume
            comments = current_user.comments
            if github is None: github = ""
            if comments is None: comments = ""
            if resume is None: resume = ""
            return render_template('manage.html',
                                    github=github,
                                    resume=resume,
                                    comments=comments)
        if request.method == 'POST':
            print "nerds!!!!!!!!!!!"
            github = request.form.get('github')
            comments = request.form.get('comments')

            print github, comments

            if github is None: github = ""
            else: current_user.github = github

            if comments is None: comments = ""
            else: current_user.comments = comments

            # Upload file handling
            file = request.files['resume']
            if file:
                print "there's a file!!!"
                flash(upload_file_handler(file))
            else:
                print "no file!!!"

            db.session.commit()

            app.logger.info("{}[{}] at {} updated account information".format(
                current_user.name, current_user.id, request.remote_addr))

            flash("Successfully updated account info!")

            return redirect(url_for('dash'))
    else:
        return redirect(url_for('register'))

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
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


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def upload_file_handler(file):
    if allowed_file(file.filename):
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

        return "Successfully updated information!"
    else:
        return "Invalid file type! Please upload a PDF, TXT, DOC, DOCX"
