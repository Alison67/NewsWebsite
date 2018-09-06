import logging

from flask import session

from . import index_blu

from flask import current_app

from info import redis_store


@index_blu.route("/")
def index():
    # 向redis保存一个值
    redis_store.set("nihao","I'm redis_store ,I'm the session in redis")
    session["Hello"] = "Session"
    logging.debug("debug")
    logging.warning("warning")
    logging.error("error")
    logging.fatal("fatal")
    current_app.logger.debug("app.logger.debug")
    current_app.logger.error("app.logger.error")
    current_app.logger.warning("warning")
    current_app.logger.fatal("fatal")
    return "index"
