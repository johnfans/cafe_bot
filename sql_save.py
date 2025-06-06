from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost:3306/dbname'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

# 查询所有用户
def get_all_users():
    return User.query.all()

# 插入新用户
def add_user(name):
    user = User(name=name)
    db.session.add(user)
    db.session.commit()
    return user

# 示例用法
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        add_user('Alice')
        users = get_all_users()
        for user in users:
            print(user.id, user.name)