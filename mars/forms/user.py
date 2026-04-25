from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, EmailField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo


class RegisterForm(FlaskForm):
    email = EmailField('Login / email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password_again = PasswordField('Repeat password', validators=[DataRequired(), EqualTo('password', message='Пароли не совпадают')])
    surname = StringField('Surname', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    position = StringField('Position', validators=[DataRequired()])
    speciality = StringField('Speciality', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')