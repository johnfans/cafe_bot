import os
import requests
from urllib.parse import urlparse
import uuid
import time

def download_image():
    for _ in range(3):
        try:
            url="https://moe.starfishdl.site/api/setu/v1"
            response = requests.get(url, stream=True)
            response.raise_for_status()
            # 获取文件扩展名
            parsed = urlparse(url)
            ext = os.path.splitext(parsed.path)[1] or '.jpg'
            # 生成唯一文件名
            filename = f"{uuid.uuid4().hex}{ext}"
            save_dir = './temp'
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            
        except Exception as e:
            time.sleep(1)
            print(f"Error downloading image: {e}, retrying...")
            continue

        else:
            return filename
    return False

    

if __name__ == '__main__':
    ret=download_image()
    print(ret)