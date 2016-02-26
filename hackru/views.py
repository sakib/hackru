#!venv/bin/python
from flask import redirect, url_for, render_template, flash, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import login_user, logout_user, current_user, login_required
from oauth import OAuthSignIn
from models import User
from hackru import app, lm, db
from werkzeug import secure_filename
import os, logging


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard', methods=['GET'])
@login_required
def dash():
    if request.method == 'GET':
        return render_template('dashboard.html',
                                name=current_user.name)


@app.route('/confirm', methods=['GET'])
@login_required
def confirm():
    if request.method == 'GET':
        current_user.confirmed = True
        db.session.commit()
        return render_template('confirm.html')


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
                                        error="Error: Must agree to Code of Conduct")

            github = request.form.get('github')
            comments = request.form.get('comments')

            if github is None: github = ""
            else: current_user.github = github

            if comments is None: comments = ""
            else: current_user.comments = comments

            # Set user to registered
            if current_user.confirmed == 0:
                current_user.confirmed = 1

            # Upload file handling
            file = request.files['resume']
            if file:
                flash(upload_file_handler(file))

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
    if request.method == 'GET':
        github = current_user.github
        resume = current_user.resume
        comments = current_user.comments
        if github is None: github = ""
        if comments is None: comments = ""
        if resume is None: resume = ""
        return render_template('account.html',
                                github=github,
                                resume=resume,
                                comments=comments)
    if request.method == 'POST':
        github = request.form.get('github')
        comments = request.form.get('comments')

        if github is None: github = ""
        else: current_user.github = github

        if comments is None: comments = ""
        else: current_user.comments = comments

        # Upload file handling
        file = request.files['resume']
        if file:
            flash(upload_file_handler(file))

        return render_template('account.html',
                                github=github,
                                comments=comments,
                                filename=file.filename)


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
        return redirect(url_for('register'))
    else:
        # Login new user. Redirect to /
        login_user(user, True)
        return redirect(url_for('index'))


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def upload_file_handler(file):
    if allowed_file(file.filename):
        filename = str(current_user.mlh_id) + "_" + secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        current_user.resume = filename
        db.session.commit()
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
