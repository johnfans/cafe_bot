# cafe_bot
# 咖啡馆小樊bot
项目目前已更新至最新版本的框架，但仍然部分缺少注释，编码过程中有问题随时群里联系。

## 项目技术栈及依赖
- 开发语言：Python
- 核心框架：wxauto
  [框架地址](https://github.com/cluic/wxauto)
- 其他依赖：Flask，flask_sqlalchemy，火山引擎SDK，numpy等
- 数据库：MySQL

## 环境要求
仅可使用 ** Windows ** win7及以上或winserver2012及以上

Python 3.10及以上

wxauto 39.1.18版本

微信电脑版 3.9.12

Flask 3.1.1以上

火山引擎SDK 3.0.9以上

numpy 2.0以上

MySQL 8.0以上 推荐用navicat管理，防止sql文件执行异常。


## 基本模块

listen.py: 主函数，经常什么都往里塞，主要塞流程控制和对话

gacha.py: 抽卡算法模块

db_execute.py: 和主流程无关的数据库操作放这里

setu.py: 对接海星来来涩图接口

llm.py: 对接火山引擎大模型


## 快速开始
### 第一步
安装wxauto框架，由于原作者停止维护了，所以从我那里clone下来后安装
```bash
git clone https://github.com/johnfans/wxauto.git

cd "path-to-wxauto"

pip install -e .
```

### 第二步
搭建数据库。直接用导航猫连接你的MySQL数据库，运行sql_struct里面的所有sql文件。

### 第三步
安装必要的库
```bash
#安装火山引擎SDK
pip install volcengine-python-sdk[ark]
#安装数据库驱动
pip install pyodbc,PyMySQL
#安装flask框架及数据库连接池
pip install flask,flask_sqlalchemy
```


### 第四步
编辑环境变量 ARK_API_key 为你的火山引擎密钥

### 第五步
clone该仓库，修改.vscode中设置的python额外路径到wxauto库的路径，项目目录下创建文件夹0，1，2放入你的抽卡素材。创建文件夹temp用于收集下载的图片。修改跟踪的群聊名称。完成后启动运行listen.py启动服务。





