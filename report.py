#!/usr/bin/env python3.8
# -*- encoding: utf-8 -*-

import requests
from requests import exceptions
import json
import time


class NcovReport:
    def __init__(self, token, keys=None):
        self.headers = {
            "Content-Type": "application/json;charset=utf-8",
            "ncov-access-token": token
        }
        self.keys = keys
        self.data = self.getLast()
        try:
            self.codeId = self.data["address"].pop("_id", None)
        except TypeError as e:
            print("打卡失败，请登录再重试！," +
                  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            if keys is not None:
                self.sendMsg("今日打卡失败，请登录小程序打卡")
        else:
            reportStatus =  self.dailyReport() 
            if keys is not None:
                self.sendMsg(reportStatus)

    def getLast(self):
        """
        通过上一次打卡提交的数据来获取这次该提交的数据
        """
        # 上一次的报告情况
        lastReport = 'https://www.ioteams.com/ncov/api/users/last-report'
        try:
            response = requests.get(lastReport, headers=self.headers)
        except exceptions.HTTPError as e:
            return e
        else:
            try:
                req = response.json()["data"]["data"]
            except ValueError as e:
                return e
            else:
                unneceInfo = ["_id", "user", "company",
                               "created_at", "updated_at", "__v"]
                for i in unneceInfo:
                    req.pop(i, None)
                return req

    def dailyReport(self):
        """
        每天的第一次日报，每日仅一次
        之后再请求就会403
        """
        link = 'https://www.ioteams.com/ncov/api/users/dailyReport'
        response = requests.post(
            link, headers=self.headers, data=json.dumps(self.data))
        req = response.json()
        if req['code'] == 403:
            print(req['msg'].split('，')[0], end=",")
            print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            return req['msg']
        else:
            try:
                self.codeId = req['data']['data']['_id']
            except KeyError:
                print(req['msg'], end=",")
                return req['msg']
            except Exception as E:
                print(E, "打卡失败，请登录小程序检查", end=",")
                return "打卡失败，请登录小程序检查打卡"
            else:
                print(req['msg'], end=",")
                return req['msg']
            finally:
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    def sendMsg(self, status):
        """
        通过Server酱推送至WeChat
        """
        if status == 'success':
            status = "今日打卡成功"
        payload = {
            'text': status,
            'desp': """
#### 0x00 打卡成功
两种状态均表明打卡成功。第一种「您今天已经创建过日报，无法再次创建」表明这是一种重复打卡，没事的。第二种「今日打卡成功」属于预期的结果。

#### 0x01 打卡失败
「今日打卡失败，请登录打卡」表明打卡失败，原因可能是超过三天未登录「易统计」小程序，token未刷新。请登录小程序，顺便手动打一下卡。

#### 0x02 注意事项
大约三天不登录，账号就会过期，请求*https://www.ioteams.com/ncov/api/users/last-report*这个接口就会报403。
所以目前要求大约每2/3天需要登录一次打卡平台！（打开「易统计」微信小程序即可）
另外这个程序是以请求上次打卡（昨天）提交的信息，来作为这一次（今天）所需要提交的信息。
也就是说当离开一个地方去另一个地方，需要暂停使用这个程序一天。那一天自己手动打卡以后再使用这个程序。
另外身体异常者不要使用！

#### 项目地址：https://github.com/FanqXu/ncovAutoReport （欢迎Star🤗）
            """}
        reqUrl = 'https://sc.ftqq.com/' + self.keys + ".send"
        push = requests.post(reqUrl, data=payload)


if __name__ == '__main__':
    usersInfo = open('./conf.ini',
                      encoding='UTF-8').read().split()
    for info in usersInfo:
        spread = info.split('#')
        print(spread[1], end=',')
        if spread[2] == '':
            NcovReport(spread[0])
        else:
            NcovReport(spread[0], spread[2])
