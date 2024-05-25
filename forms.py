from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class MessageForm(FlaskForm):
    """Form for adding/editing messages."""

    text = TextAreaField('text', validators=[DataRequired()])


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    image_url = StringField('(Optional) Image URL')


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class EditProfileForm(FlaskForm):
    """Form for editng user profile."""
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    image_url = StringField('(Optional) Image URL')
    bio = TextAreaField('Bio')
    location = StringField('Location')
    header_image_url = StringField('Header image url')
    password = PasswordField('Password', validators=[DataRequired()])

class DirectMessageForm(FlaskForm):
    """Form for sending direct messages."""

    text = TextAreaField('Message', validators=[DataRequired()])



