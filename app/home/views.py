# coding:utf-8
from . import home
from flask import render_template, redirect, url_for, flash, session, request, Response
from app.home.forms import RegistForm, UserdetailForm, LoinForm, CommentForm, PwdForm
from app.models import User, Userlog, Preview, Movie, Tag, Comment, Moviecol
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import uuid
from functools import wraps
from app import db, app, rd
import os
import datetime


# 建立登录装饰器
def user_login_req(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("home.login", next=request.url))
        return func(*args, **kwargs)

    return decorated_function


# 修改文件名称
def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + fileinfo[-1]
    return filename


# 会员登录
@home.route("/login/", methods=['POST', 'GET'])
def login():
    form = LoinForm()
    if form.validate_on_submit():
        # 获取前端页面填写的数据
        data = form.data
        user = User.query.filter_by(name=data['name']).first()
        if user:
            if not user.check_pwd(data['pwd']):
                flash('密码错误', 'err')
                return redirect(url_for('home.login'))
        else:
            flash('账号不存在！', 'err')
            return redirect(url_for('home.login'))
        session['user'] = user.name
        session['user_id'] = user.id
        userlog = Userlog(
            user_id=user.id,
            # ip的获取方法
            ip=request.remote_addr
        )
        db.session.add(userlog)
        db.session.commit()
        return redirect(url_for('home.user'))
    return render_template("home/login.html", form=form)


# 会员退出
@home.route("/logout/")
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    return redirect(url_for("home.login"))


# 会员注册
@home.route("/regist/", methods=['POST', 'GET'])
def regist():
    form = RegistForm()
    if form.validate_on_submit():
        # 获取其中的data
        data = form.data
        user = User(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            pwd=generate_password_hash(data['pwd']),
            uuid=uuid.uuid4().hex

        )

        db.session.add(user)
        db.session.commit()
        flash("注册成功", 'ok')
    return render_template("home/regist.html", form=form)


# 会员修改资料
@home.route("/user/", methods=['POST', 'GET'])
@user_login_req
def user():
    form = UserdetailForm()
    user = User.query.get(int(session['user_id']))
    form.face.validators = []
    if request.method == "GET":
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info
    if form.validate_on_submit():
        data = form.data
        file_face = secure_filename(form.face.data.filename)
        # 查看一下路径是否存在，如果不存在，则创建路劲
        if not os.path.exists(app.config["FC_DIR"]):
            os.makedirs(app.config["FC_DIR"])
            os.chmod(app.config["FC_DIR"])
        user.face = change_filename(file_face)
        form.face.data.save(app.config["FC_DIR"] + user.face)

        name_count = User.query.filter_by(name=data['name']).count()
        if data['name'] != user.name and name_count == 1:
            flash('昵称已存在！', 'err')
            return redirect(url_for('home.user'))

        email_count = User.query.filter_by(email=data['email']).count()
        if data['email'] != user.email and email_count == 1:
            flash('邮箱已存在！', 'err')
            return redirect(url_for('home.user'))

        phone_count = User.query.filter_by(phone=data['phone']).count()
        if data['phone'] != user.phone and phone_count == 1:
            flash('电话已存在！', 'err')
            return redirect(url_for('home.user'))

        user.name = data['name']
        user.email = data['email']
        user.phone = data['phone']
        user.info = data['info']
        db.session.add(user)
        db.session.commit()
        flash("修改成功", 'ok')
        return redirect(url_for('home.user'))
    return render_template("home/user.html", form=form, user=user)


# 修改密码
@home.route("/pwd/", methods=['POST', 'GET'])
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=session['user']).first()
        if not user.check_pwd(data['old_pwd']):
            flash('旧密码错误', 'err')
            return redirect(url_for('home.pwd'))
        user.pwd = generate_password_hash(data['new_pwd'])
        db.session.add(user)
        db.session.commit()
        flash("修改密码成功，请重新登录页面", "ok")
        return redirect(url_for('home.logout'))
    return render_template("home/pwd.html", form=form)


# 评论记录
@home.route("/comments/<int:page>/")
def comments(page=None):
    if page is None:
        page = 1
        # 以添加时间作为排序，paginate作为分页
        # movie关联tag进行查询  filter_by 单表关联的时候使用上边这个，多表关联的时候使用filter
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Comment.movie_id,
        User.id == session['user_id']
    ).order_by(
        Comment.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    return render_template("home/comments.html", page_data=page_data)


# 登录日志
@home.route("/loginlog/<int:page>", methods=['GET'])
@user_login_req
def loginlog(page=None):
    if page is None:
        page = 1
        # 以添加时间作为排序，paginate作为分页
        # movie关联tag进行查询  filter_by 单表关联的时候使用上边这个，多表关联的时候使用filter
    page_data = Userlog.query.filter_by(
        user_id=int(session['user_id'])
    ).order_by(
        Userlog.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    return render_template("home/loginlog.html", page_data=page_data)


# 添加电影收藏
# 收藏电影
@home.route("/moviecol/add/", methods=["GET"])
@user_login_req
def moviecol_add():
    uid = request.args.get('uid', '')
    mid = request.args.get('mid', '')
    moviecol = Moviecol.query.filter_by(
        user_id=int(uid),
        movie_id=int(mid)
    ).count()
    if moviecol == 1:
        data = dict(ok=0)
    if moviecol == 0:
        moviecol = Moviecol(
            user_id=int(uid),
            movie_id=int(mid)
        )
        db.session.add(moviecol)
        db.session.commit()
        data = dict(ok=1)
    import json
    return json.dumps(data)


# 收藏电影
@home.route("/moviecol/<int:page>/", methods=["GET"])
@user_login_req
def moviecol(page=None):
    if page is None:
        page = 1
        # 以添加时间作为排序，paginate作为分页
        # movie关联tag进行查询  filter_by 单表关联的时候使用上边这个，多表关联的时候使用filter
    page_data = Moviecol.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Moviecol.movie_id,
        User.id == session['user_id']
    ).order_by(
        Moviecol.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    return render_template('home/moviecol.html', page_data=page_data)


# 首页
@home.route("/<int:page>/", methods=['GET'])
def index(page=None):
    tags = Tag.query.all()
    page_data = Movie.query
    # 标签 获取标签的话得到tid没有获取到的话就设置为0
    tid = request.args.get('tid', 0)
    if int(tid) != 0:
        page_data = page_data.filter_by(tag_id=int(tid))
    # 星级
    star = request.args.get('star', 0)
    if int(star) != 0:
        page_data = page_data.filter_by(star=int(star))
    # 时间
    time = request.args.get('time', 0)
    if int(time) != 0:
        if int(time) == 1:
            page_data = page_data.order_by(
                # 按电影添加时间升序
                Movie.addtime.desc()
            )
        else:
            page_data = page_data.order_by(
                # 按电影添加时间降序
                Movie.addtime.asc()
            )
    # 播放量
    pm = request.args.get('pm', 0)
    if int(pm) != 0:
        if int(pm) == 1:
            page_data = page_data.order_by(
                # 按电影添加时间升序
                Movie.playnum.desc()
            )
        else:
            page_data = page_data.order_by(
                # 按电影添加时间降序
                Movie.playnum.asc()
            )
    # 评论量
    cm = request.args.get('cm', 0)
    if int(cm) != 0:
        if int(cm) == 1:
            page_data = page_data.order_by(
                # 按电影添加时间升序
                Movie.commentnum.desc()
            )
        else:
            page_data = page_data.order_by(
                # 按电影添加时间降序
                Movie.commentnum.asc()
            )
    if page is None:
        page = 1
    page_data = page_data.paginate(page=page, per_page=10)
    p = dict(
        tid=tid,
        star=star,
        time=time,
        pm=pm,
        cm=cm
    )
    return render_template("home/index.html", tags=tags, p=p, page_data=page_data)


# 上映预告 动画
@home.route("/animation/")
def animation():
    data = Preview.query.all()
    # 下面用于查询当前的图片对应的标号
    # for v in data:
    #     print(v.id)
    return render_template("home/animation.html", data=data)


# 搜索
@home.route("/search/<int:page>")
def search(page=None):
    if page is None:
        page = 1
    # 查询到值的话为key，没查询到值的话采取默认的空
    key = request.args.get("key", "")
    movie_count = Movie.query.filter(
        # ilike为进行模糊匹配
        Movie.title.ilike('%' + key + '%')
    ).count()
    page_data = Movie.query.filter(
        Movie.title.ilike('%' + key + '%')
    ).order_by(
        Movie.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    page_data.key = key
    return render_template("home/search.html", key=key, page_data=page_data, movie_count=movie_count)


# 电影详情
@home.route("/play/<int:id>/<int:page>/", methods=['GET', 'POST'])
def play(id=None, page=None):
    movie = Movie.query.join(Tag).filter(
        Tag.id == Movie.tag_id,
        Movie.id == int(id)
    ).first_or_404()

    if page is None:
        page = 1
        # 以添加时间作为排序，paginate作为分页
        # movie关联tag进行查询  filter_by 单表关联的时候使用上边这个，多表关联的时候使用filter
    page_data = Comment.query.join(
        Movie
        # join对应的关联查询
    ).join(
        User
    ).filter(
        Movie.id == movie.id,
        User.id == Comment.user_id
    ).order_by(
        Comment.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)

    movie.playnum = movie.playnum + 1
    form = CommentForm()
    if 'user' in session and form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data['content'],
            movie_id=movie.id,
            user_id=session['user_id']
        )
        db.session.add(comment)
        db.session.commit()
        # 增加了一条数据，其评论需要加1
        movie.commentnum = movie.commentnum + 1
        db.session.add(movie)
        db.session.commit()
        flash("添加评论成功", "ok")
        return redirect(url_for('home.play', id=movie.id, page=1))
    db.session.add(movie)
    db.session.commit()
    return render_template("home/play.html", movie=movie, form=form, page_data=page_data)


# 电影详情
@home.route("/video/<int:id>/<int:page>/", methods=['GET', 'POST'])
def video(id=None, page=None):
    movie = Movie.query.join(Tag).filter(
        Tag.id == Movie.tag_id,
        Movie.id == int(id)
    ).first_or_404()

    if page is None:
        page = 1
        # 以添加时间作为排序，paginate作为分页
        # movie关联tag进行查询  filter_by 单表关联的时候使用上边这个，多表关联的时候使用filter
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == movie.id,
        User.id == Comment.user_id
    ).order_by(
        Comment.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)

    movie.playnum = movie.playnum + 1
    form = CommentForm()
    if 'user' in session and form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data['content'],
            movie_id=movie.id,
            user_id=session['user_id']
        )
        db.session.add(comment)
        db.session.commit()
        # 增加了一条数据，其评论需要加1
        movie.commentnum = movie.commentnum + 1
        db.session.add(movie)
        db.session.commit()
        flash("添加评论成功", "ok")
        return redirect(url_for('home.video', id=movie.id, page=1))
    db.session.add(movie)
    db.session.commit()
    return render_template("home/video.html", movie=movie, form=form, page_data=page_data)


@home.route('/tm/', methods=['GET', 'POST'])
def tm():
    import json
    resp = ''
    if request.method == 'GET':
        # 获取弹幕消息队列
        id = request.args.get('id')
        key = 'movie' + str(id)

        if rd.llen(key):
            msgs = rd.lrange(key, 0, 299)
            # 有消息的话封装成一个res，并且返回列表
            res = {
                'code': 1,
                'danmaku': [json.loads(v) for v in msgs]
            }
        else:
            res = {
                'code': 1,
                'danmaku': []
            }
        resp = json.dumps(res)
    if request.method == 'POST':
        # 添加弹幕
        data = json.loads(request.get_data())
        print(data)
        msg = {
            '__v': data['author'],
            'time': data['time'],
            'text': data['text'],
            'color': data['color'],
            'type': data['type'],
            'ip': request.remote_addr,
            '_id': datetime.datetime.now().strftime('%Y%m%d%H%M%S') + uuid.uuid4().hex,
            'player': [
                data['player']
            ]
        }
        res = {
            'code': 1,
            'data': msg
        }
        # 将封装好的字符串转换为json格式的数据
        resp = json.dumps(res)
        rd.lpush('movie' + str(data['player']), json.dumps(msg))
    return Response(resp, mimetype='application/json')
