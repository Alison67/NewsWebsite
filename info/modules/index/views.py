import logging

from flask import session, render_template, request, jsonify

from info.models import User, News
from info.utils.response_code import RET
from . import index_blu

from flask import current_app

from info import redis_store, constants


@index_blu.route("/")
def index():
    # 向redis保存一个值
    # redis_store.set("nihao","I'm redis_store ,I'm the session in redis")
    # session["Hello"] = "Session"
    # logging.debug("debug")
    # logging.warning("warning")
    # logging.error("error")
    # logging.fatal("fatal")
    # current_app.logger.debug("app.logger.debug")
    # current_app.logger.error("app.logger.error")
    # current_app.logger.warning("warning")
    # current_app.logger.fatal("fatal")
    # 获取用户session
    """
    首页展示逻辑
    1. 从session中获取用户id
    2. 判断用户id是否为空
    3. 使用用户id从数据库中获取用户模型
    4. 将用户数据转换成字典传输至模板中
    :return:
    """
    user_id = session.get("user_id",None)
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as ret:
            current_app.logger.error(ret)
            return jsonify(errno=RET.DBERR,errmsg="数据库查询失败")

    # 展示排行
    news = []
    try:
        news = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS).all()
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.DBERR,errmsg="数据库查询失败")

    news_dict_li = []
    for new in news:
        news_dict_li.append(new.to_basic_dict())

    data = {
        "user":user.to_dict() if user else None,  # 注意这里要加一个条件判断
        "news_dict_li":news_dict_li
    }

    return render_template("news/index.html",data=data)
