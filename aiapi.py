import requests
import os
from volcenginesdkarkruntime import Ark


def query_pdl_api(question: str) :
    
    # 1. 构造请求头（指定JSON格式）
    headers = {
        "Content-Type": "application/json"
    }
    api_key ="j9547m8346atr"
    model = "gemini-2.5-flash",
    api_url = "https://moe.starfishdl.site/api/aigc/gemini-chat"

    # 2. 构造请求体（完全匹配你提供的请求结构）
    payload = {
        "key": api_key,
        "message": question,
        "model": model
    }

    try:
        # 3. 发送POST请求（设置30秒超时，避免无限等待）
        response = requests.post(
            url=api_url,
            json=payload,
            headers=headers,
            timeout=30
        )

        # 4. 检查HTTP响应状态（非200直接抛出异常）
        response.raise_for_status()

        # 5. 解析JSON响应
        resp_data = response.json()

        # 6. 检查业务状态码（接口自定义的code字段）
        if resp_data.get("code") != 200:
            print(f"接口业务错误：{resp_data.get('msg', '未知错误')}")
            return None

        # 7. 提取回答内容（严格匹配响应结构）
        content = resp_data.get("data", {}).get("content", {})
        parts = content.get("parts", [])
        
        if not parts:
            print("未获取到有效回答内容")
            return None

        # 取第一个part的text（响应结构中仅包含1个part）
        answer = parts[0].get("text", "")
        return answer+"\n喵~"

    except requests.exceptions.RequestException as e:
        print(f"网络请求异常：{str(e)}")
        return None
    except Exception as e:
        print(f"响应处理异常：{str(e)}")
        return None
    


# 从环境变量中获取您的API KEY，配置方法见：https://www.volcengine.com/docs/82379/1399008
def query_doubao_api(question: str):
    api_key = os.getenv('ARK_API_KEY')

    client = Ark(
        base_url='https://ark.cn-beijing.volces.com/api/v3',
        api_key=api_key,
    )

    try:
        response = client.responses.create(
            model="doubao-seed-2-0-pro-260215",
            tools=[
                {
                    "type": "web_search",
                    "max_keyword": 5
                }
            ],
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": question
                        }
                    ]
                }
            ]
        )
    except Exception as e:
        print(f"请求Doubao API异常：{str(e)}")
        return None

    return response.output[-1].content[0].text


# ------------------------------
# 📌 函数使用示例（替换为你的真实信息）
# ------------------------------
if __name__ == "__main__":
   
    # 提问示例（和你截图中的问题一致）
    question = "今天黄金价格是多少？"
    answer = query_doubao_api(
        question
    )

    if answer:
        print("\n✅ AI回答：")
        print(answer)
    else:
        print("\n❌ 获取回答失败")