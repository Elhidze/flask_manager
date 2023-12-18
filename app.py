# main.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy.exc import IntegrityError
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Elhidze13'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Классы ------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    user_tasks = db.relationship('Task', backref='user', lazy=True)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"User('{self.username}')"


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Log In')


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    priority = db.Column(db.String(20))
    completed = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Task {self.id} - {self.title}>"


Task.__tablename__ = 'tasks'


# функции -----------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('tasks'))
    return redirect(url_for('register'))


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = form.password.data
        new_user = User(username=form.username.data, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Username is already taken. Please choose a different username.')

    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tasks'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.password == form.password.data:
            login_user(user, remember=form.remember.data)
            flash('Login successful!', 'success')
            return redirect(url_for('tasks'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')

    return render_template('login.html', title='Login', form=form)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/tasks")
@login_required
def tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template("tasks.html", tasks=tasks)


@app.route('/add', methods=['POST'])
def add_task():
    title = request.form['title']
    description = request.form.get('description')
    due_date = request.form.get('due_date')
    priority = request.form.get('priority')
    category = request.form.get('category')
    user_id = current_user.get_id()

    new_task = Task(
        title=title,
        description=description,
        due_date=datetime.strptime(due_date, '%Y-%m-%d') if due_date else None,
        priority=priority,
        category=category,
        user_id=user_id
    )

    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('tasks'))


with app.app_context():
    db.create_all()

if __name__ == '__app__':
    app.run(host='0.0.0.0', port=5000, debug=True)
