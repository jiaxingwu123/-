from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os
from flask_redis import FlaskRedis

app = Flask(__name__)  # 实例化flask对象


app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:070529@localhost/movies1"  # 依次表示用户名，密码ip端口数据库
app.config[
    "SQLALCHEMY_TRACK_MODIFICATIONS"] = True  # 如果设置为True，Flask-SQLAlchemy将跟踪对对象的修改，并发出信号。默认值为None，他可以启用跟踪功能，但会发出警告，表明它在将来会被默认禁用。这需要额外的内存，如果不需要，应该禁用。
app.config["SECRET_KEY"] = "0114a7a0c3bf4743b52b9a81706a206c"
# redis的链接路径
app.config['REDIS_URL'] = "redis://127.0.0.1:6379/1"
# 文件上传的保存路径
app.config['UP_DIR'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/")
# 用户图像保存路径
app.config['FC_DIR'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/users/")

db = SQLAlchemy(app)  # 创建与数据库相关的内容
rd = FlaskRedis(app)

app.debug = True  # 调试模式打开

from app.home import home as home_blueprint
from app.admin import admin as admin_blueprint

app.register_blueprint(home_blueprint)
app.register_blueprint(admin_blueprint, url_prefix="/admin")  # url_prefix，地址加上admin拼接成为所需的优先的访问


@app.errorhandler(404)
def page_not_found(error):
    return render_template('home/404.html'), 404