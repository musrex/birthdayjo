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
    )
    app.config['UPLOAD_EXTENSIONS'] = ['.jpg', 'jpeg', '.png', '.gif']
    app.config['UPLOAD_PATH'] = os.path.join(app.root_path, 'img')

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



    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/lodging/')
    def lodging():
        return render_template('lodging.html')

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)

    return app
