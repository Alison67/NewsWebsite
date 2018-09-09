import logging

from flask import session, render_template, request, jsonify

from info.models import User, News, Category
from info.utils.response_code import RET
from . import index_blu

from flask import current_app

from info import redis_store, constants


@index_blu.route("/news_list")
def news_list():
    """
    获取数据
    :return:
    """
    cid = request.args.get("cid","1")
    page = request.args.get("page","1")
    per_page = request.args.get("per_page","10")

    # 2. 校验参数
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.PARAMERR,errmsg="参数错误")

    # 3. 查询数据库
    filters = []
    if cid != 1:
        filters.append(News.category_id==cid)

    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,per_page,False)
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.DBERR,errmsg="数据库查询失败")

    # 取出paginate的内容
    news = paginate.items
    total_page = paginate.pages
    current_page = paginate.page

    news_dict_li = []
    for new in news:
        news_dict_li.append(new.to_basic_dict())
    data = {
        "news_dict_li":news_dict_li,
        "total_page":total_page,
        "current_page":current_page
    }

    return jsonify(errno=RET.OK,errmsg="查询成功",data=data)





    # try:
    #     cid = int(cid)
    #     page = int(page)
    #     per_page = int(per_page)
    # except Exception as ret:
    #     current_app.logger.error(ret)
    #     return jsonify(errno=RET.PARAMERR,errmsg="参数错误")
    # if cid != 1:
    #     paginate = News.query.filter(News.category_id==cid).order_by(News.create_time.desc()).paginate(page,per_page,False)
    # else:
    #     paginate = News.query.order_by(News.create_time.desc()).paginate(page, per_page,False)
    # news = paginate.items
    # current_page = paginate.page
    # total_page = paginate.pages
    # news_dict_li = []
    # for new in news:
    #     news_dict_li.append(new.to_basic_dict())
    # data = {
    #     'current_page':current_page,
    #     'news_dict_li': news_dict_li,
    #     'total_page':total_page
    # }
    # return jsonify(errno=RET.OK, errmsg="haha",data=data)







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

    # 展示分类
    categories = []
    try:
        categories = Category.query.all()
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.DBERR,errmsg="数据库查询失败")
    category_li = []
    for category in categories:
        category_li.append(category.to_dict())

    data = {
        "user":user.to_dict() if user else None,  # 注意这里要加一个条件判断
        "news_dict_li":news_dict_li,
        "category_li":category_li
    }

    return render_template("news/index.html",data=data)
