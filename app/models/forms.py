from flask_wtf import FlaskForm
from wtforms.fields import StringField
from wtforms.fields import PasswordField
from wtforms.fields import SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    login_id = StringField(validators=[DataRequired()])
    password = PasswordField(validators=[DataRequired()])
    submit = SubmitField()