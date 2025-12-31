from wxauto import WeChat
from wxauto.msgs import FriendMessage
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor
from setu import *
from llm import *
from gacha import *
from db_exute import *
import threading
import os
import random

import numpy as np

# 语录伪随机
# 全局变量和初始化
# with app.app_context():
#     result=db.session.execute(text("SELECT value FROM global WHERE name = 'chouka_count'"))
#     chouka_count=int(result.fetchone()[0]) if result else 0

chouka = GachaSimulator()
flag1 = 0

# 创建一个线程池，最大线程数为10
pool_executor = ThreadPoolExecutor(max_workers=10)
pool2_executor = ThreadPoolExecutor(max_workers=5)
pool3_executor = ThreadPoolExecutor(max_workers=5)
wx = WeChat()
greet = '''Ciallo～(∠・ω< )⌒★,
这里是代号：泛用型小樊（还没拿到版号555）

命令前加斜杠：
help查看本消息
总结 [条目数/分钟数][条/分]
来一份图
抽卡
issue
班味排行榜
班味比重榜
收录@群友
语录@群友

找真人小樊询问详细使用方法。
根据相关规定，应答时间调整至3-5秒，且2点-8点不会应答消息。
问就是未成年人保护系统。
'''
'''

/help 查看本消息


/总结 [条目/时间] [条目数/分钟数] [群内/私聊] 使用llm总结聊天记录
可简化为 /总结 [条目数/分钟数][条/分]
示例：/总结 条目 100 群内 或/总结 100条，意思是总结当前最新的100条群消息

/来一份图 来一份二次元美图（感谢东来哥的api）

/issue [内容] bug反馈

/班味排行榜 

注：私聊选项目前尚未测试，可能不太好使。

'''


def insert_message_to_db(group,msg):
    global app, db
    if msg.sender == "system" or msg.type == "base":
        return False
    conten=msg.content
    usr = msg.sender
    if len(conten)>500:
        return False
    
    if msg.sender == 'self':
        if len(conten) >100 or conten == '[图片]':
            return False
        elif ("喵~" in conten) or ("杂鱼" in conten) or ("记录在总结中" in conten) or ("记录在分析中" in conten) or ("已关联" in conten) or ("已收录" in conten) or ("随机语录" in conten):
            usr = "bot"
        else:
            usr = "南航大-樊卓铭"
    
    with app.app_context():
        try:
            sql = text("""
            INSERT INTO record (chat, name, time, content)
            VALUES (:group, :name, NOW(), :content)
                    """)
            params = {
                'group': group,
                'name': usr,
                'content': conten  # 不存储引用部分
            }
            db.session.execute(sql, params)
            db.session.commit()
            print("已插入")
            return True
        except Exception as e:
            print(f"Error inserting message to DB: {e}")
            db.session.rollback()
            return False
    

                    
        

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

def analyze_process(chat, count, group, type, prompt):
    global wx
    try:
        if type == 2:
            records = select_record_by_time(group, count)
        else:
            records = select_record(group, int(count))
        
        text_content = "\n".join([f"{record.name}: {record.content}" for record in reversed(records)])
        
        
        response=llm(text_content,job=prompt)
        with lock:
            chat.SendMsg(response)
            
    
    except Exception as e:
        print(f"Error responding to user: {e}")

def toil_rank(chat):
    records = select_record_by_time(chat.who, 1430)
    text_content = "\n".join([f"{record.name}: {record.content}" for record in reversed(records)])
    response = llm(text_content,job="在以下的消息记录中，请你统计谁讨论上班话题最多，并给出排名")
    with lock:
        chat.SendMsg(response)

def toil_rank2(chat):
    records = select_record_by_time(chat.who, 1430)
    text_content = "\n".join([f"{record.name}: {record.content}" for record in reversed(records)])
    response = llm(text_content,job="在以下的消息记录中，请你统计谁讨论上班话题所占其发言的比重最高，并给出排名")
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
        dictum = ["好可爱啊，想看你加班", "嗨，想班了吗？", "已在工位，消息秒回", "最喜欢可爱的班班了","TGIF!", "周末愉快，上班就是为了不上班", "周末愉快，但是还有14个小时就周一了"][time.localtime().tm_wday]
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
            chat.SendMsg('好吧好吧，就给你一张吧，喵~')
        filename = download_image()
        # files = os.listdir('./temp')
        # filename = random.choice(files) if files else None
        with lock:
            if filename:
                chat.SendFiles(f'./temp/{filename}')
            else:
                chat.SendMsg('下载图片失败了呢，呜喵~')
    except Exception as e:
        print(f"Error in setu_process: {e}")

def chouka_process(result,chat):
    
    with lock:
        if result == 0:
            chat.SendMsg('四星喵~')
            file = np.random.choice(os.listdir("./0"))
        elif result == 1:
            file = np.random.choice(os.listdir("./1"))
            chat.SendMsg('喵~五星常驻，'+file.split('.')[0])
        elif result == 2:
            chat.SendMsg('五星限定，园酱喵~')
            file = np.random.choice(os.listdir("./2"))
        chat.SendFiles(f'./{result}/{file}')




def order_analysis(msg, chat, group):
    global wx
    try:
        parts = msg.content.split('\n')[0].split()
        if parts[0][1:] == 'help' or parts[0][1:] == '帮助':
            chat.SendMsg(greet)
        elif ('发' in parts[0][1:4] or '来' in parts[0][1:4]) and '图' in parts[0][2:]:
            #TODO:这里有时间把异步做了
            if group == "咖啡馆大群":
                if service_judge("ALL","setu",group,1440,10):
                    pool2_executor.submit(setu_process, chat)
                else:
                    chat.SendMsg("杂鱼，一天之内只能要五张哦")
            else:
                if service_judge(msg.sender,"setu",group,2,1):
                    pool2_executor.submit(setu_process, chat)
                else:
                    chat.SendMsg("杂鱼，不要涩涩的这么频繁啊")
        
        elif parts[0][1:3] == '总结':
            if len(parts) >= 4:
                command = parts[1]
                count = int(parts[2])
                scope = parts[3]
                if command == '条目':
                    chat.SendMsg(f'{group}的最新{count}条记录在总结中喵~')
                    pool3_executor.submit(conclusion_process, chat, count, scope, group, msg, 1)
                elif command == '时间':
                    chat.SendMsg(f'{group}最新的{count}分钟的记录在总结中喵~')
                    pool3_executor.submit(conclusion_process, chat, count, scope, group, msg, 2)
                    pass

            elif len(parts) == 3:
                num = int(parts[1][:-1])
                command = parts[2]
                if command == '条':
                    chat.SendMsg(f'{group}的最新{num}条记录在总结中喵~')
                    pool3_executor.submit(conclusion_process, chat, num, "群内", group, msg, 1)
                elif command == '分' or command == '分钟':
                    chat.SendMsg(f'{group}最新的{num}分钟的记录在总结中喵~')
                    pool3_executor.submit(conclusion_process, chat, num, "群内", group, msg, 2)

            elif len(parts) == 2:
                num = int(parts[1][:-1])
                command = parts[1][-1]
                if command == '条':
                    chat.SendMsg(f'{group}的最新{num}条记录在总结中喵~')
                    pool3_executor.submit(conclusion_process, chat, num, "群内", group, msg, 1)
                elif command == '分':
                    chat.SendMsg(f'{group}最新的{num}分钟的记录在总结中喵~')
                    pool3_executor.submit(conclusion_process, chat, num, "群内", group, msg, 2)
            
            elif len(parts) == 1:
                num = int(parts[0][3:-1])
                command = parts[0][-1]
                if command == '条':
                    chat.SendMsg(f'{group}的最新{num}条记录在总结中喵~')
                    pool3_executor.submit(conclusion_process, chat, num, "群内", group, msg, 1)
                elif command == '分':
                    chat.SendMsg(f'{group}最新的{num}分钟的记录在总结中喵~')
                    pool3_executor.submit(conclusion_process, chat, num, "群内", group, msg, 2)
            
            else:
                chat.SendMsg(f'不知道你在说什么喵~？')
        
        elif parts[0][1:3] == '收录':
            if msg.type != 'quote':
                chat.SendMsg(f'收录命令需要引用一条消息喵~')
                return
            word = msg.quote_content
            if ('@' in msg.content.split('\n')[0]):
                if ("已收录：" in word) or ("以下是" in word):
                    chat.SendMsg(f'禁止套娃！喵~')
                else:
                    if service_judge(msg.sender,"motto",group,1440,5):
                        person = msg.content.split('\n')[0].split('@')[1]
                        pool2_executor.submit(motto_process, person, word, chat)
                    else:
                        chat.SendMsg("24小时之内只能收录5次喵~")
            else:
                chat.SendMsg(f'不知道你在说什么喵~？')

        elif parts[0][1:3] == '语录':
            if ('@' in msg.content.split('\n')[0]):
                if parts[0][1:5] == '语录检索' and len(parts) >=2:
                    keyword = parts[1].split('@')[0]
                    person = msg.content.split('\n')[0].split('@')[1]
                    pool2_executor.submit(select_moto_with_keyword, person, chat, keyword)
                
                elif parts[0][1:5] == '语录随机':
                    person = msg.content.split('\n')[0].split('@')[1]
                    pool2_executor.submit(select_moto_random, chat, person)
                    
                else:
                    person = msg.content.split('\n')[0].split('@')[1]
                    pool2_executor.submit(select_moto, person, chat)
            
            elif parts[0][1:5] == '语录随机':
                pool2_executor.submit(select_moto_random, chat)

            else:
                chat.SendMsg(f'不知道你在说什么喵~？')

        elif parts[0][1:3] == '抽卡':
            if group == "咖啡馆大群":
                if service_judge("ALL","setu",group,1440,10):
                    pool2_executor.submit(chouka_process, chouka.draw(), chat)
                else:
                    chat.SendMsg("杂鱼，一天之内只能要10张哦")
            else:
                if service_judge(msg.sender,"setu",group,2,1):
                    pool2_executor.submit(chouka_process, chouka.draw(), chat)
                else:
                    chat.SendMsg("杂鱼，不要涩涩的这么频繁啊")
            
            
        
        elif parts[0][1:4] == '班味排':
            chat.SendMsg(f'最近24小时的班味排名即将出炉喵~')
            pool3_executor.submit(toil_rank,chat)

        elif parts[0][1:4] == '班味比':
            chat.SendMsg(f'最近24小时的班味比重排名即将出炉喵~')
            pool3_executor.submit(toil_rank2,chat)
        
        elif parts[0][1:3] == '分析':
            if len(parts) == 4:
                num = int(parts[1][:-1])
                command = parts[2]
                prompt = parts[3]
                if command == '条':
                    chat.SendMsg(f'{group}的最新{num}条记录在分析中喵~')
                    pool3_executor.submit(analyze_process, chat, num, group, 1, prompt)
                elif command == '分' or command == '分钟':
                    chat.SendMsg(f'{group}最新的{num}分钟的记录在分析中喵~')
                    pool3_executor.submit(analyze_process, chat, num, group, 2, prompt)

            elif len(parts) == 3:
                num = int(parts[1][:-1])
                command = parts[1][-1]
                prompt = parts[2]
                if command == '条':
                    chat.SendMsg(f'{group}的最新{num}条记录在分析中喵~')
                    pool3_executor.submit(analyze_process, chat, num, group, 1, prompt)
                elif command == '分':
                    chat.SendMsg(f'{group}最新的{num}分钟的记录在分析中喵~')
                    pool3_executor.submit(analyze_process, chat, num, group, 2, prompt)
            
            elif len(parts) == 2:
                num = int(parts[0][3:-1])
                command = parts[0][-1]
                prompt = parts[1]
                if command == '条':
                    chat.SendMsg(f'{group}的最新{num}条记录在分析中喵~')
                    pool3_executor.submit(analyze_process, chat, num, group, 1, prompt)
                elif command == '分':
                    chat.SendMsg(f'{group}最新的{num}分钟的记录在分析中喵~')
                    pool3_executor.submit(analyze_process, chat, num, group, 2, prompt)
            
            else:
                chat.SendMsg(f'不知道你在说什么喵~？')

        elif parts[0][1:5] == 'sudo':
            if auth_judge(msg.sender,0):
                if parts[1] == 'sql':
                    sql_command = msg.content.split('\n',1)[1]
                    result = exec_sql(sql_command)
                    chat.SendMsg(f'SQL执行结果喵~：\n{result}')
            else:
                chat.SendMsg(f'你没有权限使用喵~')
                    

        elif parts[0][1:6] == 'issue':
            chat.SendMsg("已收到反馈喵~，呼叫小樊",at="小樊" )

        else:
            chat.SendMsg(f'不知道你在说什么喵~？')
    except Exception as e:
        print(f"Error in order_analysis: {e}")
        if e == IndexError:
            chat.SendMsg(f'理解不了你在说什么喵~')
        else:
            chat.SendMsg(f'好像有什么错误喵~')

def messege_handler(msg,chat):
    # 消息处理
    try:
        pool_executor.submit(insert_message_to_db,chat.who,msg)
        if time.localtime().tm_hour<=1 or time.localtime().tm_hour>=8:
            if (msg.content == None) or (msg.content == ''):
                return
            if msg.attr == 'system' or msg.type == 'base':
                print(f'【系统消息】{msg.content}')
            
            elif msg.attr == 'friend' or msg.attr == 'self':
                print(f'【{chat.who}】【{msg.sender}】{msg.content}')
                if msg.content[0] == '/':
                    time.sleep(random.uniform(2,5))
                    with lock:
                        order_analysis(msg, chat, "咖啡馆打工人分部")
    except Exception as e:
        print(f"Error in messege_handler: {e}")

wx.AddListenChat(nickname="咖啡馆打工人分部", callback=messege_handler)

wx.KeepRunning()




    #     if time.localtime().tm_hour==10 and time.localtime().tm_min==0 and flag1 == 0:
    #         flag1 = 1
    #         for thegroup in listen_list:
    #             pool3_executor.submit(daily_news,thegroup)

                
    #     time.sleep(wait)  # 等待一段时间后继续监听
    # except KeyboardInterrupt:
    #     print('Bye~')
    #     break
