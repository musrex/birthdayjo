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
    #create and configure a[[]]
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'birthdayjo.sqlite'),
        UPLOAD_PATH = 'birthdayjo/static/img',
        UPLOAD_EXTENSIONS = ['.JPG','.jpg','.JPEG','.png','.gif']
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
        return render_template('share.html') 



    def validate_image(stream):
        header = stream.read(512)
        stream.seek(0)
        format = imghdr.what(None, header)
        if not format:
            return None
        return '.' + (format if format != 'jpeg' else 'jpg')

    @app.route('/')
    def index():
        return render_template('base.html')

    @app.route('/gallery/')
    def gallery():
        files = os.listdir(app.config['UPLOAD_PATH'])
        return render_template('gallery.html', files=files)

    @app.route('/lodging/')
    def lodging():
        return render_template('lodging.html')

    @app.route('/share/')
    def share():
        files = os.listdir(app.config['UPLOAD_PATH'])
        return render_template('share.html', files=files)

    @app.route('/blog/share/', methods=['POST'])
    def upload_file():
        count = 0
        for uploaded_file in request.files.getlist('file'):

            filename = secure_filename(uploaded_file.filename)
            if filename != '':
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                    file_ext != validate_image(uploaded_file.stream):
                    flash('Invalid image, check file extension.', 'ERROR')
                    return render_template('share.html')
                uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
            flash('Image upload complete. ', 'Success')
            return render_template('/blog/share.html')


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
