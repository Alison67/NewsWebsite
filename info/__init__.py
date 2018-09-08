import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from redis import StrictRedis

from config import config

# 初始化db
from info.utils.common import do_index_class

db = SQLAlchemy()
redis_store = None  # type: StrictRedis


def setup_log(config_name):
    """配置日志"""
    # 设置日志的记录等级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)
    # 创建日志记录器,指明日志保存的路径/每个日志文件的最大大小,保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log",maxBytes=1024*1024*100,backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter("%(levelname)s %(filename)s:%(lineno)d %(message)s")
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    # 配置项目日志
    setup_log(config_name)
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    # 初始化一个sqlALchemy对象
    db.init_app(app)
    # 创建redis存储对象
    global redis_store
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST,port=config[config_name].REDIS_PORT,decode_responses=True)
    # 开启CSRF保护
    CSRFProtect(app)
    # 设置session保存指定位置
    Session(app)
    # 将自己定义的过滤器添加到app中
    app.add_template_filter(do_index_class,"index_class")
    @app.after_request
    def after_request(response):
        # 生成随机的csrf_token
        csrf_token = generate_csrf()
        # 设置cookie
        response.set_cookie("csrf_token",csrf_token)
        return response

    # 将蓝图注册到app里
    from info.modules.index import index_blu
    app.register_blueprint(index_blu)

    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)
    # 切记一定要返回一个app,否则创建不成功
    return app