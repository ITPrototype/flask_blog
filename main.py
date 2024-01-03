from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE')
app.secret_key = os.getenv('SECRET_KEY')
app.jinja_env.add_extension('jinja2.ext.do')
db = SQLAlchemy(app)
app.config['UPLOAD_FOLDER'] = 'uploads'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=5))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)



def create_admin():
    with app.app_context():
        db.create_all()  
        admin_username = f"{os.getenv('USERNAME')}"
        admin_password = f"{os.getenv('PASSWORD')}"
        hashed_password = generate_password_hash(admin_password, method='pbkdf2:sha256')

        admin_user = User.query.filter_by(username=admin_username).first()

        if admin_user is None:
            admin_user = User(username=admin_username, password_hash=hashed_password, is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
  

if __name__ == "__main__":
    create_admin()
    @app.route("/")
    def index():
        articles = Blog.query.all()
        return render_template("index.html", name="test", articles=articles)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                return redirect(url_for('dashboard'))
        return render_template('login.html')

    @app.route("/dashboard", methods=['POST', 'GET'])
    def dashboard():
        if 'user_id' in session:
            articles = Blog.query.all()
           
            user = db.session.get(User,session['user_id'])
            return render_template('dashboard.html', user=user,articles=articles)
        else:
            return redirect(url_for('index'))

    @app.route("/post_article", methods=['POST'])
    def post_article():
        if 'user_id' in session:
            title = request.form['title']
            text = request.form['text']
            article_id = request.form.get('article_id')
            if article_id:
                blog_post = Blog.query.get(article_id)
                blog_post.title = title
                blog_post.text = text
            else:
                new_blog = Blog(title=title, text=text)
                db.session.add(new_blog)
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('index'))
        
    @app.route('/edit_post/<int:article_id>', methods=['GET'])
    def edit_post(article_id):
        if 'user_id' in session:
            article = Blog.query.get(article_id)
            return render_template('edit_post.html', article=article)
        else:
            return redirect(url_for('index'))
    @app.route('/delete_article/<int:article_id>')
    def delete_article(article_id):
        if 'user_id' in session:
            article = Blog.query.get(article_id)
            db.session.delete(article)
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('index'))
    @app.route('/view/<int:article_id>')
    def view(article_id):
        article = Blog.query.get(article_id)
        return render_template("view.html",article=article)
    app.run(debug=True)
