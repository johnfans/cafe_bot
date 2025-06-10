from wxauto import WeChat
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor
from setu import *
from llm import *
import threading
lock = threading.Lock()

# 创建一个线程池，最大线程数为10
pool_executor = ThreadPoolExecutor(max_workers=10)
pool2_executor = ThreadPoolExecutor(max_workers=5)
pool3_executor = ThreadPoolExecutor(max_workers=5)
greet = '''Ciallo～(∠・ω< )⌒★,version: 0.0.2

/help 查看本消息

/获取 [条目/时间] [条目数/分钟数] [群内/私聊] 获取聊天记录的txt
示例：/获取 条目 100 群内 ，意思是获取当前最新的100条群消息的txt

/总结 [条目/时间] [条目数/分钟数] [群内/私聊] 使用llm总结聊天记录
示例：/总结 条目 100 群内 ，意思是总结当前最新的100条群消息

/来一份图 来一份二次元美图（感谢东来哥的api）

/issue [内容] bug反馈

/班味排行榜 

注：私聊选项目前尚未测试，可能不太好使。

'''

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Fzm&20011202@localhost:3306/wx_record'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 15
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
now_id = 0  # 用于记录当前record表id的最大值
db = SQLAlchemy(app)
with app.app_context():
    # 查询record表id字段的最大值，使用SQLAlchemy连接池
    result = db.session.execute(text("SELECT MAX(id) FROM record"))
    now_id = result.scalar()+1


def insert_message_to_db(group,msg,index):
    global app, db, now_id
    if msg.type != 'friend' and msg.type != 'self' and msg.type != 'group':
        return False
    conten=msg[1].split('引用  的消息')[0]
    if len(conten)>500:
        return False
    with app.app_context():
        try:
            sql = text("""
            INSERT INTO record (id, chat, name, time, content)
            VALUES (:id, :group, :name, NOW(), :content)
                    """)
            params = {
                'id': now_id+index,
                'group': group,
                'name': msg[0],
                'content': conten  # 不存储引用部分
            }
            db.session.execute(sql, params)
            db.session.commit()
            return now_id+index
        except Exception as e:
            print(f"Error inserting message to DB: {e}")
            db.session.rollback()
            return False
   

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
    minutes = int(min(minutes, 1440))  # 限制最大查询时间为1440分钟
    with app.app_context():
        sql = text("""
        SELECT * FROM record WHERE chat = :group AND time >= NOW() - INTERVAL :minutes MINUTE
        ORDER BY id DESC""")
        params = {'group': group, 'minutes': minutes}
        result = db.session.execute(sql, params)
        return result.fetchall()

def response_to_user(chat, count, scope, group, msg):
    global wx
    try:
        records = select_record(group, int(count))
        filename = f"./temp/{group}-"+time.strftime("%Y%m%d-%H%M%S",time.localtime())+"-records.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for record in reversed(records):
                f.write(f"{record.name}: {record.content}\n")
        with lock:
            if scope == '群内':
                chat.SendFiles(filename)
            elif scope == '私聊':
                wx.SendFiles(filename, who=msg.sender)    
    except Exception as e:
        print(f"Error responding to user: {e}")

def response_to_user2(chat, minute, scope, group, msg):
    global wx
    try:
        records = select_record_by_time(group, minute)
        filename = f"./temp/{group}-"+time.strftime("%Y%m%d-%H%M%S",time.localtime())+"-records.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for record in reversed(records):
                f.write(f"{record.name}: {record.content}\n")
        with lock: 
            if scope == '群内':
                chat.SendFiles(filename)
            elif scope == '私聊':
                wx.SendFiles(filename, who=msg.sender)    
    except Exception as e:
        print(f"Error responding to user: {e}")

def conclusion_process(chat, count, scope, group, msg, type):
    global wx
    try:
        if type == 2:
            records = select_record_by_time(group, count)
        else:
            records = select_record(group, int(count))
        
        text_content = "\n".join([f"{record.name}: {record.content}" for record in reversed(records)])
        
        
        response=llm(text_content)
        with lock:
            if scope == '群内':
                chat.SendMsg(response)
            elif scope == '私聊':
                wx.SendMsg(response, who=msg.sender) 
    
    except Exception as e:
        print(f"Error responding to user: {e}")

def toil_rank(chat):
    records = select_record_by_time(chat.who, 1440)
    text_content = "\n".join([f"{record.name}: {record.content}" for record in reversed(records)])
    response = llm(text_content,job="在以下的消息记录中，请你总结谁讨论上班话题最多，并给出排名")
    with lock:
        chat.SendMsg(response)

def daily_news(group):
    global flag1,wx
    try:
        records = select_record_by_time(group, 1440)
        text_content = "\n".join([f"{record.name}: {record.content}" for record in reversed(records)])
        response = llm(text_content,job="请你总结聊天记录生成群聊日报")
        today = time.strftime("%Y-%m-%d", time.localtime())
        weekday = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][time.localtime().tm_wday]
        dictum = ["好可爱啊，想看你加班", "嗨，想班了吗？", "已在工位，消息秒回", "最喜欢可爱的班班了", "周末愉快，上班就是为了不上班", "周末愉快，但是还有14个小时就周一了"][time.localtime().tm_wday]
        with lock:
            if group != "咖啡馆大群":
                wx.SendMsg(f"今天是 {today}，{weekday}\n{dictum}\n{response}",who=group)
            else:
                wx.SendMsg(f"今天是 {today}，{weekday}\n{response}",who=group)
        
    except Exception as e:
        print(e)
    
    finally:
        time.sleep(60)
        flag1=0

def setu_process(chat):
    try:
        global wx
        with lock:
            chat.SendMsg('好吧好吧，就给你一张吧')
        filename = download_image()
        with lock:
            if filename:
                chat.SendFiles(f'./temp/{filename}')
            else:
                chat.SendMsg('下载图片失败了呢，555...')
    except Exception as e:
        print(f"Error in setu_process: {e}")

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


def order_analysis(msg, chat, group):
    global wx
    try:
        parts = msg[1].split('\n')[0].split()
        if parts[0][1:] == 'help' or parts[0][1:] == '帮助':
            chat.SendMsg(greet)
        elif ('发' in parts[0][1:4] or '来' in parts[0][1:4]) and '图' in parts[0][2:]:
            #TODO:这里有时间把异步做了
            if group == "咖啡馆大群":
                if service_judge("ALL","setu",group,1440,5):
                    pool2_executor.submit(setu_process, chat)
                else:
                    chat.SendMsg("杂鱼，一天之内只能要五张哦")
            else:
                if service_judge(msg[0],"setu",group,1,1):
                    pool2_executor.submit(setu_process, chat)
                else:
                    chat.SendMsg("杂鱼，不要涩涩的这么频繁啊")

        elif parts[0][1:3] == '获取':
            if len(parts) >= 4:
                command = parts[1]
                count = int(parts[2])
                scope = parts[3]
                if command == '条目':
                    chat.SendMsg(f'正在获取{group}的最新{count}条记录，请稍等...')
                    pool2_executor.submit(response_to_user, chat, count, scope, group, msg)
                elif command == '时间':
                    chat.SendMsg(f'正在获取{group}的{count}分钟内的记录，请稍等...')
                    pool2_executor.submit(response_to_user2, chat, count, scope, group, msg)
                    pass
            else:
                chat.SendMsg(f'命令解析失败')
        
        elif parts[0][1:3] == '总结':
            if len(parts) >= 4:
                command = parts[1]
                count = int(parts[2])
                scope = parts[3]
                if command == '条目':
                    chat.SendMsg(f'正在总结{group}的最新{count}条记录，请稍等...')
                    pool3_executor.submit(conclusion_process, chat, count, scope, group, msg, 1)
                elif command == '时间':
                    chat.SendMsg(f'正在总结{group}的{count}分钟内的记录，请稍等...')
                    pool3_executor.submit(conclusion_process, chat, count, scope, group, msg, 2)
                    pass
            else:
                chat.SendMsg(f'命令解析失败')
        
        elif parts[0][1:6] == '班味排行榜':
            chat.SendMsg(f'正在生成最近24小时的班味排名')
            pool3_executor.submit(toil_rank,chat)


        elif parts[0][1:] == 'issue':
            chat.SendMsg("已收到反馈，呼叫小樊")

        else:
            chat.SendMsg(f'未知命令，请输入 /help 查看帮助信息')
    except Exception as e:
        print(f"Error in order_analysis: {e}")
        if e == IndexError:
            chat.SendMsg(f'命令解析失败，请检查输入格式是否正确')


wx = WeChat()

# 首先设置一个监听列表，列表元素为指定好友（或群聊）的昵称
listen_list = [
    '咖啡馆大群',
    '咖啡馆打工人分部',
    '咖啡馆大湾区分馆',
]

flag1 = 0    

# 然后调用`AddListenChat`方法添加监听对象，其中可选参数`savepic`为是否保存新消息图片
for i in listen_list:
    wx.AddListenChat(who=i)

wait = 1  # 设置3秒查看一次是否新消息

while True:
    try:
        msgs = wx.GetListenMessage()
        #print("msgs",msgs)
        for chat in msgs:
            group=chat.who  # 获取聊天对象的昵称
            one_msgs = msgs.get(chat)   # 获取消息内容
            ret=pool_executor.map(insert_message_to_db, [group] * len(one_msgs), one_msgs,range(len(one_msgs)))  # 异步插入消息到数据库
            print(list(ret))  # 打印插入结果
            now_id += len(one_msgs)
            # 消息处理
            for msg in one_msgs:
                if (msg[1] == None) or (msg[1] == ''):
                    continue
                if msg.type == 'sys':
                    print(f'【系统消息】{msg.content}')
                
                elif msg.type == 'friend' or msg.type == 'group' or msg.type == 'self':
                    print(msg)
                    if msg[1][0] == '/':
                        with lock:
                            order_analysis(msg, chat, group)

        if time.localtime().tm_hour==10 and time.localtime().tm_min==0 and flag1 == 0:
            flag1 = 1
            for thegroup in listen_list:
                pool3_executor.submit(daily_news,thegroup)

                # elif msg.type == 'time':
                #     print(f'\n【时间消息】{msg.time}')
        
                # elif msg.type == 'recall':
                #     print(f'【撤回消息】{msg.content}')
        time.sleep(wait)  # 等待一段时间后继续监听
    except KeyboardInterrupt:
        print('Bye~')
        break
