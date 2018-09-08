import logging

from redis import StrictRedis


class Config(object):
    """工程配置信息"""

    SECRET_KEY = "eRu7C5x9P2Pe4ov4W+1IuNzsqu7Vo0zZ1cM0TksGCK403/PLzfMOcjdneiws6d0I"
    """导入数据库扩展"""
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:mysol@127.0.0.1:3306/information"
    # 动态追踪修改设置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 数据库中修改数据自动提交
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    # redis配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # 通过flask_session将session保存到redis中
    # 指定session保存在redis中
    SESSION_TYPE = "redis"
    # 让cookie中的session_id被加密签名处理
    SESSION_USE_SIGNER = True
    # 指定session保存的redis
    SESSION_REDIS = StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    # 设置session的过期时间,单位s
    PERMANENT_SESSION_LIFETIME = 86400 * 2

    # 默认日志等级
    LOG_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = logging.ERROR


class TestingConfig(Config):
    """单元测试环境下的配置"""
    DEBUG = True
    TESTING = True


config = {
    "development":DevelopmentConfig,
    "testing":TestingConfig,
    "production":ProductionConfig
}