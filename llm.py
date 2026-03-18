
import os
# 升级方舟 SDK 到最新版本 pip install -U 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark
key=os.environ.get('ARK_API_KEY')

client = Ark(
    # 从环境变量中读取您的方舟API Key
    api_key=key,
    # 深度思考模型耗费时间会较长，请您设置较大的超时时间，避免超时，推荐30分钟以上
    timeout=120,
    )


def llm(text,job="请你总结上述群聊的聊天记录"):
    global client
    try:
        response = client.chat.completions.create(
            # 替换 <Model> 为Model ID
            model="doubao-seed-1-8-251228",
            messages=[
                {"role": "user", "content": text},
                {"role": "system", "content": job}
            ]
        )
        return response.choices[0].message.content.replace('*','')
    except Exception as e:
        print("error:",e)
        return "访问异常"

    

if __name__ == "__main__":
    job = "你是一个聊天记录总结器。"
    text = '''
'''
    print(llm(text))