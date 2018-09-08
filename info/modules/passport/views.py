import json
import random
import re
from datetime import datetime

from flask import request, jsonify, abort, current_app, make_response, session

from info import redis_store, constants, db
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.response_code import RET
from . import passport_blu

from info.utils.captcha.captcha import captcha


@passport_blu.route("logout")
def logout():
    # 将session清空
    session.pop("mobile")
    session.pop("nick_name")
    session.pop("user_id")

    return jsonify(errno=RET.OK,errmsg="退出成功")


@passport_blu.route("/login",methods=["post"])
def login():
    """
    登录逻辑
    1. 获取参数 手机号 密码
    2. 校验参数
    3. 判断数据库中是否有此用户
    4. 查询真实密码
    5. 判断密码是否正确
    6. 设置session
    7. 返回响应
    :return:
    """
    params = request.json
    mobile = params.get("mobile")
    passport = params.get("passport")

    # 校验参数
    if not all([mobile,passport]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数错误")

    if not re.match(r"1[345678]\d{9}",mobile):
        return jsonify(errno=RET.PARAMERR,errmsg="手机号格式错误")

    # 判断数据库中是否有这个手机号
    try:
        user = User.query.filter(User.mobile==mobile).first()
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.DBERR,errmsg="数据查询失败")

    # if user:
    #     result = user.check_passowrd(passport)
    # 判断用户是否存在 如果不存在需要返回没有此用户
    if not user:
        return jsonify(errno=RET.NODATA,errmsg="没有此用户")

    # 判断密码是否一致
    if not user.check_passowrd(passport) :
        return jsonify(errno=RET.PWDERR,errmsg="密码错误")

    # 登陆成功设置session
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name
    session["user_id"] = user.id

    # 设置保存用户最后一次登陆时间
    user.last_login = datetime.now()

    # 可以在数据库中设置SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    return jsonify(errno=RET.OK,errmsg="登录成功")


@passport_blu.route("/register",methods=["post"])
def register():
    """
    注册流程
    1. 获取参数 手机号 手机验证码 密码
    2. 校验参数
    3. 找出手机验证码对比输入是否正确
    4. 初始化User模型.生成user
    5. 将user模型保存至数据库中
    6. 返回响应
    :return:
    """
    params_dict = request.json
    mobile = params_dict.get("mobile")
    sms_code = params_dict.get("smscode")
    password = params_dict.get("password")

    # 校验参数
    if not all([mobile,sms_code,password]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数错误")

    # 校验手机号是否符合规则
    if not re.match(r"1[345678]\d{9}",mobile):
        return jsonify(errno=RET.PARAMERR,errmsg="手机号格式错误")

    # 从redis中找出手机验证码
    try:
        real_sms_code = redis_store.get("SMS_" + mobile)
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.DBERR,errmsg="数据库查询失败")

    if not real_sms_code:
        return jsonify(errno=RET.NODATA,errmsg="手机验证码过期")

    # 对比手机验证码
    if sms_code != real_sms_code:
        return jsonify(errno=RET.DATAERR,errmsg="手机验证码错误")

    # 初始化User模型
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    user.password = password
    # 记录最后一次登录时间
    user.last_login = datetime.now()
    # 将用户存入数据库中
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as ret:
        current_app.logger.error(ret)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg="数据插入失败")

    # 设置session 保存用户的登录状态
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name
    session["user_id"] = user.id

    # 返回响应
    return jsonify(errno=RET.OK,errmsg="注册成功")


@passport_blu.route("/sms_code",methods=["post"])
def sms_code():
    """
    手机验证码逻辑
    1. 获取参数 手机号 图片验证码 随机值
    2. 校验参数
    3. 通过随机值获取redis中图片验证码内容
    4. 匹配图片验证码是否一致
    5. 生成短信验证码
    6. 发送短信验证码
    !.7. 设置session.保存用户的登录状态
    7. 返回响应
    :return:
    """
    # 1. 获取参数
    # params_dict = request.json  # json后面没有（）
    params_dict = json.loads(request.data)
    current_app.logger.debug(params_dict)
    current_app.logger.debug(request.data)
    mobile = params_dict.get("mobile")
    image_code = params_dict.get("image_code")
    image_code_id = params_dict.get("image_code_id")

    # 2. 校验参数
    # 是否有值
    if not all([mobile,image_code_id,image_code]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数错误")

    # 手机号是否符合规范
    if not re.match(r"1[345678]\d{9}",mobile):
        return jsonify(errno=RET.PARAMERR,errmsg="手机号格式错误")

    # 3. 通过随机值获取redis中保存的图片验证码
    try:
        real_image_code = redis_store.get("imageCodeId_" + image_code_id)
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.DBERR,errmsg="数据查询错误")
    # 判断是否有值
    if not real_image_code:
        return jsonify(errno=RET.NODATA,errmsg="图片验证码已过期")

    # 4. 对比验证码是否一致
    if image_code.upper() != real_image_code.upper():
        return jsonify(errno=RET.DATAERR,errmsg="图片验证码错误")

    # 5. 生成随机六位数字的手机验证码
    sms_code_str = "%06d" % random.randint(0,999999)
    current_app.logger.debug("生成的手机验证码是%s" % sms_code_str)

    # 6. 发送手机验证码
    # result = CCP().send_template_sms(mobile,[sms_code_str,5],1)
    # if result != 0:
    #     return jsonify(errno=RET.THIRDERR,errmsg="短信发送失败")
    # 将短信验证码保存到redis中
    try:
        redis_store.set("SMS_" + mobile,sms_code_str)
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.DBERR,errmsg="数据保存失败")

    # 7. 返回响应
    return jsonify(errno=RET.OK,errmsg="发送手机验证码成功")


@passport_blu.route("/image_code")
def image_code():
    """
    图片验证码的实现逻辑
    1. 获取参数 图片验证码的随机值
    ！ 切记！ 一定要判断
    2. 生成图片验证码
    3. 将图片文字和随机值保存到redis中
    4. 将图片验证码 返回
    :return:
    """
    image_code_id = request.args.get("imageCodeId", None)

    # 判断参数是否有值
    if not image_code_id:
        abort(403)

    # 生成图片验证码
    name, text, image = captcha.generate_captcha()

    # 将图片验证码文字保存到redis中
    try:
        redis_store.set("imageCodeId_" + image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as ret:
        current_app.logger.error(ret)
        abort(500)

    # 将图片验证码返回
    response = make_response(image)
    # 让浏览器可以识别图片类型
    response.headers["Content-Type"] = "image/jpg"
    return response
