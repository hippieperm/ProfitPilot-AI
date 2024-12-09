from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class LoginForm(FlaskForm):
    username = StringField('사용자 이름', validators=[
        DataRequired(message='사용자 이름을 입력해주세요.')
    ])
    password = PasswordField('비밀번호', validators=[
        DataRequired(message='비밀번호를 입력해주세요.')
    ])
    remember = BooleanField('로그인 상태 유지')
    submit = SubmitField('로그인')

class RegistrationForm(FlaskForm):
    username = StringField('사용자 이름', validators=[
        DataRequired(message='사용자 이름을 입력해주세요.'),
        Length(min=4, max=20, message='사용자 이름은 4-20자 사이여야 합니다.')
    ])
    email = StringField('이메일', validators=[
        DataRequired(message='이메일을 입력해주세요.'),
        Email(message='올바른 이메일 주소를 입력해주세요.')
    ])
    password = PasswordField('비밀번호', validators=[
        DataRequired(message='비밀번호를 입력해주세요.'),
        Length(min=6, message='비밀번호는 최소 6자 이상이어야 합니다.')
    ])
    password2 = PasswordField('비밀번호 확인', validators=[
        DataRequired(message='비밀번호를 다시 입력해주세요.'),
        EqualTo('password', message='비밀번호가 일치하지 않습니다.')
    ])
    submit = SubmitField('회원가입')
  