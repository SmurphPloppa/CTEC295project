from flask import Flask, request, render_template, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secretive_Key"

# SQLAlchemy setup
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///user.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# To-Do Model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Comment Model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    task_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Initialize the database
with app.app_context():
    db.create_all()

# Home Route
@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

# Login Route
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session["username"] = username
        session["user_id"] = user.id
        return redirect(url_for("dashboard"))
    else:
        flash("Invalid username or password")
        return redirect(url_for("home"))

# Register Route
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    user = User.query.filter_by(username=username).first()

    if user:
        flash("Username already exists. Please choose another.")
        return redirect(url_for("home"))
    else:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session["username"] = username
        session["user_id"] = new_user.id
        return redirect(url_for("dashboard"))

# Dashboard Route
@app.route("/dashboard")
def dashboard():
    if "username" in session:
        user_id = session["user_id"]
        tasks = Todo.query.filter_by(user_id=user_id).all()
        return render_template("dashboard.html", tasks=tasks)
    return redirect(url_for("home"))

# Add To-Do Route
@app.route("/add", methods=["POST"])
def add_todo():
    if "username" in session:
        content = request.form.get("content")
        user_id = session["user_id"]
        new_todo = Todo(content=content, user_id=user_id)
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return redirect(url_for("home"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_todo(id):
    if "username" in session:
        task = Todo.query.get_or_404(id)
        if task.user_id == session["user_id"]:  # Ensure the user owns the task
            if request.method == "POST":
                task.content = request.form.get("content")
                db.session.commit()
                return redirect(url_for("dashboard"))
            return render_template("edit.html", task=task)
    return redirect(url_for("home"))


# Delete Task Route
@app.route("/delete/<int:id>")
def delete_todo(id):
    if "username" in session:
        todo = Todo.query.get_or_404(id)
        if todo.user_id == session["user_id"]:  # Ensure the user owns the task
            db.session.delete(todo)
            db.session.commit()
        return redirect(url_for("dashboard"))
    return redirect(url_for("home"))

# Add Comment Route
@app.route("/comment/<int:task_id>", methods=["POST"])
def add_comment(task_id):
    if "username" in session:
        content = request.form.get("comment")
        user_id = session["user_id"]
        new_comment = Comment(content=content, task_id=task_id, user_id=user_id)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("view_task", task_id=task_id))
    return redirect(url_for("home"))

# View Task with Comments
@app.route("/task/<int:task_id>")
def view_task(task_id):
    if "username" in session:
        task = Todo.query.get_or_404(task_id)
        comments = Comment.query.filter_by(task_id=task_id).all()
        return render_template("task.html", task=task, comments=comments)
    return redirect(url_for("home"))

# Logout Route
@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("user_id", None)
    return redirect(url_for("home"))

# Run the App
if __name__ == '__main__':
    app.run(debug=True)
