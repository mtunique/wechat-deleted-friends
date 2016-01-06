# coding=utf-8

import os
import urllib, urllib2
import re
import cookielib
import time
import xml.dom.minidom
import json
import sys
import math
import hashlib


class Wechat(object):

    def __init__(self):

        self.MAX_GROUP_NUM = 35 # 每组人数


        self.tip = 0
        self.uuid = ''

        self.base_uri = ''
        self.redirect_uri = ''

        self.skey = ''
        self.wxsid = ''
        self.wxuin = ''
        self.pass_ticket = ''
        self.deviceId = 'e000000000000000'

        self.BaseRequest = {}

        self.ContactList = []
        self.My = []


        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
        urllib2.install_opener(opener)

        if not self.getUUID():
            print '获取uuid失败'
            return

        self.QRImagePath = os.getcwd() + '/{}.jpg'.format(hashlib.md5(self.uuid).hexdigest())

    def second(self):


        while self.waitForLogin() != '200':
            pass


        if not self.login():
            print '登录失败'
            return

        if not self.webwxinit():
            print '初始化失败'
            return

        self.MemberList = self.webwxgetcontact()

        self.MemberCount = len(self.MemberList)
        print '通讯录共%s位好友' % self.MemberCount

        ChatRoomName = ''
        result = []
        print '开始查找...'
        group_num=int(math.ceil(self.MemberCount / float(self.MAX_GROUP_NUM)))
        for i in xrange(0, group_num):
            UserNames = []
            NickNames = []
            for j in xrange(0, self.MAX_GROUP_NUM):
                if i * self.MAX_GROUP_NUM + j >= self.MemberCount:
                    break
                Member = self.MemberList[i * self.MAX_GROUP_NUM + j]
                UserNames.append(Member['UserName'])
                NickNames.append(Member['NickName'].encode('utf-8'))

            # 	进度条
            progress='-'*10
            progress_str='%s'%''.join(map(lambda x:'#',progress[:(10*(i+1))/group_num]))
            print '[',progress_str,''.join('-'*(10-len(progress_str))),']',
            print '(当前,你被%d人删除,好友共%d人'%(len(result),len(self.MemberList)),'\r',
            time.time()

            # print '第%s组...' % (i + 1)

            # print ', '.join(NickNames)
            # print '回车键继续...'
            # raw_input()

            # 新建群组/添加成员
            if ChatRoomName == '':
                (ChatRoomName, DeletedList) = self.createChatroom(UserNames)
            else:
                DeletedList = self.addMember(ChatRoomName, UserNames)

            DeletedCount = len(DeletedList)
            if DeletedCount > 0:
                result += DeletedList

            # print '找到%s个被删好友' % DeletedCount
            # raw_input()

            # 删除成员
            self.deleteMember(ChatRoomName, UserNames)

        resultNames = []
        for Member in self.MemberList:
            if Member['UserName'] in result:
                NickName = Member['NickName']
                if Member['RemarkName'] != '':
                    NickName += '(%s)' % Member['RemarkName']
                resultNames.append(NickName.encode('utf-8'))

        print '\n---------- 被删除的好友列表 ----------'
        # 过滤emoji
        resultNames=map(lambda x:re.sub(r'<span.+/span>','',x),resultNames)
        print '-----------------------------------'

        return '\n'.join(resultNames)


    def getUUID(self):

            url = 'https://login.weixin.qq.com/jslogin'
            params = {
                    'appid': 'wx782c26e4c19acffb',
                    'fun': 'new',
                    'lang': 'zh_CN',
                    '_': int(time.time()),
            }

            request = urllib2.Request(url = url, data = urllib.urlencode(params))
            response = urllib2.urlopen(request)
            data = response.read()

            # print data

            # window.QRLogin.code = 200; window.QRLogin.uuid = "oZwt_bFfRg==";
            regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
            pm = re.search(regx, data)

            code = pm.group(1)
            self.uuid = pm.group(2)

            if code == '200':
                    return True

            return False

    def showQRImage(self):

            url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
            params = {
                    't': 'webwx',
                    '_': int(time.time()),
            }

            return url+'?'+urllib.urlencode(params)

    def waitForLogin(self):

            url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (self.tip, self.uuid, int(time.time()))

            request = urllib2.Request(url = url)
            response = urllib2.urlopen(request)
            data = response.read()

            # print data

            # window.code=500;
            regx = r'window.code=(\d+);'
            pm = re.search(regx, data)

            code = pm.group(1)

            if code == '201': #已扫描
                    print '成功扫描,请在手机上点击确认以登录'
                    self.tip = 0
            elif code == '200': #已登录
                    print '正在登录...'
                    regx = r'window.redirect_uri="(\S+?)";'
                    pm = re.search(regx, data)
                    self.redirect_uri = pm.group(1) + '&fun=new'
                    self.base_uri = self.redirect_uri[:self.redirect_uri.rfind('/')]
            elif code == '408': #超时
                    pass
            # elif code == '400' or code == '500':

            return code

    def login(self):
            request = urllib2.Request(url = self.redirect_uri)
            response = urllib2.urlopen(request)
            data = response.read()

            # print data

            '''
                    <error>
                            <ret>0</ret>
                            <message>OK</message>
                            <skey>xxx</skey>
                            <wxsid>xxx</wxsid>
                            <wxuin>xxx</wxuin>
                            <pass_ticket>xxx</pass_ticket>
                            <isgrayscale>1</isgrayscale>
                    </error>
            '''

            doc = xml.dom.minidom.parseString(data)
            root = doc.documentElement

            for node in root.childNodes:
                    if node.nodeName == 'skey':
                            self.skey = node.childNodes[0].data
                    elif node.nodeName == 'wxsid':
                            self.wxsid = node.childNodes[0].data
                    elif node.nodeName == 'wxuin':
                            self.wxuin = node.childNodes[0].data
                    elif node.nodeName == 'pass_ticket':
                            self.pass_ticket = node.childNodes[0].data


            if self.skey == '' or self.wxsid == '' or self.wxuin == '' or self.pass_ticket == '':
                    return False
            self.BaseRequest = {
                    'Uin': int(self.wxuin),
                    'Sid': self.wxsid,
                    'Skey': self.skey,
                    'DeviceID': self.deviceId,
            }

            return True

    def webwxinit(self):

            url = self.base_uri + '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (self.pass_ticket, self.skey, int(time.time()))
            params = {
                    'BaseRequest': self.BaseRequest
            }

            request = urllib2.Request(url = url, data = json.dumps(params))
            request.add_header('ContentType', 'application/json; charset=UTF-8')
            response = urllib2.urlopen(request)
            data = response.read()

            # print data

            global ContactList, My
            dic = json.loads(data)
            ContactList = dic['ContactList']
            My = dic['User']

            ErrMsg = dic['BaseResponse']['ErrMsg']
            # if len(ErrMsg) > 0:
            # 	print ErrMsg

            Ret = dic['BaseResponse']['Ret']
            if Ret != 0:
                    return False

            return True

    def webwxgetcontact(self):

            url = self.base_uri + '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (self.pass_ticket, self.skey, int(time.time()))

            request = urllib2.Request(url = url)
            request.add_header('ContentType', 'application/json; charset=UTF-8')
            response = urllib2.urlopen(request)
            data = response.read()


            dic = json.loads(data)
            MemberList = dic['MemberList']

            # 倒序遍历,不然删除的时候出问题..
            SpecialUsers = ['newsapp', 'fmessage', 'filehelper', 'weibo', 'qqmail', 'fmessage', 'tmessage', 'qmessage', 'qqsync', 'floatbottle', 'lbsapp', 'shakeapp', 'medianote', 'qqfriend', 'readerapp', 'blogapp', 'facebookapp', 'masssendapp', 'meishiapp', 'feedsapp', 'voip', 'blogappweixin', 'weixin', 'brandsessionholder', 'weixinreminder', 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c', 'officialaccounts', 'notification_messages', 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c', 'wxitil', 'userexperience_alarm', 'notification_messages']
            for i in xrange(len(MemberList) - 1, -1, -1):
                    Member = MemberList[i]
                    if Member['VerifyFlag'] & 8 != 0: # 公众号/服务号
                            MemberList.remove(Member)
                    elif Member['UserName'] in SpecialUsers: # 特殊账号
                            MemberList.remove(Member)
                    elif Member['UserName'].find('@@') != -1: # 群聊
                            MemberList.remove(Member)
                    elif Member['UserName'] == My['UserName']: # 自己
                            MemberList.remove(Member)

            return MemberList




    def createChatroom(self, UserNames):
        MemberList = []
        for UserName in UserNames:
            MemberList.append({'UserName': UserName})


        url = self.base_uri + '/webwxcreatechatroom?pass_ticket=%s&r=%s' % (self.pass_ticket, int(time.time()))
        params = {
            'BaseRequest': self.BaseRequest,
            'MemberCount': len(MemberList),
            'MemberList': MemberList,
            'Topic': '',
        }

        request = urllib2.Request(url = url, data = json.dumps(params))
        request.add_header('ContentType', 'application/json; charset=UTF-8')
        response = urllib2.urlopen(request)
        data = response.read()

        # print data

        dic = json.loads(data)
        ChatRoomName = dic['ChatRoomName']
        MemberList = dic['MemberList']
        DeletedList = []
        for Member in MemberList:
            if Member['MemberStatus'] == 4: #被对方删除了
                DeletedList.append(Member['UserName'])

        ErrMsg = dic['BaseResponse']['ErrMsg']
        # if len(ErrMsg) > 0:
        # 	print ErrMsg

        return ChatRoomName, DeletedList

    def deleteMember(self, ChatRoomName, UserNames):
        url = self.base_uri + '/webwxupdatechatroom?fun=delmember&pass_ticket=%s' % (self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest,
            'ChatRoomName': ChatRoomName,
            'DelMemberList': ','.join(UserNames),
        }

        request = urllib2.Request(url = url, data = json.dumps(params))
        request.add_header('ContentType', 'application/json; charset=UTF-8')
        response = urllib2.urlopen(request)
        data = response.read()

        # print data

        dic = json.loads(data)
        ErrMsg = dic['BaseResponse']['ErrMsg']
        # if len(ErrMsg) > 0:
        # 	print ErrMsg

        Ret = dic['BaseResponse']['Ret']
        if Ret != 0:
            return False

        return True

    def addMember(self, ChatRoomName, UserNames):
        url = self.base_uri + '/webwxupdatechatroom?fun=addmember&pass_ticket=%s' % (self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest,
            'ChatRoomName': ChatRoomName,
            'AddMemberList': ','.join(UserNames),
        }

        request = urllib2.Request(url = url, data = json.dumps(params))
        request.add_header('ContentType', 'application/json; charset=UTF-8')
        response = urllib2.urlopen(request)
        data = response.read()

        # print data

        dic = json.loads(data)
        MemberList = dic['MemberList']
        DeletedList = []
        for Member in MemberList:
            if Member['MemberStatus'] == 4: #被对方删除了
                DeletedList.append(Member['UserName'])

        ErrMsg = dic['BaseResponse']['ErrMsg']
        # if len(ErrMsg) > 0:
        # 	print ErrMsg

        return DeletedList


# windows下编码问题修复
# http://blog.csdn.net/heyuxuanzee/article/details/8442718
class UnicodeStreamFilter:
        def __init__(self, target):
                self.target = target
                self.encoding = 'utf-8'
                self.errors = 'replace'
                self.encode_to = self.target.encoding
        def write(self, s):
                if type(s) == str:
                        s = s.decode('utf-8')
                s = s.encode(self.encode_to, self.errors).decode(self.encode_to)
                self.target.write(s)


if __name__ == '__main__' :

    if sys.stdout.encoding == 'cp936':
        sys.stdout = UnicodeStreamFilter(sys.stdout)
    print '本程序的查询结果可能会引起一些心理上的不适,请小心使用...'
    print '回车键继续...'
    raw_input()

    # Wechat().main()

    print '回车键结束'
    raw_input()
