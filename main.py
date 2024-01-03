from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor 
from markupsafe import Markup 
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required 
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
# Import your forms from the forms.py
from forms import CreatePostForm, CommentForm, LoginForm, UserForm  
import os




app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_KEY")
ckeditor = CKEditor(app)
bootstrap =  Bootstrap5(app) 





# TODO: Configure Flask-Login


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy()
db.init_app(app)  
login_manager = LoginManager() 
login_manager.init_app(app)  


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    # author = db.Column(db.String(250), nullable=False) 
    img_url = db.Column(db.String(250), nullable=False) 
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))   
    author = relationship("Users", back_populates="posts")
    comments = relationship("Comment", back_populates="parent_post")

    def to_dict(self): 
        return { 
            "id": self.id, 
            "title": self.title, 
            "subtitle": self.subtitle, 
            "date": self.date, 
             "body": self.body, 
             "img_url": self.img_url, 
             "author_id": self.author_id
        } 
    
    @staticmethod
    def full_list(): 
        all_posts = BlogPost.query.all() 
        post_list = [post.to_dict() for post in all_posts] 
        return post_list 
    
    def to_dict_kwargs(self, **kwargs): 
        post_dict = dict() 
        for key in kwargs: 
            if hasattr(self, key): 
                post_dict[key] = getattr(self, key) 
        return post_dict 
    
    @staticmethod 
    def create_post(**kwargs): 
        new_post = BlogPost(**kwargs) 
        db.session.add(new_post) 
        db.session.commit() 
        return new_post


# TODO: Create a User table for all your registered users.   
    
class Comment(db.Model): 
    __tablename__ = "comments" 
    id = db.Column(db.Integer, primary_key=True) 
    rating = db.Column(db.Integer, nullable=False) 
    comment = db.Column(db.Text, nullable=False) 
    author_id = db.Column(db.Integer, db.ForeignKey('users.id')) 
    comment_author = relationship("Users", back_populates="comments") 
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id")) 
    parent_post = relationship("BlogPost", back_populates="comments")

    
class Users(db.Model, UserMixin): 
    __tablename__ = "users" 
    id = db.Column(db.Integer, primary_key=True)  
    name = db.Column(db.String(100))
    email = db.Column(db.String(250), nullable=False, unique=False) 
    password = db.Column(db.String(250), nullable=False, unique=False)  
    posts = relationship('BlogPost', back_populates="author") 
    comments = relationship("Comment", back_populates="comment_author") 

    def to_dict(self): 
        return { 
            "id": self.id, 
            "name": self.name, 
            "email": self.email, 
            "password": self.password, 
             "posts": self.posts
        } 
    
    @staticmethod 
    def create_user(**kwargs): 
        if 'password' in kwargs: 
            kwargs['password'] = generate_password_hash(kwargs['password'], method='pbkdf2:sha256', salt_length=8)  
        new_user = Users(**kwargs) 
        db.session.add(new_user) 
        db.session.commit() 
        return new_user 

    def to_dict_kwargs(self, **kwargs): 
        user_dict = dict() 
        for key in kwargs: 
            if hasattr(self, key): 
                user_dict[key] = getattr(self, key) 
        return user_dict 

    
# Only Admin decorator function 
def only_admin(f): 
    @wraps(f) 
    def decorator_admin(*args, **kwargs): 
      if current_user.id != 1: 
          return abort(403) 
      return f(*args, **kwargs)
    return decorator_admin 


def only_commentor(function): 
    @wraps(function) 
    def check(*args, **kwargs): 
        user = db.session.execute(db.select(Comment).where(Comment.author == current_user.id)).scalar() 
        if not current_user.is_authenticated or current_user.id != user.author_id: 
            return abort(403) 
        return function(*args, **kwargs) 
    return check 

with app.app_context():
    db.create_all()


@login_manager.user_loader 
def load_user(user_id): 
   return db.get_or_404(Users, user_id)

# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=["GET", "POST"]) 
def register(): 
    register_form = UserForm() 
    if request.method == "POST":  
        if register_form.validate_on_submit():  
            result = db.session.execute(db.select(Users).where(Users.email == register_form.email.data)) 
            user = result.scalar() 
            if user: 
                flash("You've already signed up with this email", "warning") 
                return redirect(url_for('login'))
            request_data = {key: value for key, value in register_form.data.items() if key not in ['csrf_token', 'submit']}
            new_user = Users.create_user(**request_data)  
            if new_user:
                flash("Registration succesful. Please log in", 'success')  
                login_user(new_user)
            print(new_user.to_dict()) 
        return redirect(url_for("get_all_posts"))

    return render_template("register.html", form=register_form, current_user=current_user)


 
@app.route('/login', methods=["GET", "POST"])
def login(): 
    login_form = LoginForm()  
    if request.method == "POST": 
        email = login_form.email.data  
        password = login_form.password.data 
        result = db.session.execute(db.select(Users).where(Users.email == login_form.email.data)) 
        user = result.scalar() 
        if not user: 
            flash("That email does not exist try again", "warning") 
            return redirect(url_for('login'))  
        print(email, password)
        if email and password:
            found_user = Users.query.filter_by(email=email).first() 
            if found_user: 
                if check_password_hash(found_user.password, password):  
                    flash("Congratulations. You logged in", "success")
                    login_user(found_user) 
                    return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=login_form, current_user=current_user)


@app.route('/logout') 
def logout(): 
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>", methods=["GET", "POST"]) 
@login_required
def show_post(post_id): 
    comment_form = CommentForm()
    requested_post = db.get_or_404(BlogPost, post_id)  
    if request.method == "POST":  
        if comment_form.validate_on_submit():  
            rating = comment_form.rating.data 
            
            new_comment = Comment( 
                comment = comment_form.comment.data,  
                rating = rating, 
                author_id = current_user.id, 
                post_id = post_id,
               comment_author = current_user, 
               parent_post = requested_post, 
            )   
            db.session.add(new_comment) 
            db.session.commit()  
            
    return render_template("post.html", post=requested_post, current_user=current_user, form=comment_form)


# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])  
@only_admin
def add_new_post():
    form = CreatePostForm() 
    if request.method == "POST":
        if form.validate_on_submit():
            new_post = BlogPost(
                title=form.title.data,
                subtitle=form.subtitle.data,
                body=form.body.data,
                img_url=form.img_url.data,
                author=current_user,
                date=date.today().strftime("%B %d, %Y")
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])   
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>") 
@only_admin
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=False, port=5002)
