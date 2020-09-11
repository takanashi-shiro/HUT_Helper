# @name             HUT_Helper
# @namespace        https://github.com/takanashi-shiro/HUT_Helper
# @version          2.0.0
# @description      基于python的胡工大小助手
# @author:          Takanashi-Shiro


# -*-coding:utf-8-*-
import requests
import bs4
import re
import os
from lxml import etree
import datetime
import os
import time
import json


def login():  # 登入获取cookies
    global user
    user = input("输入用户名(学号):")
    user_password = input("输入密码:")
    url = 'http://218.75.197.123:83/app.do?method=authUser&xh='+user+'&pwd='+user_password
    response = requests.get(url)

    soup = bs4.BeautifulSoup(response.text, "html.parser")
    s_soup = str(soup)
    success = s_soup[11]

    if success == 'f':
        os.system('cls')
        print("用户名或密码错误，请重试")
        return login()
    else:
        os.system('cls')
        begin = s_soup.find("token")+8
        final = s_soup.find("user")-3
        cookie = s_soup[begin:final]
        return cookie


def get_now_week(cookie, time):  # 获取当前日期为第几周
    url = 'http://218.75.197.123:83/app.do'
    header = {
        'token': cookie
    }
    data = {
        'method': 'getCurrentTime',
        'currDate': time
    }
    response = requests.get(url=url, params=data, headers=header)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    soup_str = str(soup)
    zc = soup_str[soup_str.find('zc')+4:soup_str.find('e_time')-2]
    global s_time
    if zc == 'null':
        print("当前还未到上课时间，请自行输入有课的第一天的日期(2020-01-01)\n")
        rq = input()
        return get_now_week(cookie, rq)
    else:
        zc = eval(zc)
        s_time = soup_str[11:15]+soup_str[16:18] + \
            soup_str[19:21]  # 当前日期所在周的第一天 用于推出从当前周起 以后的所有课程
        return zc


def find_class(cookie, zc, now_week_date, now_xh):  # 获取zc周课程 now_week_date为当前周的第一天日期
    url = 'http://218.75.197.123:83/app.do'
    header = {
        'token': cookie
    }
    data = {
        'method': 'getKbcxAzc',
        'xnxqid': '',
        'xh': now_xh,
        'zc': str(zc)
    }
    response = requests.get(url=url, params=data, headers=header)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    soup_str = str(soup)
    if soup_str == "[]":
        return soup_str
    global course, course_name, course_time_start, course_time_finnal, course_classroom, course_teacher, course_day
    s = 0
    f = 2147483647

    course = []
    course_name = []
    course_time_start = []
    course_time_finnal = []
    course_classroom = []
    course_teacher = []
    course_day = []

    for i in range(0, len(soup_str)):  # 先获取课程的全部信息
        if soup_str[i] == '{':
            s = i
        if soup_str[i] == '}':
            f = i
            course.append(soup_str[s+1:f])
            s = f+1
            f = 2147483647

    for i in course:  # 再对每个课程的信息进行分类

        fs = str(i).find('jssj')+7
        ff = fs+5
        course_time_finnal.append(str(i)[fs:fs+2]+str(i)[fs+3:ff])

        names = str(i).find('kcmc')+7
        namef = str(i).find('kcsj')-3
        course_name.append(str(i)[names:namef])

        ss = str(i).find('kssj')+7
        sf = ss+5
        course_time_start.append(str(i)[ss:ss+2]+str(i)[ss+3:sf])

        cs = str(i).find('jsmc')+7
        cf = str(i).find('jsxm')-3
        if str(i)[cs:cf] == 'ul':
            course_classroom.append('无/待定')
        else:
            course_classroom.append(str(i)[cs:cf])

        ts = str(i).find('jsxm')+7
        tf = len(str(i))-1
        course_teacher.append(str(i)[ts:tf])

        day = str(i)[str(i).find('kcsj')+7]
        course_day.append(day)

    return tras(now_week_date, 1)


def tras(now_week_date, day):  # 将获取的课程信息转换为ics格式输出
    res = ''
    now_day = int(day)
    now_time = now_week_date
    for i in range(0, len(course)):
        if(int(course_day[i]) != now_day):  # 判断是否是同一天的课程 如果不是就加一天
            n = int(course_day[i]) - now_day
            now_time = str((datetime.datetime(int(now_time[0:4]), int(now_time[4:6]), int(
                now_time[6:8])) + datetime.timedelta(days=n)).strftime('%Y%m%d'))
            now_day += n
        st = now_time + 'T' + course_time_start[i] + '00'
        ft = now_time + 'T' + course_time_finnal[i] + '00'
        res += "BEGIN:VCALENDAR\nPRODID:-//Google Inc//Google Calendar 70.9054//EN\nVERSION:2.0\nCALSCALE:GREGORIAN\nMETHOD:PUBLISH\nX-WR-CALNAME:课程表\nX-WR-TIMEZONE:America/New_York\nBEGIN:VEVENT\n"
        res += "DTSTART:"+st+'\n'
        res += "DTEND:"+ft+'\n'
        res += "DTSTAMP:"+st+'\n'
        res += "UID:课程表\n"
        res += "CREATED:"+st+'\n'
        res += "DESCRIPTION:"+course_teacher[i]+'\n'
        res += "LAST-MODIFIED:"+st+'\n'
        res += "LOCATION:"+course_classroom[i]+'\n'
        res += "SEQUENCE:0"+'\n'
        res += "STATUS:CONFIRMED"+'\n'
        res += "SUMMARY:"+course_name[i]+'\n'
        res += "TRANSP:OPAQUE\nEND:VEVENT\nEND:VCALENDAR\n"
    return res


def jdt(start, i, len_jdt):  # 进度条
    a = '*' * i
    b = '.' * (len_jdt - i)
    c = (i/len_jdt)*100
    dur = time.perf_counter() - start
    print("\r{:^3.0f}%[{}->{}]{:.2f}s".format(c, a, b, dur), end='')
    time.sleep(0.1)


def std_info(cookie, xh):  # 获取学生信息
    os.system('cls')
    if xh == "exit":
        return
    url = 'http://218.75.197.123:83/app.do'
    header = {
        'token': cookie
    }
    data = {
        'method': 'getUserInfo',
        'xh': xh
    }
    global now_xh
    now_xh = xh
    response = requests.get(url=url, params=data, headers=header)
    soup = str(bs4.BeautifulSoup(response.text, "html.parser"))
    if soup == "{}":
        new_xh = input("请输入正确的学号！\n输入exit退出。\n")
        std_info(cookie, new_xh)
        return
    soup = soup.replace("null", '"未填写"')
    soup = soup.replace("ksh", '高考考号')
    soup = soup.replace("fxzy", '辅修专业')
    soup = soup.replace("xz", '学制')
    soup = soup.replace("dh", '电话')
    soup = soup.replace("bj", '班级')
    soup = soup.replace("xb", '性别')
    soup = soup.replace("rxnf", '入学年份')
    soup = soup.replace("zymc", '专业名称')
    soup = soup.replace("yxmc", '院系名称')
    soup = soup.replace("xh", '学号')
    soup = soup.replace("xm", '姓名')
    soup = soup.replace("nj", '年级')
    soup = soup.replace("email", 'Email')
    soup_dict = dict(eval(soup))
    for k, v in soup_dict.items():
        if(k != "dqszj" and k != "usertype"):
            print(k, v)


def std_check(cookie, xh):
    if xh == "exit":
        return False, 'exit'
    url = 'http://218.75.197.123:83/app.do'
    header = {
        'token': cookie
    }
    data = {
        'method': 'getUserInfo',
        'xh': xh
    }
    response = requests.get(url=url, params=data, headers=header)
    soup = str(bs4.BeautifulSoup(response.text, "html.parser"))
    if soup == "{}":
        os.system('cls')
        new_xh = input("请输入正确的学号！\n输入exit退出。\n")
        os.system('cls')
        return std_check(cookie, new_xh)
    return True, xh


def get_now_year(cookie):  # 获取当前学期学年
    url = 'http://218.75.197.123:83/app.do'
    header = {
        'token': cookie
    }
    data = {
        'method': 'getXnxq',
        'xh': user
    }
    response = requests.get(url=url, params=data, headers=header)
    soup = str(bs4.BeautifulSoup(response.text, "html.parser"))
    js = json.loads(soup)
    for i in js:
        if i['isdqxq'] == '1':
            return i['xnxq01id']


def change_year(now_xn, pd):  # 学期换算
    y1 = eval(now_xn[0:4])
    y2 = eval(now_xn[5:9])
    if pd == 1:
        if now_xn[-1] == '1':
            return str(y1-1)+'-'+str(y2-1)+'-2'
        else:
            return str(y1)+'-'+str(y2)+'-1'
    else:
        if now_xn[-1] == '2':
            return str(y1+1)+'-'+str(y2+1)+'-1'
        else:
            return str(y1)+'-'+str(y2)+'-2'


def get_grades(cookie, now_xn, xh):  # 获取课程成绩
    url = 'http://218.75.197.123:83/app.do'
    header = {
        'token': cookie
    }
    judge, xh = std_check(cookie, xh)
    if judge and xh != 'exit':
        data = {
            "method": "getCjcx",
            "xh": xh,
            "xnxqid": now_xn
        }
        print("当前学期学年为："+now_xn)
        session = requests.Session()
        req = session.get(url=url, params=data, headers=header).text
        if req == '{"success":true,"result":[]}':
            tmp = input("当前暂无成绩！\n1.查询上一学期成绩\n2.查询下一学期成绩\n3.退出\n")
            if tmp == '1':
                os.system('cls')
                get_grades(cookie, change_year(now_xn, 1), xh)
            if tmp == '2':
                os.system('cls')
                get_grades(cookie, change_year(now_xn, 2), xh)
            return

        req = req.replace("zcj", "总成绩")
        req = req.replace("kcxzmc", "课程性质名称")
        req = req.replace("xqmc", "学期名称")
        req = req.replace("kclbmc", "课程类别名称")
        req = req.replace("kcmc", "课程名称")
        req = req.replace("cjbsmc", "成绩标识名称")
        req = req.replace("kcywmc", "课程英文名称")
        req = req.replace("ksxzmc", "考试性质名称")
        req = req.replace("xf", "学分")
        req = req.replace("bz", "网络平台")
        req = req.replace("xm", "姓名")
        js = json.loads(req)
        ans = ''
        for course in js['result']:
            for k, v in course.items():
                if k == "姓名":
                    name = str(v)
                if v != None:
                    ans += str(k)+' '+str(v)+'\n'
            ans += '\n'
        a = open(name+"_grades_"+now_xn+".txt", mode='w', encoding="utf-8")
        a.write(ans)
        a.close
        os.system('cls')
        print("导出完成，名称为“"+name+"_grades_"+now_xn+".txt"+"”。\n")
        tmp = input("1.查询上一学期成绩\n2.查询下一学期成绩\n3.退出\n")
        if tmp == '1':
            os.system('cls')
            get_grades(cookie, change_year(now_xn, 1), xh)
        if tmp == '2':
            os.system('cls')
            get_grades(cookie, change_year(now_xn, 2), xh)
        return


def get_ics(cookie, xh):  # 获取课程表ics文件
    if xh == "exit":
        return
    global s_time
    ics_flag = 0
    test = find_class(cookie, now_week, s_time, xh)
    if test == '[]':
        os.system('cls')
        now_xh = input("请输入正确的学号！\n输入exit退出。\n")
        os.system('cls')
        get_ics(cookie, now_xh)
        return
    os.system('cls')
    s_jdt = time.perf_counter()
    print("执行开始".center(50//2, '-'))
    cnt = 0
    now_jdt = 20-int(now_week)
    res = ''
    for i in range(int(now_week), 21):  # 由于一学期正常最多不超过20周 循环到20周
        # 👇将每次获得的now_week转换成datetime类型 +7天 直接到下一周
        res += find_class(cookie, i, s_time, xh)
        s_time = str((datetime.datetime(int(s_time[0:4]), int(s_time[4:6]), int(
            s_time[6:8])) + datetime.timedelta(days=7)).strftime('%Y%m%d'))
        jdt(s_jdt, int(cnt), 50)
        cnt += 50/now_jdt
    print("\n"+"执行结束".center(50//2, '-'))
    a = open("your_calendar.ics", mode='w', encoding="utf-8")
    a.write(res)
    a.close


if __name__ == "__main__":
    cookie = login()
    global now_time, now_week
    now_time = datetime.datetime.now().strftime('%Y-%m-%d')
    now_week = get_now_week(cookie, now_time)
    numb = input(
        "输入想要使用的功能\n1.个人信息\n2.查询已知学号的学生信息\n3.获取课表(ics文件)\n4.获取成绩消息\n5.退出\n")
    while(numb != '5'):
        if(numb == '1'):
            os.system('cls')
            std_info(cookie, user)
            os.system('pause')
            os.system('cls')
        if(numb == '2'):
            os.system('cls')
            std_info(cookie, xh=input("输入查询学号\n"))
            os.system('pause')
            os.system('cls')
        if(numb == '3'):
            os.system('cls')
            xh = input("输入要获取课表的学生学号\n")
            get_ics(cookie, xh)
            os.system('pause')
            os.system('cls')
        if(numb == '4'):
            os.system('cls')
            xh = input("输入学号导出成绩单.txt\n")
            get_grades(cookie, get_now_year(cookie), xh)
            os.system('pause')
            os.system('cls')
        numb = input(
            "输入想要使用的功能\n1.个人信息\n2.查询已知学号的学生信息\n3.获取课表(ics文件)\n4.获取成绩消息\n5.退出\n")
