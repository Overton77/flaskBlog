from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, SelectField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])  
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post") 


# TODO: Create a RegisterForm to register new users 
    
class UserForm(FlaskForm):  
    name = StringField("Name", validators=[DataRequired()]) 
    email = EmailField("Email", validators=[DataRequired()]) 
    password = PasswordField("Password", validators=[DataRequired()])  
    submit = SubmitField("Submit") 



# TODO: Create a LoginForm to login existing users  
class LoginForm(FlaskForm): 
    email = EmailField("Email", validators=[DataRequired()]) 
    password = PasswordField("Password", validators=[DataRequired()]) 
    submit = SubmitField("Submit")


# TODO: Create a CommentForm so users can leave comments below posts 
class CommentForm(FlaskForm): 
    rating =  SelectField('Rating', choices=[(0, 'zero'), (1, 'one'), (2, 'two'), (3, 'three'), (4, 'four'), (5, 'five')], validators=[DataRequired()])
    comment = CKEditorField('Comment', validators=[DataRequired()]) 
    submit = SubmitField("Submit")