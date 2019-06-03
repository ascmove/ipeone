#!/usr/bin/python
# -*- coding:utf-8 -*-
# 通用网关认证工具 for Python2.7（一网通办版本）
import ConfigParser
import os
import random
import sys
import time
import urllib
import urllib2

import requests
from pyquery import PyQuery as pq  # pip install pyquery
from requests.cookies import RequestsCookieJar

work_folder = os.path.dirname(__file__)
cf = ConfigParser.ConfigParser()
cf.read(work_folder+'/config-eone.ini')
access_forbidden_file = work_folder+"/"+str(cf.get("access", "access_forbidden_file"))

eone_account = str(cf.get("eone", "eone_account"))  # 网关账号
eone_passwd = str(cf.get("eone", "eone_passwd"))  # 网关密码
eone_tpass_url = str(cf.get("eone", "eone_tpass_url"))  # 认证地址
eone_logout_url = str(cf.get("eone", "eone_logout_url"))  # 注销地址
auth_action_url = str(cf.get("ipgw", "auth_action_url"))  # 在线信息
test_connection_url = str(cf.get("ipgw", "test_connection_url"))  # 测试联网链接
logout_sid_file = str(cf.get("logout", "sid_file"))  #
session_id_file = str(cf.get("eone", "session_id"))  #


def auth_eone_login(username, password):
    """
    一网通办认证
    :param username:
    :param password:
    :return: status code
    200 认证成功
    501 暂时禁止登陆
    400 登陆异常
    401 账号或密码错误
    402 访问被拒绝
    601 网络连接异常
    """
    with open(access_forbidden_file, 'a+') as fp:
        fc = fp.read()
    if len(fc) == 0:
        fc = 0
    if int(fc) > int(time.time()):
        return 501

    # 预加载网页,获取lt,execution值
    try:
        res = requests.get(eone_tpass_url)
    except:
        return 601
    Language = res.cookies['Language']
    JSESSIONID = res.cookies['JSESSIONID']
    with open(work_folder + "/" + session_id_file, 'w+') as fw:
        fw.write(str(JSESSIONID))

    doc = pq(res.content)
    lt = doc.find("#lt").val()
    execution = doc.find("input[name='execution']").val()

    req_data = {'rsa': username + password + lt, 'ul': len(username), 'pl': len(password), 'lt': lt,
                'execution': execution, '_eventId': 'submit'}

    cookie_jar = RequestsCookieJar()
    cookie_jar.set("Language", Language, domain="pass.neu.edu.cn")
    cookie_jar.set("JSESSIONID", JSESSIONID, domain="pass.neu.edu.cn")
    try:
        res = requests.post(eone_tpass_url, req_data, cookies=cookie_jar)
    except:
        return 601
    if "锁定" in res.content:
        # 连续登录失败5次，账号将被锁定1分钟，剩余次数3
        return 401
    if "访问被拒绝" in res.content:
        # 访问被拒绝
        return 402
    doc = pq(res.content)
    ss = doc.find("tr").items()
    for s in ss:
        if s.attr("style") == "background:lightgreen;":
            logoutId = s.find("a").attr("onclick").split("'")[1]
            with open(work_folder + "/" + logout_sid_file, 'w+') as fw:
                fw.write(str(int(logoutId)))

    # 检测登陆成功方法是返回页面中包含账号信息
    # 受页面改版影响，该方法可能不稳定
    if eone_account in res.content:
        return 200
    elif "5分钟" in res:
        with open(access_forbidden_file, 'w+') as fw:
            fw.write(str(int(time.time() + 300)))
        return 501
    else:
        return 400


def get_online_info():
    """
    旧版API接口，可能不稳定
    获取在线信息
    :return:在线信息
    """
    k = int(random.random() * 100000)
    test_data = {'action': 'get_online_info', 'k': k}
    test_data_urlencode = urllib.urlencode(test_data)
    requrl = auth_action_url
    req = urllib2.Request(url=requrl, data=test_data_urlencode)
    res_data = urllib2.urlopen(req)
    res = res_data.read()
    return res.split(',')


def auth_eone_logout():
    with open(work_folder + "/" + session_id_file, 'a+') as fp:
        JSESSIONID = fp.read()
    if len(JSESSIONID) == 0:
        return False
    with open(work_folder + "/" + logout_sid_file, 'a+') as fp:
        logout_sid = int(fp.read())
    if logout_sid == 0:
        return False
    cookie_jar = RequestsCookieJar()
    cookie_jar.set("session_for:srun_cas_php", JSESSIONID, domain="ipgw.neu.edu.cn")
    res = requests.post(eone_logout_url, {'action': 'dm', 'sid': logout_sid}, cookies=cookie_jar)
    if "失败" in res.content:
        return False
    if "下线请求已发送" in res.content:
        return True
    return False


if __name__ == '__main__':

    if len(sys.argv) == 1:
        online_info = get_online_info()
        if online_info[0] == 'not_online':
            # 本机未在线，进行登入程序
            res = auth_eone_login(eone_account, eone_passwd)
            if res == 501:
                print "网关繁忙，请等待5分钟再试"
            elif res == 200:
                print "认证成功"
            elif res == 400:
                print "登陆异常"
            elif res == 401:
                print "账号或密码错误"
            elif res == 402:
                print "访问被拒绝，稍后再试"
            elif res == 601:
                print "网络连接异常"
            else:
                print "认证失败"
        else:
            print "已在线"
    elif len(sys.argv) == 2 and sys.argv[1] == "logout":
        online_info = get_online_info()
        if online_info[0] == 'not_online':
            print "未上线"
        elif auth_eone_logout():
            print "已下线"
        else:
            print "下线失败"
    else:
        print "Use [ipgw.py logout] to disconnet from server."
