from flask import Flask, render_template, request, session, url_for, redirect, current_app
from flask_sqlalchemy import SQLAlchemy #Sqlite操作
from sqlalchemy.sql.expression import func
from flask_compress import Compress #Gzip压缩
import time,random
from functools import wraps
import re
from werkzeug.security import check_password_hash #数据库密码解密
from flask_cache import Cache #缓存系统

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask.db?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'r(*&9e0Y7rby(fr&*by9t77'
Compress(app)
db = SQLAlchemy(app)
cache = Cache(app,config={'CACHE_TYPE': 'redis','CACHE_REDIS_HOST': '127.0.0.1','CACHE_REDIS_PORT': 6379,'CACHE_REDIS_DB': '1'})

#缓存带参数的网址
def key_prefix_func():    
    key_prefix = "view%s"
    with current_app.app_context():       
        if '%s' in key_prefix:            
            cache_key = key_prefix % request.url        
        else:            
            cache_key = key_prefix
    return cache_key
 
#去掉首页和分类页的文章的html标签
def nohtml(content):
    return(re.compile(r'<[^>]+>',re.S).sub('',content))
app.jinja_env.globals.update(nohtml=nohtml)

#装饰器校验用户是否登录
def wapper(func):
    @wraps(func)
    def inner(*args,**kwargs):
        if not session.get('user'):
            return redirect('/login')
        return func(*args,**kwargs)
    return inner

#上下文全局变量
@app.context_processor
def make_template_context():
    title = Setting.query.filter_by().first()
    category_nav = db.session.query(Category).all()
    check = User.query.filter_by().first()
    return dict(title=title,category_nav=category_nav,check=check)

#错误处理
@app.errorhandler(404)
@app.errorhandler(500)
@app.errorhandler(400)
def page_not_found(e):
    return render_template('404.html')

#数据库模型定义
class Setting(db.Model):
    """设置"""
    __tablename__ = 'setting'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    discription = db.Column(db.Text)
    about = db.Column(db.Text)
    keywords = db.Column(db.Text)
    notice = db.Column(db.Text)

class User(db.Model):
    """用户"""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text)
    password = db.Column(db.Text)
    
class Category(db.Model):
    """分类"""
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)

class Article(db.Model):
    """文章"""
    __tablename__ = 'articles'
    PER_PAGE = 4
    ADMIN_PER_PAGE = 12

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    created = db.Column(db.Text)
    author = db.Column(db.Text)
    category_id = db.Column(db.Integer)
    @property
    def link(self):
        return url_for('article', id=self.id, _external=True)

class Comment(db.Model):
    """留言"""
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text)
    website = db.Column(db.Text)
    articleid = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created = db.Column(db.Text)

#路由定义
@app.route('/')
@cache.cached(key_prefix=key_prefix_func,timeout=31536000)
def index():
    pagination = Article.query.order_by(
        Article.id.desc()).paginate(
        int(request.args.get('page', 1)), per_page=Article.PER_PAGE,
        error_out=False)
    return render_template('index.html', articles=pagination.items, pagination=pagination)

@app.route('/search')
@cache.cached(key_prefix=key_prefix_func,timeout=31536000)
def search():
    keyword = request.args.get('s')
    pagination = Article.query.filter(
        Article.title.ilike("%"+keyword+"%")).order_by(Article.id.desc()).paginate(int(request.args.get('page', 1)), per_page=Article.PER_PAGE,
        error_out=False)
    return render_template('index.html',articles=pagination.items,keyword=keyword,pagination=pagination)

@app.route('/category/<int:id>/')
@cache.cached(timeout=31536000)
def category(id):
    pagination = Article.query.filter_by(category_id=id).order_by(Article.id.desc()).paginate(
        int(request.args.get('page', 1)), per_page=Article.PER_PAGE,
        error_out=False)
    category=db.session.query(Category.name).filter(Category.id == id).first()
    return render_template('category.html', articles=pagination.items,pagination=pagination,category=category)

@app.route('/about/')
@cache.cached(timeout=31536000)
def about():
    return render_template('about.html')

@app.route('/article/<int:id>.html', methods=['GET', 'POST'])
@cache.cached(timeout=31536000)
def article(id):
    if request.method == 'GET':
        category=db.session.query(Category).join(Article,Article.category_id == Category.id).filter(Article.id == id).first()
        comments = db.session.query(Comment).filter_by(articleid = id)
        return render_template('article.html',article=Article.query.get_or_404(id),comments=comments,category=category)
    if request.method == 'POST':
        db.session.add(Comment(username=request.form.get("author"),website=request.form.get("url"),
        articleid=id,comment=request.form.get("text"),created=time.strftime("%Y-%m-%d", time.localtime())))
        db.session.commit()
        return redirect(url_for('article',id=id ))

@app.route('/login/', methods=['GET', 'POST'])
def login():
    check = User.query.filter_by().first()
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        if request.form.get("username") == check.username and check_password_hash(check.password,request.form.get("password")) == True:
            session["user"] = request.form.get("username")
            return redirect(url_for('managerarticle'))
        else:
            return render_template('login.html',loginerror='用户名或密码错误！')

@app.route('/article/edit/<int:id>/', methods=['GET', 'POST'])
@wapper
def editarticle(id):
    edit_article = Article.query.filter(Article.id == id).first()
    if request.method == 'GET':
        edit_category=Category.query.filter(Category.id==edit_article.category_id).first()
        return render_template('edit.html',edit_title=edit_article.title,edit_content=edit_article.content, edit_category=edit_category) 
    if request.method == 'POST':
        article_item = Article.query.filter(Article.id == id).first()
        article_item.title=request.form.get("title")
        article_item.content=request.form.get("text1")
        article_item.category_id=request.form.get("category")
        article_item.created=time.strftime("%Y-%m-%d", time.localtime())
        db.session.commit()
        return redirect(url_for('index'))

@app.route('/article/add/', methods=['GET', 'POST'])
@wapper
def addarticle():
    if request.method == 'GET':
        return render_template('add.html')
    if request.method == 'POST':
        db.session.add(Article(title=request.form.get("title"),content=request.form.get("text1"),
        created=time.strftime("%Y-%m-%d", time.localtime()),category_id=request.form.get("category"),author='王殊勋'))
        db.session.commit()
        return redirect(url_for('index'))

@app.route('/category/manager/', methods=['GET', 'POST'])
@wapper
def managercategory():
    if request.method == 'GET':
        return render_template('category-manager.html')
    if request.method == 'POST':
        db.session.add(Category(name=request.form.get("categoryname")))
        db.session.commit()
        return redirect(url_for('managercategory'))

@app.route('/comment/manager/')
@wapper
def managercomment():
    pagination = db.session.query(Comment).paginate(
        int(request.args.get('page', 1)), per_page=Article.ADMIN_PER_PAGE,
        error_out=False)
    return render_template('comment-manager.html',admin_comment=pagination.items,pagination=pagination)

@app.route('/setting/', methods=['GET', 'POST'])
@wapper
def setting():
    if request.method == 'GET':
        settings = db.session.query(Setting).first()
        return render_template('setting.html',settings=settings)
    if request.method == 'POST':
        setting_item = Setting.query.filter().first()
        setting_item.title=request.form.get("title")
        setting_item.discription=request.form.get("discription")
        setting_item.keywords=request.form.get("keywords")
        setting_item.about=request.form.get("text1")
        setting_item.notice=request.form.get("notice")
    
        db.session.commit()
        return redirect(url_for('index'))

@app.route('/article/manager/', methods=['GET', 'POST'])
@wapper
def managerarticle():
    if request.method == 'GET':
        pagination = Article.query.order_by(
            Article.created.desc()).paginate(
            int(request.args.get('page', 1)), per_page=Article.ADMIN_PER_PAGE,
            error_out=False)
        return render_template('article-manager.html',articles=pagination.items,pagination=pagination)


@app.route('/manager/search')
@wapper
def adminsearch():
    keyword = request.args.get('search')
    pagination = Article.query.filter(
        Article.title.ilike("%"+keyword+"%")).order_by(Article.id.desc()).paginate(int(request.args.get('page', 1)), 
        per_page=Article.ADMIN_PER_PAGE,error_out=False)
    return render_template('article-manager.html',articles=pagination.items,keyword=keyword,pagination=pagination)

@app.route('/article/delete/<int:id>/')
@wapper
def articledelete(id):
    db.session.delete(Article.query.filter(Article.id == id).first())
    db.session.commit()
    return redirect(url_for('managerarticle'))

@app.route('/comment/delete/<int:id>/')
@wapper
def commentdelete(id):
    db.session.delete(Comment.query.filter(Comment.id == id).first())
    db.session.commit()
    return redirect(url_for('managercomment'))

@app.route('/category/delete/<int:id>/')
@wapper
def categorydelete(id):
    db.session.delete(Category.query.filter(Category.id == id).first())
    db.session.commit()
    return redirect(url_for('managercategory'))

@app.route('/logout', methods=['GET'])
@wapper
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if  __name__ == '__main__':
    app.run(host='0.0.0.0',port='8000')
