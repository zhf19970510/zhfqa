# encoding:utf-8
from flask import Flask, render_template, request, redirect, url_for, session
from sqlalchemy import or_
from page_utils import Pagination

import config
from models import User, Question, Answer
from exts import db
from decorators import login_required

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)


@app.route('/')
def index():
    # context = {
    #     'questions': Question.query.order_by(db.desc('create_time')).all()
    # }
    questions = Question.query.order_by(db.desc('create_time')).all()
    # return render_template("index.html", **context)
    pager_obj = Pagination(request.args.get("page", 1), len(questions), request.path, request.args, per_page_count=10)
    questions = questions[pager_obj.start:pager_obj.end]
    html = pager_obj.page_html()
    return render_template("index.html", questions=questions, html=html)


@app.route("/search/")
def search():
    q = request.args.get("q")
    questions = Question.query.order_by(db.desc('create_time')).filter(or_(Question.title.contains(q), Question.content.contains(q))).all()
    context = {
        'questions': questions
    }
    return render_template('index.html', **context)


@app.route("/login/", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    else:
        telephone = request.form.get("telephone")
        password = request.form.get("password")
        user = User.query.filter(User.telephone == telephone, User.password == password).first()
        if user:
            session['user_id'] = user.id
            # 如果想在31天内都不需要登录
            remberme = request.form.get("remberme")
            if remberme == 'on':
                session.permanent = True
            return redirect(url_for("index"))
        else:
            # return u"手机号或者密码错误，请确认后再登录"
            msg = u'手机号或者密码错误，请确认后再登录'
            return render_template("login.html", msg=msg)


@app.route("/regist/", methods=['GET', 'POST'])
def regist():
    if request.method == 'GET':
        return render_template("regist.html")
    else:
        telephone = request.form.get("telephone")
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        # 手机号码验证，如果被注册了，就不能再注册了
        user = User.query.filter(User.telephone == telephone).first()
        if user:
            # return u"该手机号码已经被注册，请更换手机号码!"
            msg = u"该手机号码已经被注册，请更换手机号码!"
            return render_template("regist.html", msg=msg)
        else:
            # password1 要和password2相等才可以
            if password1 != password2:
                # return u"两次密码不相同，请重新核对!"
                msg = u"两次密码不相同，请重新核对!"
                return render_template("regist.html", msg=msg)
            else:
                user = User(telephone=telephone, username=username, password=password1)
                db.session.add(user)
                db.session.commit()
                # 如果注册成功，就让页面跳转到登录的页面
                return redirect(url_for("login"))


@app.route("/logout/")
def logout():
    # session.pop("user_id")
    # del session["user_id"]
    session.clear()
    return redirect(url_for("login"))


@app.route("/question/", methods=['GET', 'POST'])
@login_required
def question():
    if request.method == 'GET':
        return render_template("question.html")
    else:
        title = request.form.get('title')
        content = request.form.get('content')
        question = Question(title=title, content=content)
        user_id = session.get('user_id')
        user = User.query.filter(User.id == user_id).first()
        question.author = user
        db.session.add(question)
        db.session.commit()
        return redirect(url_for("index"))


@app.route('/detail/<question_id>/')
def detail(question_id):
    question_model = Question.query.filter(Question.id == question_id).first()
    return render_template('detail.html', question=question_model)


@app.route("/add_answer/", methods=['POST'])
@login_required
def add_anwser():
    content = request.form.get("answer_content")
    question_id = request.form.get("question_id")
    answer = Answer(content=content)
    user_id = session.get("user_id")
    user = User.query.filter(User.id == user_id).first()
    answer.author = user
    question = Question.query.filter(Question.id == question_id).first()
    answer.question = question
    db.session.add(answer)
    db.session.commit()
    return redirect(url_for('detail', question_id=question_id))


@app.context_processor
def my_context_processor():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.filter(User.id == user_id).first()
        if user:
            return {'user': user}

    return {}


if __name__ == '__main__':
    app.run(port=9000)
