from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, NumberRange


class JobForm(FlaskForm):
    job = StringField('Описание работы', validators=[DataRequired()])
    work_size = IntegerField('Длительность (в часах)', validators=[DataRequired(), NumberRange(min=1, message='Количество часов должно быть больше 0')])
    collaborators = StringField('Список id участников', validators=[DataRequired()])
    is_finished = BooleanField('Работа завершена')
    submit = SubmitField('Сохранить')
