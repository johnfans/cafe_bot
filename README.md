# cafe_bot
# 咖啡馆小樊bot
项目目前代码不规范，注释混乱，且依赖版本过旧。目前仅供群友嘲笑，不开放给群友编辑。将在代码整理完后开放权限。

有需要微信里找小樊，不认识我的当没看见这个项目。

## 项目技术栈及依赖
- 开发语言：Python
- 核心框架：wxauto
  [框架地址](https://github.com/cluic/wxauto)
- 其他依赖：Flask，flask_sqlalchemy，火山引擎SDK，numpy等
- 数据库：MySQL

## 环境要求
仅可使用 ** Windows ** win7及以上或winserver2012及以上

Python 3.10及以上

wxauto 3.9.11.17.5版本（后续会更新到开源版最新版本）

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
现在快速开始不了一点



