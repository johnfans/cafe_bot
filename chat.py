from wxauto import *
import threading
lock = threading.Lock()
from concurrent.futures import ThreadPoolExecutor
pool_executor = ThreadPoolExecutor(max_workers=10)

# 获取当前微信客户端
wx = WeChat()

def boo(msg):
    with lock:
        wx.SendMsg(msg,who="文件传输助手")

pool_executor.map(boo,["aaa","bbb","ccc","ddd","eee"])