# coding:utf-8
from flask_wtf import FlaskForm
from wtforms.fields import SubmitField, StringField, PasswordField, FileField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Email, Regexp, ValidationError
from app.models import User


class RegistForm(FlaskForm):
    name = StringField(
        label="昵称",
        validators=[
            DataRequired("请输入昵称！")
        ],
        description='昵称',

        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入昵称！",

        }
    )
    email = StringField(
        label="邮箱",

        validators=[
            DataRequired("请输入邮箱！"),
            # 内置邮箱验证
            Email('邮箱的格式不正确')
        ],
        description='邮箱',

        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入邮箱！",

        }
    )

    phone = StringField(
        label="电话",
        validators=[
            DataRequired("请输入电话！"),
            # 使用正则表达式来验证手机号
            Regexp("1[34589]\\d{9}", message='手机格式错误')

        ],
        description='电话',

        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入电话！",

        }
    )
    pwd = PasswordField(
        label="密码",
        validators=[
            DataRequired("请输入密码！")
        ],
        description='密码',

        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入密码！",

        }
    )

    repwd = PasswordField(
        label="确认密码",
        validators=[
            DataRequired("请输入确认密码！"),
            EqualTo('pwd', message='两次密码不一致')
        ],
        description='确认密码',

        render_kw={
            'class': 'form-control input-lg',
            "placeholder": "请输入确认密码！",
        }
    )
    submit = SubmitField(
        label='注册',
        render_kw={
            "class": "btn btn-lg btn-success btn-block",
        }
    )

    def validate_name(self, filed):
        name = filed.data
        user = User.query.filter_by(name=name).count()
        if user == 1:
            raise ValidationError('昵称已经存在')

    def validate_email(self, filed):
        email = filed.data
        user = User.query.filter_by(email=email).count()
        if user == 1:
            raise ValidationError('邮箱已经存在')

    def validate_phone(self, filed):
        phone = filed.data
        user = User.query.filter_by(phone=phone).count()
        if user == 1:
            raise ValidationError('电话已经存在')


class LoinForm(FlaskForm):
    name = StringField(
        label="账号",
        validators=[
            DataRequired("请输入账号！")
        ],
        description='账号',

        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入账号！",

        }
    )
    pwd = PasswordField(
        label="密码",
        validators=[
            DataRequired("请输入密码！")
        ],
        description='密码',

        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入密码！",

        }
    )
    submit = SubmitField(
        label='登录',
        render_kw={
            "class": "btn btn-lg btn-primary btn-block",
        }
    )


class UserdetailForm(FlaskForm):
    name = StringField(
        label="账号",
        validators=[
            DataRequired("请输入账号！")
        ],
        description='账号',

        render_kw={
            "class": "form-control",
            "placeholder": "请输入账号！",

        }
    )
    email = StringField(
        label="邮箱",

        validators=[
            DataRequired("请输入邮箱！"),
            Email('邮箱的格式不正确')
        ],
        description='邮箱',

        render_kw={
            "class": "form-control",
            "placeholder": "请输入邮箱！",

        }
    )

    phone = StringField(
        label="电话",
        validators=[
            DataRequired("请输入电话！"),
            Regexp("1[34589]\\d{3}", message='手机格式错误')

        ],
        description='电话',

        render_kw={
            "class": "form-control",
            "placeholder": "请输入电话！",

        }
    )
    # fileField这个字段用于保存头像字段
    face = FileField(
        label="头像",
        validators=[
            DataRequired('请上传头像')
        ],
        description='头像',
    )
    info = TextAreaField(
        label="简介",
        validators=[
            DataRequired('请输入简介！')
        ],
        description='简介',
        render_kw={
            'class': "form-control",
            'rows': 10
        }
    )
    submit = SubmitField(
        # <span class="glyphicon glyphicon-saved"></span>   用于控制字体
        label='保存修改',
        render_kw={
            "class": "btn btn-success",
        }
    )


class PwdForm(FlaskForm):
    old_pwd = PasswordField(
        label="旧密码",
        validators=[
            DataRequired("请输入旧密码！")
        ],
        description='旧密码',

        render_kw={
            "class": "form-control",
            "placeholder": "请输入旧密码！",
        }
    )

    new_pwd = PasswordField(
        label="新密码",
        validators=[
            DataRequired("请输入新密码！")
        ],
        description='新密码',

        render_kw={
            "class": "form-control",
            "placeholder": "请输入新密码！",
        }
    )

    submit = SubmitField(
        label='编辑',
        render_kw={
            "class": "btn btn-success",
        }
    )


class CommentForm(FlaskForm):
    content = TextAreaField(
        label='内容',
        validators=[
            DataRequired("请输入内容！")
        ],
        description='内容',
        render_kw={
            'id': 'input_content'
        }
    )
    submit = SubmitField(
        label='提交评论',
        render_kw={
            "class": "btn btn-success",
            'id': 'btn-sub'
        }
    )
