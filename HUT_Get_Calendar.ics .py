# @name             HUT_Get_Calendar.ics
# @namespace        https://github.com/takanashi-shiro/HUT_Get_Calendar_ics
# @version          1.0.0
# @description      用python提取课表并生成可导入至日历中isc文件
# @author:          Takanashi-Shiro


#-*-coding:utf-8-*-
import requests, bs4, re, os
from lxml import etree
import datetime
import os


def find_class(cookie,zc,now_week_date):    #获取zc周课程 now_week_date为当前周的第一天日期
    url = 'http://218.75.197.123:83/app.do'
    header = {
        'token':cookie
    }
    data = {
        'method':'getKbcxAzc',
        'xh':user,
        'xnxqid':'',
        'zc':str(zc)
    }
    response = requests.get(url=url,params=data,headers=header)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    soup_str = str(soup)

    global course,course_name,course_time_start,course_time_finnal,course_classroom,course_teacher,course_day
    s = 0
    f = 2147483647

    course = []
    course_name = []
    course_time_start = []
    course_time_finnal = []
    course_classroom = []
    course_teacher = []
    course_day = []

    for i in range(0,len(soup_str)):        #先获取课程的全部信息
        if soup_str[i] == '{':
            s = i
        if soup_str[i] == '}':
            f = i
            course.append(soup_str[s+1:f])
            s = f+1
            f = 2147483647

    for i in course:        #再对每个课程的信息进行分类

        fs = str(i).find('jssj')+7
        ff = fs+5
        course_time_finnal.append(str(i)[fs:fs+2]+str(i)[fs+3:ff])

        names = str(i).find('kcmc')+7
        namef = str(i).find('kcsj')-3
        course_name.append(str(i)[names:namef])

        ss = str(i).find('kssj')+7
        sf = fs+5
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
    tras(now_week_date,1)


def login():            #登入获取cookies
    global user
    user = input("输入用户名(学号):")
    user_password = input("输入密码:")
    url = 'http://218.75.197.123:83/app.do?method=authUser&xh='+user+'&pwd='+user_password
    response = requests.get(url)

    soup = bs4.BeautifulSoup(response.text, "html.parser")
    s_soup = str(soup)
    begin = s_soup.find("token")+8
    final = s_soup.find("user")-3
    cookie = s_soup[begin:final]
    return cookie

def get_now_week(cookie):       #获取当前日期为第几周
    url = 'http://218.75.197.123:83/app.do'
    header = {
        'token':cookie
    }
    data = {
        'method':'getCurrentTime',
        'currDate':datetime.datetime.now().strftime('%Y-%m-%d')
    }
    response = requests.get(url=url,params=data,headers=header)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    soup_str = str(soup)
    zc = eval(soup_str[soup_str.find('zc')+4:soup_str.find('e_time')-2])
    global s_time
    s_time = soup_str[11:15]+soup_str[16:18]+soup_str[19:21]            #当前日期所在周的第一天 用于推出从当前周起 以后的所有课程
    return zc


def tras(now_week_date,day):        #将获取的课程信息转换为ics格式输出
    now_day = int(day)
    now_time = now_week_date
    for i in range(0,len(course)):
        if(int(course_day[i])!=now_day):        #判断是否是同一天的课程 如果不是就加一天
            n = int(course_day[i]) - now_day
            now_time = str((datetime.datetime(int(now_time[0:4]),int(now_time[4:6]),int(now_time[6:8])) + datetime.timedelta(days=n)).strftime('%Y%m%d'))
            now_day+=n
        st = now_time + 'T' +course_time_start[i] + '00'
        ft = now_time + 'T' +course_time_finnal[i] +'00'
        a.write("BEGIN:VCALENDAR\nPRODID:-//Google Inc//Google Calendar 70.9054//EN\nVERSION:2.0\nCALSCALE:GREGORIAN\nMETHOD:PUBLISH\nX-WR-CALNAME:课程表\nX-WR-TIMEZONE:America/New_York\nBEGIN:VEVENT\n")
        a.write("DTSTART:"+st+'\n')
        a.write("DTEND:"+ft+'\n')
        a.write("DTSTAMP:"+st+'\n')
        a.write("UID:课程表\n")
        a.write("CREATED:"+st+'\n')
        a.write("DESCRIPTION:"+course_teacher[i]+'\n')
        a.write("LAST-MODIFIED:"+st+'\n')
        a.write("LOCATION:"+course_classroom[i]+'\n')
        a.write("SEQUENCE:0"+'\n')
        a.write("STATUS:CONFIRMED"+'\n')
        a.write("SUMMARY:"+course_name[i]+'\n')
        a.write("TRANSP:OPAQUE\nEND:VEVENT\nEND:VCALENDAR\n")
    

if __name__ == "__main__":
     cookie = login()
     now_week = int(get_now_week(cookie))
     cnt = 0
     a = open("your_calendar.ics",mode='w',encoding="utf-8")
     a.write('')
     a.close
     a = open("your_calendar.ics",mode='a',encoding="utf-8")
     for i in range(now_week,21):           #由于一学期正常最多不超过20周 循环到20周
        find_class(cookie,i,s_time)         #👇将每次获得的now_week转换成datetime类型 +7天 直接到下一周
        s_time = str((datetime.datetime(int(s_time[0:4]),int(s_time[4:6]),int(s_time[6:8])) + datetime.timedelta(days=7)).strftime('%Y%m%d'))
     a.close