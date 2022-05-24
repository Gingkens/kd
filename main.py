from email import header
from time import sleep
from appscript import k
from pyrsistent import get_in
import urllib3
import json
import numpy as np
import re
from urllib.parse import quote, urlparse
from urllib import parse

def get_info(type):
    config = open('./info.json')
    config = json.load(config)
    config = config[type]

    return config
def get_config(type):
    config = open('./config.json')
    config = json.load(config)
    config = config[type]

    return config

def convert_cookies_to_dict(cookies):
    cookies_dict = {}
    for cookie in cookies:
        cookie = cookie.split(';')[0].split('=', 1)
        cookies_dict[cookie[0]] = cookie[1]
    # cookies = dict([l.split("=", 1) for l in cookies.split("; ")])
    return cookies_dict

def learn(uid, url=''):
    http = urllib3.PoolManager()
    # url = 'http://dangxiao.pku.edu.cn/ybdy/lesson/play?v_id=1490&lesson_id=800&r_id=2885&r=video&pg=1'
    
    headers = get_config('headers')[2]
    headers['Cookie'] = 'uid=' + uid
    r = http.request(
        'GET',
        url,
        headers=headers
    )
    html = r.data.decode('utf-8')
    cookie = convert_cookies_to_dict(r.headers.getheaders('Set-Cookie'))
    headers = get_config('headers')[3]
    headers['Cookie'] = '_xsrf=' + cookie['_xsrf'] + '; uid='+cookie['uid']

    query = parse.parse_qs(urlparse(url).query)
    
    data = {}
    data['rid'] = re.search('rid: "(.*)",\r\n.* resource_id', html, re.M).group(1)
    data['resource_id'] = query['r_id'][0]
    data['video_id'] = query['v_id'][0]
    data['lesson_id'] = query['lesson_id'][0]
    data['_xsrf'] = re.search('value="(.*)"', html).group(1)

    body = ''
    for key in data.keys():
        if body == '':
            body = key + '=' + data[key] 
        else:
            body = body + '&' + key + '=' + data[key]  
    
    headers['Content-Length'] = len(body)

    r = http.request(
        'POST',
        "http://dangxiao.pku.edu.cn/ybdy/lesson/resource_record",
        headers=headers,
        body = body
    )

    # print(data['_xsrf'])
    # print(r.status)
    # print(r.data.decode('utf-8'))
    # print(r.headers)
    return r.status


def getid(token):
    # print(token)
    _rand  = str(np.random.random())

    headers = get_config('headers')[1]

    http = urllib3.PoolManager()

    r = http.request(
        'GET',
        'http://dangxiao.pku.edu.cn/user/casLogin',

        # 'http://dangxiao.pku.edu.cn/user/casLogin?_rand='+_rand+'&token='+token,
        fields = {
            '_rand': _rand,
            'token': token},
        headers=headers,
        retries=False
    )
    # return r
    uid = convert_cookies_to_dict(r.headers.getheaders('Set-Cookie'))['uid']
    headers['Cookie'] = 'uid=' + uid

    r = http.request(
        'GET',
        'http://dangxiao.pku.edu.cn',
        headers=headers
    )

    cookie = convert_cookies_to_dict(r.headers.getheaders('Set-Cookie'))
    uid = cookie['uid']

    return uid

    return learn(uid)


def login(userName, password):
    data = get_config('userInfo')
    headers = get_config('headers')[0]

    data['userName'] = userName
    data['password'] = password

    body = ''

    for key in data.keys():
        if len(body) == 0:
            body = key + '=' + quote(data[key], 'utf-8')
        else:
            body = body + '&' + key + '=' + quote(data[key], 'utf-8')

    content_len = len(body)

    headers['Content-Length'] = content_len
    http = urllib3.PoolManager(num_pools=1)

    r = http.request(
        'POST',
        'https://iaaa.pku.edu.cn/iaaa/oauthlogin.do',
        body=body,
        headers=headers,
    )
    data = r.data.decode('utf-8')

    token = json.loads(data)['token']

    return token

    # return getid(token)


if __name__ == '__main__':
    url = 'http://dangxiao.pku.edu.cn/ybdy/lesson/play?v_id=1490&lesson_id=800&r_id=2886&r=video&t=2&pg=1'
    
    userInfo = get_info('userInfo')
    courseLink = get_info("courseLink")
    
    
    token = login(userInfo['userName'], userInfo['password'])
    uid = getid(token)

    for course in courseLink:
        status = learn(uid, url=course)

        if str(status) == '200':
            print('OK:' + course)


