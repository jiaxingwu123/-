# coding:utf-8
from . import admin
from flask import render_template, redirect, url_for, flash, session, request, abort
from app.admin.forms import LoginForm, TagForm, MovieForm, PreviewForm, PwdForm, AuthForm, RoleForm, AdminForm
from app.models import Admin, Tag, Movie, Preview, User, Comment, Moviecol, Oplog, Adminlog, Userlog, Auth, Role
from functools import wraps
from app import db, app

# 将文件名设置为安全的文件名
from werkzeug.utils import secure_filename
import os
import uuid
import datetime


# 上下文应用处理器(封装全局变量，将全局变量封装到魔板中)
@admin.context_processor
def tpl_extra():
    data = dict(
        online_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    return data


# 建立登录装饰器
def admin_login_req(func):
    @wraps(func)  # 保留源信息，本质是endpoint装饰，否则修改函数名很危险
    def decorated_function(*args, **kwargs):  # 接收参数，*args接收多余参数形成元组，**kwargs接收对于参数形成字典
        if "admin" not in session:
            return redirect(url_for("admin.login", next=request.url))
        return func(*args, **kwargs)  # 登录成功就执行传过来的函数

    return decorated_function


# 建立登录权限装饰器
def admin_auth(func):
    @wraps(func)
    def authted_function(*args, **kwargs):
        admin = Admin.query.join(
            Role
        ).filter(
            Role.id == Admin.role_id,
            Admin.id == session['admin_id']
        ).first()
        # print(admin)
        print(admin)
        # 如果没有指定权限，就按照超级管理员走
        if admin:
            auths = admin.role.auths
            # 将auth转换位列表
            auths = list(map(lambda item: int(item), auths.split(',')))

            auth_list = Auth.query.all()
            # print(auth_list)
            urls = [v.url for v in auth_list for val in auths if val == v.id]
            # print([v.url for v in auth_list])
            # print(urls)
            rule = request.url_rule
            if str(rule) not in urls:
                abort(404)
        return func(*args, **kwargs)

    return authted_function


# 修改文件名称
def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + fileinfo[-1]
    return filename


# 后台登录（支持get请求和post提交）
@admin.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # 获取表单数据
        data = form.data
        admin = Admin.query.filter_by(name=data["account"]).first()  # 查询表信息admin表里的用户名信息first代表查询一条记录
        if not admin.check_pwd(data['pwd']):
            flash("密码错误！", 'err')
            return redirect(url_for('admin.login'))
        # # 如果密码正确，session中添加账号记录，然后跳转到request中的next，或者是跳转到后台的首页
        session["admin"] = data['account']
        session['admin_id'] = admin.id
        adminlog = Adminlog(
            admin_id=admin.id,
            ip=request.remote_addr,

        )
        db.session.add(adminlog)
        db.session.commit()
        return redirect(request.args.get('next') or url_for('admin.index'))
    return render_template('admin/login.html', form=form)


# 后台退出
@admin.route("/logout/")
@admin_login_req
def logout():
    session.pop("admin", None)
    session.pop("admin_id", None)
    return redirect(url_for('admin.login'))


# 后台
@admin.route("/")
@admin_login_req
@admin_auth
def index():
    return render_template('admin/index.html')


# 后台修改密码
@admin.route("/pwd/", methods=['GET', 'POST'])
@admin_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session['admin']).first()
        from werkzeug.security import generate_password_hash
        admin.pwd = generate_password_hash(data['new_pwd'])
        db.session.add(admin)
        db.session.commit()
        flash("修改密码成功，请重新登录页面", "ok")
        return redirect(url_for('admin.logout'))
    return render_template('admin/pwd.html', form=form)


# 添加标签编辑
@admin.route("/tag/add/", methods=['GET', 'POST'])
@admin_login_req
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        # 判断所提交的标签是否存在
        tag = Tag.query.filter_by(name=data["name"]).count()
        if tag == 1:
            flash("名称已经存在！", "err")
            return redirect(url_for('admin.tag_add'))
        # 所提交的标签并未存在，将标签输入到数据库中
        tag = Tag(
            name=data['name']
        )
        # 添加标签
        db.session.add(tag)
        # 提交标签
        db.session.commit()
        flash("添加标签成功", "ok")
        oplog = Oplog(
            admin_id=session['admin_id'],
            ip=request.remote_addr,
            reason="添加标签%s" % data['name']
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for('admin.tag_add'))
    return render_template('admin/tag_add.html', form=form)


# 标签列表
@admin.route("/tag/list/<int:page>/", methods=['GET'])
@admin_login_req
def tag_list(page=None):
    if page is None:
        page = 1
    # 以添加时间作为排序，paginate作为分页
    page_data = Tag.query.order_by(
        Tag.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    return render_template('admin/tag_list.html', page_data=page_data)


# 删除标签
@admin.route("/tag/del/<int:id>/", methods=['GET'])
@admin_login_req
def tag_del(id=None):
    tag = Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash("删除标签成功！", "ok")
    return redirect(url_for('admin.tag_list', page=1))


# 编辑标签
@admin.route("/tag/edit/<int:id>/", methods=['GET', 'POST'])
@admin_login_req
def tag_edit(id):
    form = TagForm()
    tag = Tag.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        # 判断所提交的标签是否存在
        tag_count = Tag.query.filter_by(name=data["name"]).count()
        if tag.name != data["name"] and tag_count == 1:
            flash("名称已经存在！", "err")
            return redirect(url_for('admin.tag_edit', id=id))
        # 所提交的标签并未存在，将标签输入到数据库中
        tag.name = data["name"]
        # 添加标签
        db.session.add(tag)
        # 提交标签
        db.session.commit()
        flash("修改标签成功", "ok")
        redirect(url_for('admin.tag_edit', id=id))
    return render_template('admin/tag_edit.html', form=form, tag=tag)


# 添加电影
@admin.route("/movie/add/", methods=["GET", "POST"])
@admin_login_req
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        # 获取上传的数据
        file_url = secure_filename(form.url.data.filename)
        file_logo = secure_filename(form.logo.data.filename)
        # 查看一下路径是否存在，如果不存在，则创建路劲
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])
            # 对这个目录进行授权
            os.chmod(app.config["UP_DIR"], "rw")
        url = change_filename(file_url)
        logo = change_filename(file_logo)
        # 保存
        form.url.data.save(app.config["UP_DIR"] + url)
        form.logo.data.save(app.config["UP_DIR"] + logo)
        movie = Movie(
            title=data["title"],
            url=url,
            info=data["info"],
            logo=logo,
            star=int(data['star']),
            playnum=0,
            commentnum=0,
            tag_id=int(data['tag_id']),
            area=data['area'],
            releasse_time=data["releasse_time"],
            length=data['length']
        )
        db.session.add(movie)
        db.session.commit()
        flash("添加成功", 'ok')
        return redirect(url_for('admin.movie_add'))
    return render_template('admin/movie_add.html', form=form)


# 电影列表
@admin.route("/movie/list/<int:page>/", methods=["GET", "POST"])
def movie_list(page=None):
    if page is None:
        page = 1
        # 以添加时间作为排序，paginate作为分页
        # movie关联tag进行查询  filter_by 单表关联的时候使用上边这个，多表关联的时候使用filter
    page_data = Movie.query.join(Tag).filter(
        # 将tag和movie进行关联
        Tag.id == Movie.tag_id
    ).order_by(
        Movie.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    # 将查询到的数据放到page_data之中
    return render_template('admin/movie_list.html', page_data=page_data)


# 删除电影
@admin.route("/movie/del/<int:id>/", methods=["GET", "POST"])
@admin_login_req
def movie_del(id=None):
    movie = Movie.query.get_or_404(int(id))
    db.session.delete(movie)
    db.session.commit()
    flash("删除电影成功！", "ok")
    return redirect(url_for('admin.movie_list', page=1))


# 编辑电影
@admin.route("/movie/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
def movie_edit(id=None):
    form = MovieForm()
    form.url.validators = []
    form.logo.validators = []
    movie = Movie.query.get_or_404(int(id))
    # 下面的用于解决初始内容（修改前的初始内容）
    if request.method == "GET":
        form.title.data = movie.title
        form.url.data = movie.url
        form.logo.data = movie.logo
        form.area.data = movie.area
        form.length.data = movie.length
        form.releasse_time.data = movie.releasse_time
        form.info.data = movie.info
        form.tag_id.data = movie.tag_id
        form.star.data = movie.star
    if form.validate_on_submit():
        data = form.data
        movie_count = Movie.query.filter_by(title=data["title"]).count()
        if movie_count == 1 and movie.title != data["title"]:
            flash("片名已经存在", 'err')
            return redirect(url_for('admin.movie_edit', id=movie.id))
            # 查看一下路径是否存在，如果不存在，则创建路劲
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])
            os.chmod(app.config["UP_DIR"], "rw")
        # 更改图片和视频
        if form.url.data.filename != "":
            file_url = secure_filename(form.url.data.filename)
            movie.url = change_filename(file_url)
            form.url.data.save(app.config["UP_DIR"] + movie.url)
        if form.logo.data.filename != "":
            file_logo = secure_filename(form.logo.data.filename)
            movie.logo = change_filename(file_logo)
            form.logo.data.save(app.config["UP_DIR"] + movie.logo)

        movie.star = data["star"]
        movie.releasse_time = data["releasse_time"]
        movie.tag_id = data["tag_id"]
        movie.info = data["info"]
        movie.title = data["title"]
        movie.area = data["area"]
        movie.length = data["length"]
        db.session.add(movie)
        db.session.commit()
        flash("修改成功", 'ok')
        return redirect(url_for('admin.movie_edit', id=movie.id))
    # 将movie传进来用于设置初始值
    return render_template('admin/movie_edit.html', form=form, movie=movie)


# 编辑上映预告
@admin.route("/preview/add/", methods=["GET", "POST"])
@admin_login_req
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        preview_count = Preview.query.filter_by(title=data["title"]).count()
        if preview_count == 1 and Preview.title != data["title"]:
            flash("片名已经存在", 'err')
            return redirect(url_for('admin.preview_add'))
        file_logo = secure_filename(form.logo.data.filename)
        # 查看一下路径是否存在，如果不存在，则创建路劲
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])
            os.chmod(app.config["UP_DIR"], "rw")
        logo = change_filename(file_logo)
        form.logo.data.save(app.config["UP_DIR"] + logo)
        # 保存其中的title值
        preview = Preview(
            title=data['title'],
            logo=logo
        )
        db.session.add(preview)
        db.session.commit()
        flash("修改成功", 'ok')
        return redirect(url_for('admin.preview_add'))
    return render_template('admin/preview_add.html', form=form)


# 上映预告列表
@admin.route("/preview/list/<int:page>/", methods=["GET"])
@admin_login_req
def preview_list(page=None):
    if page is None:
        page = 1
        # 以添加时间作为排序，paginate作为分页
        # movie关联tag进行查询  filter_by 单表关联的时候使用上边这个，多表关联的时候使用filter
    page_data = Preview.query.order_by(
        Preview.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    # 将查询到的数据放到page_data之中
    return render_template('admin/preview_list.html', page_data=page_data)


# 上映预告列表删除操作
@admin.route("/preview/del/<int:id>/", methods=["GET", "POST"])
@admin_login_req
def preview_del(id=None):
    preview = Preview.query.get_or_404(int(id))
    db.session.delete(preview)
    db.session.commit()
    flash("删除预告电影成功！", "ok")
    return redirect(url_for('admin.preview_list', page=1))


# 上映预告列表编辑操作
@admin.route("/preview/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
def preview_edit(id=None):
    # 必须把preview传到摸版列表中
    form = PreviewForm()
    preview = Preview.query.get_or_404(int(id))
    # 用于显示预告的标题（显示内容）
    if request.method == "GET":
        form.title.data = preview.title

    if form.validate_on_submit():
        data = form.data

        if form.logo.data.filename != "":
            file_logo = secure_filename(form.logo.data.filename)
            preview.logo = change_filename(file_logo)
            form.logo.data.save(app.config["UP_DIR"] + preview.logo)

        preview.title = data['title']
        db.session.add(preview)
        db.session.commit()
        flash("修改成功", 'ok')
        return redirect(url_for('admin.preview_edit', id=id))
    # 必须把preview传到摸版列表中
    return render_template('admin/preview_edit.html', form=form, preview=preview)


# 会员列表
@admin.route("/user/list/<int:page>/", methods=["GET"])
@admin_login_req
def user_list(page=None):
    if page is None:
        page = 1
        # 以添加时间作为排序，paginate作为分页
        # movie关联tag进行查询  filter_by 单表关联的时候使用上边这个，多表关联的时候使用filter
    page_data = User.query.order_by(
        User.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    return render_template('admin/user_list.html', page_data=page_data)


# 查看会员
@admin.route("/user/view/<int:id>/", methods=["GET"])
@admin_login_req
def user_view(id=None):
    user = User.query.get_or_404(int(id))
    return render_template('admin/user_view.html', user=user)


# 会员列表删除操作
@admin.route("/user/del/<int:id>/", methods=["GET", "POST"])
@admin_login_req
def user_del(id=None):
    user = User.query.get_or_404(int(id))
    db.session.delete(user)
    db.session.commit()
    flash("删除会员列表成功！", "ok")
    return redirect(url_for('admin.user_list', page=1))


# 评论列表
@admin.route("/comment/list/<int:page>", methods=["GET"])
@admin_login_req
def comment_list(page=None):
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
        User.id == Comment.user_id
    ).order_by(
        Comment.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    return render_template('admin/comment_list.html', page_data=page_data)


# 评论列表删除操作
@admin.route("/comment/del/<int:id>/", methods=["GET", "POST"])
def comment_del(id=None):
    return redirect(url_for('admin.comment_list', page=1))


# 收藏列表
@admin.route("/moviecol/list/<int:page>/", methods=["GET", "POST"])
def moviecol_list(page=None):
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
        User.id == Moviecol.user_id
    ).order_by(
        Moviecol.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    return render_template('admin/moviecol_list.html', page_data=page_data)


# 收藏列表删除操作
@admin.route("/moviecol/del/<int:id>/", methods=["GET"])
@admin_login_req
def moviecol_del(id=None):
    moviecol = Moviecol.query.get_or_404(int(id))
    db.session.delete(moviecol)
    db.session.commit()
    flash("收藏列表删除评论成功！", "ok")
    return redirect(url_for('admin.moviecol_list', page=1))


# 操作日志
@admin.route("/oplog/list/<int:page>", methods=['GET'])
@admin_login_req
def oplog_list(page=None):
    # reason admin_id ip
    if page is None:
        page = 1
        # 以添加时间作为排序，paginate作为分页
        # movie关联tag进行查询  filter_by 单表关联的时候使用上边这个，多表关联的时候使用filter
    page_data = Oplog.query.join(
        Admin
    ).filter(
        Admin.id == Oplog.admin_id,
    ).order_by(
        Oplog.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    return render_template('admin/oplog_list.html', page_data=page_data)


# 管理员日志列表
@admin.route("/adminiloginlog/list/<int:page>/", methods=['GET'])
@admin_login_req
def adminiloginlog_list(page=None):
    if page is None:
        page = 1
        # 以添加时间作为排序，paginate作为分页
        # movie关联tag进行查询  filter_by 单表关联的时候使用上边这个，多表关联的时候使用filter
    page_data = Adminlog.query.join(
        Admin
    ).filter(
        Admin.id == Adminlog.admin_id,

    ).order_by(
        Adminlog.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    return render_template('admin/adminiloginlog_list.html', page_data=page_data)


# 会员日志列表
@admin.route("/userloginlog/list/<int:page>/", methods=['GET'])
@admin_login_req
def userloginlog_list(page=None):
    if page is None:
        page = 1
        # 以添加时间作为排序，paginate作为分页
        # movie关联tag进行查询  filter_by 单表关联的时候使用上边这个，多表关联的时候使用filter
    page_data = Userlog.query.join(
        User
    ).filter(
        User.id == Userlog.user_id,
    ).order_by(
        Userlog.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    return render_template('admin/userloginlog_list.html', page_data=page_data)


# 添加角色
@admin.route("/role/add/", methods=["GET", "POST"])
def role_add():
    form = RoleForm()
    if form.validate_on_submit():
        data = form.data
        print(data)
        role = Role(
            name=data['name'],
            # 使用逗号将数组分为字符串形式
            auths=",".join(map(lambda v: str(v), data["auths"]))
        )
        db.session.add(role)
        db.session.commit()
        flash("添加角色成功", 'ok')
    return render_template('admin/role_add.html', form=form)


# 角色列表
@admin.route("/role/list/<int:page>", methods=['GET'])
def role_list(page=None):
    if page is None:
        page = 1
        # 以添加时间作为排序，paginate作为分页
        # movie关联tag进行查询  filter_by 单表关联的时候使用上边这个，多表关联的时候使用filter
    page_data = Role.query.order_by(
        Role.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    return render_template('admin/role_list.html', page_data=page_data)


# 删除角色
@admin.route("/role/del/<int:id>/", methods=['GET'])
@admin_login_req
def role_del(id=None):
    role = Role.query.filter_by(id=id).first_or_404()
    db.session.delete(role)
    db.session.commit()
    flash("删除角色成功！", "ok")
    return redirect(url_for('admin.role_list', page=1))


# 编辑角色
@admin.route("/role/edit/<int:id>/", methods=['GET', 'POST'])
def role_edit(id):
    form = RoleForm()
    role = Role.query.get_or_404(id)
    if request.method == "GET":
        auths = role.auths
        # 为了使之前定义的权限显示在表单中
        form.auths.data = list(map(lambda v: int(v), auths.split(',')))
    if form.validate_on_submit():
        data = form.data
        role.name = data["name"]
        role.auths = ",".join(map(lambda v: str(v), data["auths"]))
        db.session.add(role)
        db.session.commit()
        flash("修改角色成功", 'ok')
    return render_template('admin/role_edit.html', form=form, role=role)


# 添加权限
@admin.route("/auth/add/", methods=["GET", "POST"])
def auth_add():
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth = Auth(
            name=data['name'],
            url=data['url']
        )
        db.session.add(auth)
        db.session.commit()
        flash("添加权限成功", 'ok')
    return render_template('admin/auth_add.html', form=form)


# 权限列表
@admin.route("/auth/list/<int:page>/", methods=['GET'])
def auth_list(page=None):
    if page is None:
        page = 1
    # 以添加时间作为排序，paginate作为分页
    page_data = Auth.query.order_by(
        Auth.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    return render_template('admin/auth_list.html', page_data=page_data)


# 删除权限
@admin.route("/auth/del/<int:id>/", methods=['GET'])
def auth_del(id=None):
    auth = Auth.query.filter_by(id=id).first_or_404()
    db.session.delete(auth)
    db.session.commit()
    flash("删除权限成功！", "ok")
    return redirect(url_for('admin.auth_list', page=1))


# 编辑权限
@admin.route("/auth/edit/<int:id>/", methods=['GET', 'POST'])
def auth_edit(id):
    form = AuthForm()
    auth = Auth.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        auth.url = data["url"]
        auth.name = data['name']
        db.session.add(auth)
        # 提交标签
        db.session.commit()
        flash("修改权限成功", "ok")
        redirect(url_for('admin.auth_edit', id=id))
    return render_template('admin/auth_edit.html', form=form, auth=auth)


# 添加管理员
@admin.route("/admin/add/", methods=["GET", "POST"])
def admin_add():
    from werkzeug.security import generate_password_hash
    form = AdminForm()
    if form.validate_on_submit():
        data = form.data
        auth = Admin(
            name=data['name'],
            pwd=generate_password_hash(data['pwd']),
            role_id=data['role_id'],
            # 普通管理员，不是超级管理员
            is_super=1
        )
        db.session.add(auth)
        db.session.commit()
        flash("添加管理员成功", 'ok')
    return render_template('admin/admin_add.html', form=form)


# 管理员列表
@admin.route("/admin/list/<int:page>/", methods=['GET'])
def admin_list(page=None):
    if page is None:
        page = 1
    # 以添加时间作为排序，paginate作为分页
    page_data = Admin.query.join(
        Role
    ).filter(
        Role.id == Admin.role_id
    ).order_by(
        Admin.addtime.desc()
        # per_page 表示多少条信息显示一页
    ).paginate(page=page, per_page=10)
    print(page_data)
    return render_template('admin/admin_list.html', page_data=page_data)
