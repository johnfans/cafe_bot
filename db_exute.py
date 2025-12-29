from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import random
import threading
lock = threading.Lock()




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Fzm&20011202@localhost:3306/wx_record'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 15
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30

db = SQLAlchemy(app)

with app.app_context():
    results=db.session.execute(text("SELECT * FROM moto ORDER BY RAND()"))
    moto_list=results.fetchall()
    moto_index=0

def append_motto_tolist(name,word):
    global moto_list
    idx = random.randint(0, len(moto_list))
    moto_list.insert(idx, (name,word))
   
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
                chat.SendMsg(f"已收录：{name} - {word}喵~")
            
        except Exception as e:
            print(f"Error inserting moto to DB: {e}")
            db.session.rollback()
            with lock:
                chat.SendMsg("收录失败，内容重复喵~")

def select_record(group, limit=2000):
    limit = int(min(limit, 2000))  # 限制最大查询条数为2000
    with app.app_context():
        sql = text("""
            SELECT * FROM record WHERE chat = :group
            ORDER BY id DESC
            LIMIT :limit OFFSET 1
            """)
        params = {'group': group, 'limit': limit}
        result = db.session.execute(sql, params)
        return result.fetchall()
    
def select_record_by_time(group, minutes=10):
    minutes = int(min(minutes, 1500))  # 限制最大查询时间为1500分钟
    with app.app_context():
        sql = text("""
        SELECT * FROM record WHERE chat = :group AND time >= NOW() - INTERVAL :minutes MINUTE
        ORDER BY id DESC OFFSET 1""")
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
                response = f"以下是{name}的语录喵~\n\n" + ("\n".join([f"{moto.word}" for moto in motos]))
            else:
                response = f"没有找到{name}的语录喵~"
            
        except Exception as e:
            print(f"Error selecting moto from DB: {e}")
            response = "查询失败喵~"

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
                    response = f"以下是{name}包含{keyword}的语录喵~\n\n" + ("\n".join(filtered))
                else:
                    response = f"没有找到{name}包含{keyword}的语录喵~"
            else:
                response = f"没有找到{name}的语录喵~"
            
        except Exception as e:
            print(f"Error selecting moto from DB: {e}")
            response = "查询失败喵~"

        finally:
            with lock:
                chat.SendMsg(response)

def select_moto_random(chat, name=None):
    global app, db, lock,moto_list,moto_index
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
                result = db.session.execute(sql, params)
                moto=result.fetchone()
            else:
                if moto_index >= len(moto_list):
                    results=db.session.execute(text("SELECT * FROM moto ORDER BY RAND()"))
                    moto_list=results.fetchall()
                    moto_index=0
                moto=moto_list[moto_index]
                moto_index+=1
            if moto:
                response = f"随机语录：\n{moto[1]} —— {moto[0]}"
            else:
                response = f"没有找到语录喵~"
        except Exception as e:
            response = f"查询失败喵~"
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
                AND service = :service
            """)
            params = {'group': group, 'minutes': time, 'service': service}
        else:
            sql = text("""
                SELECT COUNT(*) FROM request
                WHERE chat = :group AND time >= NOW() - INTERVAL :minutes MINUTE AND name = :person
                AND service = :service
            """)
            params = {'group': group, 'minutes': time, 'person': person, 'service': service}
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
                    append_motto_tolist(name1, word)
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
                    append_motto_tolist(name1, word)
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
            chat.SendMsg(f"已关联：{atname} 喵~")
    elif ret == -2:
        with lock:
            chat.SendMsg(f"{atname}关联冲突，如果不是整活请联系小樊处理喵~")
    elif ret == -3:
        with lock:
            chat.SendMsg("发生错误了喵~，请提交issue喵~")

def auth_judge(person,level):
    with app.app_context():
        try:
            sql = text("SELECT COUNT(*) FROM super_user WHERE name = :person AND auth <= :level")
            result = db.session.execute(sql, {'person': person, 'level': level})
            count = result.scalar() or 0
            return count > 0
        except Exception as e:
            print(f"Error checking super_user: {e}")
            return False
            
def exec_sql(sql_command):
    global app, db, lock
    with app.app_context():
        try:
            sql = text(sql_command)
            result = db.session.execute(sql)
            db.session.commit()
            rows = result.fetchall()
            if rows:
                response = "\n".join([str(row) for row in rows])
            else:
                response = "执行成功，但没有返回结果喵~"
        except Exception as e:
            db.session.rollback()
            response = f"执行失败喵~ 错误信息: {e}"
        finally:
            return response
        

        

        