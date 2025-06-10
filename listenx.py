from wxautox import WeChat
from wxautox.msgs import FriendMessage
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor
from setu import *

# 创建一个线程池，最大线程数为10
pool_executor = ThreadPoolExecutor(max_workers=10)
pool2_executor = ThreadPoolExecutor(max_workers=1)
greet = '''Ciallo～(∠・ω< )⌒★,version: 0.0.1 beta
求投喂，现急需一台能一直开机的windows服务器，一个闲置w.x账号，一个LLM的api.
因为没有api，只能需要群友先手动将聊天记录发给大模型
/help 查看本消息
/获取 [条目/时间] [条目数/分钟数] [群内/私聊] 获取聊天记录的txt
示例：/获取 条目 100 群内 ，意思是获取当前最新的100条群消息的txt
/来一份图 来一份二次元美图（感谢东来哥的api）

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
        return
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
                'content': msg[1].split('引用  的消息')[0]  # 不存储引用部分
            }
            db.session.execute(sql, params)
            db.session.commit()
            return now_id+index
        except Exception as e:
            print(f"Error inserting message to DB: {e}")
            db.session.rollback()
            return False
   

def select_record(group, limit=1000):
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
        records = select_record(group, count)
        filename = f"./temp/{group}-"+time.strftime("%Y%m%d-%H%M%S",time.localtime())+"-records.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for record in reversed(records):
                f.write(f"{record.name}: {record.content}\n")
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
        if scope == '群内':
            chat.SendFiles(filename)
        elif scope == '私聊':
            wx.SendFiles(filename, who=msg.sender)    
    except Exception as e:
        print(f"Error responding to user: {e}")

def setu_process(chat):
    try:
        global wx
        chat.SendMsg('正在获取二次元美图，请稍等...')
        filename = download_image()
        if filename:
            chat.SendFiles(f'./temp/{filename}')
        else:
            chat.SendMsg('下载图片失败，请稍后再试。')
    except Exception as e:
        print(f"Error in setu_process: {e}")

def order_analysis(msg, chat, group):
    global wx
    try:
        parts = msg[1].split('\n').split(' ')
        if parts[0][1:5] == 'help' or parts[1][1:3] == '帮助':
            chat.SendMsg(greet)
        elif ('发' in msg[1][1:4] or '来' in msg[1][1:4]) and '图' in msg[1][2:]:
            pool2_executor.submit(setu_process, chat)

        elif msg[1][1:3] == '获取':
            if len(parts) >= 4:
                parts = msg[1].split(' ')
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
    '文件传输助手',
]
    

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
                print(msg)
                if msg.type == 'sys':
                    print(f'【系统消息】{msg.content}')
                
                elif msg.type == 'friend' or msg.type == 'group' or msg.type == 'self':
                    print(msg)
                    if msg[1][0] == '/':
                        order_analysis(msg, chat, group)
                
                # elif msg.type == 'time':
                #     print(f'\n【时间消息】{msg.time}')
        
                # elif msg.type == 'recall':
                #     print(f'【撤回消息】{msg.content}')
        time.sleep(wait)  # 等待一段时间后继续监听
    except KeyboardInterrupt:
        print('Bye~')
        break
