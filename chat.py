from wxauto import *


# 获取当前微信客户端
wx = WeChat()


# 获取会话列表
wx.GetSessionList()

# 向某人发送消息（以`文件传输助手`为例）
# msg = '你好~'
# who = '文件传输助手'
# wx.SendMsg(msg, who)  # 向`文件传输助手`发送消息：你好~



wx.ChatWith('咖啡馆大群')


# 下载当前聊天窗口的聊天记录及图片
msgs = wx.GetAllMessage(savepic=False)   # 获取聊天记录，及自动下载图片
formatted_msgs = "\n".join([f"{msg[0]}：{msg[1]}" for msg in msgs])
    
print(formatted_msgs)  # 打印聊天记录