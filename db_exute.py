from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import threading
lock = threading.Lock()




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Fzm&20011202@localhost:3306/wx_record'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 15
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30

db = SQLAlchemy(app)
   
def insert_moto_to_db(name, word,chat):
    global app, db, lock
    with app.app_context():
        try:
            sql = text("""
            INSERT INTO moto (name, word)
            VALUES (:name, :word)
                    """)
            params = {
                'name': name,
                'word': word
            }
            db.session.execute(sql, params)
            db.session.commit()
            with lock:
                chat.SendMsg(f"已收录：{name} - {word}")
            
        except Exception as e:
            print(f"Error inserting moto to DB: {e}")
            db.session.rollback()
            with lock:
                chat.SendMsg("收录失败，内容重复")

def select_record(group, limit=2000):
    limit = int(min(limit, 2000))  # 限制最大查询条数为2000
    with app.app_context():
        sql = text("""
        SELECT * FROM record WHERE chat = :group
        ORDER BY id DESC LIMIT"""+ f" {limit}")
        params = {'group': group}
        result = db.session.execute(sql, params)
        return result.fetchall()
    
def select_record_by_time(group, minutes=10):
    minutes = int(min(minutes, 1500))  # 限制最大查询时间为1500分钟
    with app.app_context():
        sql = text("""
        SELECT * FROM record WHERE chat = :group AND time >= NOW() - INTERVAL :minutes MINUTE
        ORDER BY id DESC""")
        params = {'group': group, 'minutes': minutes}
        result = db.session.execute(sql, params)
        return result.fetchall()

def select_moto(name,chat):
    global app, db, lock
    with app.app_context():
        try:
            sql = text("""
            SELECT m.word
            FROM name_relate nr
            JOIN moto m ON nr.name = m.name
            WHERE nr.atname = :atname
            """)
            params = {'atname': name}
            result = db.session.execute(sql, params)
            motos=result.fetchall()
            if motos:
                response = f"以下是{name}的语录\n\n" + ("\n".join([f"{moto.word}" for moto in motos]))
            else:
                response = f"没有找到{name}的语录"
            
        except Exception as e:
            print(f"Error selecting moto from DB: {e}")
            response = "查询失败"

        finally:
            with lock:
                chat.SendMsg(response)

def select_moto_with_keyword(name,chat,keyword):
    global app, db, lock
    with app.app_context():
        try:
            sql = text("""
            SELECT m.word
            FROM name_relate nr
            JOIN moto m ON nr.name = m.name
            WHERE nr.atname = :atname
            """)
            params = {'atname': name}
            result = db.session.execute(sql, params)
            motos=result.fetchall()
            if motos:
                filtered = [moto.word for moto in motos if keyword in moto.word]
                if filtered:
                    response = f"以下是{name}包含{keyword}的语录\n\n" + ("\n".join(filtered))
                else:
                    response = f"没有找到{name}包含{keyword}的语录"
            else:
                response = f"没有找到{name}的语录"
            
        except Exception as e:
            print(f"Error selecting moto from DB: {e}")
            response = "查询失败"

        finally:
            with lock:
                chat.SendMsg(response)

def select_moto_random(chat, name=None):
    global app, db, lock
    with app.app_context():
        try:
            if name:
                sql = text("""
                SELECT m.*
                FROM name_relate nr
                JOIN moto m ON nr.name = m.name
                WHERE nr.atname = :atname
                ORDER BY RAND() LIMIT 1
                """)
                params = {'atname': name}
            else:
                sql = text("""
                SELECT m.*
                FROM name_relate nr
                JOIN moto m ON nr.name = m.name
                ORDER BY RAND() LIMIT 1
                """)
                params = {'atname': name}
            result = db.session.execute(sql, params)
            moto=result.fetchone()
            if moto:
                response = f"随机语录：{moto.word} —— {moto.name}"
            else:
                response = f"没有找到语录"
        except Exception as e:
            response = f"查询失败"
            print(f"Error selecting moto from DB: {e}")
        
        finally:
            with lock:
                chat.SendMsg(response)
            

def service_judge(person,service,group,time,threshold):
    with app.app_context():
        if person == 'ALL':
            sql = text("""
                SELECT COUNT(*) FROM request
                WHERE chat = :group AND time >= NOW() - INTERVAL :minutes MINUTE
            """)
            params = {'group': group, 'minutes': time}
        else:
            sql = text("""
                SELECT COUNT(*) FROM request
                WHERE chat = :group AND time >= NOW() - INTERVAL :minutes MINUTE AND name = :person
            """)
            params = {'group': group, 'minutes': time, 'person': person}
        result = db.session.execute(sql, params)
        count = result.scalar()
        if count>=threshold:
            return False
        else:
            try:
                
                sql_insert = text("""
                    INSERT INTO request (name, time, chat, service)
                    VALUES (:name, NOW(), :chat, :service)
                """)
                params_insert = {'name': person, 'chat': group, 'service': service}
                db.session.execute(sql_insert, params_insert)
                db.session.commit()
                
            except Exception as e:
                print(f"Error inserting message to DB: {e}")
                db.session.rollback()
                
            finally:
                return True
            
def motto_operate(atname, word, chat):
    global app, db, lock
    with app.app_context():
        try:
            sql = text("""
            SELECT name FROM name_relate WHERE atname = :atname
            LIMIT 1
            """)
            params = {'atname': atname}
            name2 = db.session.execute(sql, params).scalar()

            if name2:
                sql = text("""
                SELECT name FROM record WHERE time >= NOW() - INTERVAL 12 HOUR
                AND content = :word AND name = :name2
                ORDER BY id DESC LIMIT 1
                """)
                params = {'word': word, 'name2': name2}
                result = db.session.execute(sql, params)
                name1 = result.scalar()
                if name1 is None:
                    return -2
                else:
                    insert_moto_to_db(name1, word, chat)
                return 1


            else:
                sql = text("""
                SELECT name FROM record WHERE time >= NOW() - INTERVAL 12 HOUR
                AND content = :word 
                ORDER BY id DESC LIMIT 1
                """)
                params = {'word': word}
                result = db.session.execute(sql, params)
                name1 = result.scalar()
                if name1 is None:
                    return -1
                
                else:
                    sql = text("""
                    INSERT INTO name_relate (atname, name)
                    VALUES (:atname, :name)
                    """)
                    params = {'atname': atname, 'name': name1}
                    db.session.execute(sql, params)
                    db.session.commit()

                    insert_moto_to_db(name1, word, chat)
                    return 0
            
            

        except Exception as e:
            print(f"Error processing motto: {e}")
            db.session.rollback()
            return -3
        
def motto_process(atname, word, chat):
    global app, db, lock
    ret=motto_operate(atname, word, chat)
    if ret == -1:
        with lock:
            chat.SendMsg("找不到引用喵~")
    elif ret == 0:
        with lock:
            chat.SendMsg(f"已关联：{atname} ")
    elif ret == -2:
        with lock:
            chat.SendMsg(f"{atname}关联冲突，如果不是整活请联系小樊处理")
    elif ret == -3:
        with lock:
            chat.SendMsg("发生错误了喵~，请提交issue")
            


        