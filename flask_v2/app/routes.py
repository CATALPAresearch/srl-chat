from app import app, db
from app.models import User

import sqlalchemy as sa


@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"


@app.route('/user/<id>')
def get_user(id):
    user = db.session.scalar(
        sa.select(User).where(User.id == id))
    if user is None:
        return "User not found", 404
    return user.client
