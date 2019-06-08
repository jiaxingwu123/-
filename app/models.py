# encoding:utf8

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

import datetime
from app import db


# 会员
class User(db.Model):
    __tablename__ = "user"  # 表的名字
    id = db.Column(db.Integer, primary_key=True)  # 编号
    # dai biao zi duan
    name = db.Column(db.String(100), unique=True)  # 昵称
    pwd = db.Column(db.String(100))  # 密码
    email = db.Column(db.String(100), unique=True)  # 邮箱
    phone = db.Column(db.String(100), unique=True)  # 电话
    info = db.Column(db.TEXT)  # 简介
    face = db.Column(db.String(255), unique=True)  # 头像
    addtime = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)  # 添加时间
    uuid = db.Column(db.String(255), unique=True)  # 唯一标识符
    userlogs = db.relationship('Userlog', backref="user")  # 链接到用户日志
    comments = db.relationship('Comment', backref="user")  # 链接到评论
    moviecols = db.relationship('Moviecol', backref='user')  # 收藏外將關聯

    def __repr__(self):  # 查询到某个id返回name
        return "<User %r>" % self.name

    def check_pwd(self, pwd):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.pwd, pwd)


# 會員日志
class Userlog(db.Model):
    __tablename__ = "userlog"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 所屬會員
    ip = db.Column(db.String(100))  # 登錄ip
    addtime = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)  # 會員每次登錄時間

    def __repr__(self):
        return "<Userlog %r>" % self.id


# 標籤
class Tag(db.Model):
    __tablename__ = "tag"
    id = db.Column(db.Integer, primary_key=True)  # 編號
    name = db.Column(db.String(100), unique=True)  # 标题
    addtime = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    movies = db.relationship('Movie', backref="tag")  # 电影外建的关联

    def __repr__(self):  # 返回的类型
        return "<Tag %r>" % self.name


# 电影
class Movie(db.Model):
    __tablename__ = "movie"
    id = db.Column(db.Integer, primary_key=True)  # 編號
    title = db.Column(db.String(255), unique=True)  # 標題
    url = db.Column(db.String(255), unique=True)  # 电影播放地址
    info = db.Column(db.TEXT)  # 簡介
    logo = db.Column(db.String(255), unique=True)  # 封面
    star = db.Column(db.SmallInteger)  # 星級
    playnum = db.Column(db.BigInteger)  # 播放量
    commentnum = db.Column(db.BigInteger)  # 評論量
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))  # 所属标签

    area = db.Column(db.String(255))  # 上映地區
    releasse_time = db.Column(db.Date)
    length = db.Column(db.String(100))  # 時間長
    addtime = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)  # 添加時間
    comments = db.relationship("Comment", backref='movie')
    moviecols = db.relationship("Moviecol", backref='movie')

    def __repr__(self):
        return "<Movie %r>" % self.title


# 上映預告
class Preview(db.Model):
    __tablename__ = "preview"
    id = db.Column(db.Integer, primary_key=True)  # 編號
    title = db.Column(db.String(255), unique=True)  # 標題
    logo = db.Column(db.String(255), unique=True)  # 封面
    addtime = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)  # 添加時間

    def __repr__(self):
        return "<Preview %r>" % self.title


# 評論
class Comment(db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)  # 編號
    content = db.Column(db.TEXT)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 所屬用戶
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))  # 所屬電壓
    addtime = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)  # 添加時間

    def __repr__(self):
        return "<Comment %r>" % self.id


# 电影收藏
class Moviecol(db.Model):
    __tablename__ = "moviecol"
    id = db.Column(db.Integer, primary_key=True)  # 編號
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 所屬用戶
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))  # 所屬電壓
    addtime = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)  # 添加時間

    def __repr__(self):
        return "<Moviecol %r>" % self.id


# 权限
class Auth(db.Model):
    __tablename__ = "auth"
    id = db.Column(db.Integer, primary_key=True)  # 編號
    name = db.Column(db.String(255), unique=True)  # 標題
    url = db.Column(db.String(255), unique=True)  # 地址
    addtime = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)  # 添加時間

    def __repr__(self):
        return "<Auth %r>" % self.name


# 角色
class Role(db.Model):
    __tablename__ = "role"
    id = db.Column(db.Integer, primary_key=True)  # 編號
    name = db.Column(db.String(255), unique=True)
    auths = db.Column(db.String(100))
    addtime = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)  # 添加時間
    admins = db.relationship("Admin", backref='role')

    def __repr__(self):
        return "<Role %r>" % self.name


# 管理员
class Admin(db.Model):
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)  # 編號
    name = db.Column(db.String(255), unique=True)  # 管理员账号
    is_super = db.Column(db.SmallInteger)  # 是否为超级管理员权限,0为超级1为普通
    pwd = db.Column(db.String(100))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))  # 所属角色
    addtime = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)  # 添加時間
    oplogs = db.relationship("Oplog", backref="admin")  # 操作日志外建关联
    adminlogs = db.relationship("Adminlog", backref='admin')
    roles = db.relationship("Role", backref='admin')

    def __repr__(self):
        return "<Admin %r>" % self.name
        # 检验密码登录是否正确

    def check_pwd(self, pwd):
        """验证密码是否正确，直接将hash密码和输入的密码进行比较，如果相同则，返回True"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.pwd, pwd)


# 管理员登录日志

class Adminlog(db.Model):
    __tablename__ = "adminlog"
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))  # 所屬會員
    ip = db.Column(db.String(100))  # 登錄ip
    addtime = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)  # 會員每次登錄時間

    def __repr__(self):
        return "<Adminlog %r>" % self.id


# 操作日志
class Oplog(db.Model):
    __tablename__ = "oplog"
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))  # 所屬會員
    ip = db.Column(db.String(100))  # 登錄ip
    addtime = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)  # 會員每次登錄時間
    reason = db.Column(db.String(600))  # 操作的原因

    def __repr__(self):
        return "<Oplog %r>" % self.id

# if __name__ == '__main__':
# db.create_all()  # 用于创建所有的列表
# 添加role下面的一个字段
#     role = Role(
#         name='wujiaxing',
#         auths=''
#     )
#     db.session.add(role)  # 将内容添加到
#     db.session.commit()  # 将内容提交
#     from werkzeug.security import generate_password_hash   # 加密工具
#
#     admin = Admin(
#         name="imoocmovie1",
#         pwd=generate_password_hash('imoocmovie1'),
#         is_super=0,
#         role_id=1
#     )
#     db.session.add(admin)
#     db.session.commit()
# #
