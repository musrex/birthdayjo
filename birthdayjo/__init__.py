import imghdr
import os

from flask import (Flask, abort, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from werkzeug.utils import secure_filename
from wtforms import SubmitField



class MyForm(FlaskForm):
    file = FileField('file')
    submit = SubmitField('submit')

def create_app(test_config=None):
    #create and configure app
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'birthdayjo.sqlite'),
        UPLOAD_FOLDER = 'static/img',
        ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    )

    if test_config is None:
        #load the instance config, if exists and not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        #load the test config is passed in
        app.config.from_mapping(test_config)

    #ensures the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.errorhandler(413)
    def too_large(e):
        flash('File is too large', 'ERROR')
        return render_template('create.html') 

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/lodging/')
    def lodging():
        return render_template('lodging.html')

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    @app.route('/create/', methods=['GET','POST'])
    def upload_file():
        if request.method == 'POST':
            # check if post request has the file part
            if 'file' not in request.files:
                flash('Error 1: No file selected.')
                return redirect(url_for('blog.create'))
            file = request.files['file']
            # if the user does not select a file, the browser submits an
            # empty file without a filename
            if file.filename == '':
                flash('Error 2: No file selected.')
                return redirect('blog.create')
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return redirect(url_for('download_file', name=filename))
        return redirect(url_for('blog.gallery'))


    @app.route('/static/img/<filename>')
    def upload(filename):
        return send_from_directory(app.config['UPLOAD_PATH'], filename)

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)

    return app
