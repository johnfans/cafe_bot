from wxauto import WeChat
from wxauto.msgs import FriendMessage
import time

wx = WeChat()

# 消息处理函数
def on_message(msg, chat):
    # 示例1：将消息记录到本地文件
    print("已触发")
    print(msg.content)
    print(msg.sender)
    print(msg.type)

    ...# 其他处理逻辑，配合Message类的各种方法，可以实现各种功能

# 添加监听，监听到的消息用on_message函数进行处理
wx.AddListenChat(nickname="咖啡馆打工人分部", callback=on_message)

# 保持程序运行
wx.KeepRunning()