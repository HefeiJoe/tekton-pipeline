# -*- coding: utf-8 -*-
import json
import requests
import sys
import re
def login(sso_url,username,password):
    url = "%s/auth/native" % sso_url
    name=username
    passd=password
    headers={'Content-Type':'application/json;charset=UTF-8'}
    param ={"username":name,"password":passd}
    data = json.dumps(param)
    response=requests.post(url,data, headers=headers)
    token = response.json()['accessToken']
    Token = "Bearer %s" % token
    return Token
def CallRestfulAPI(url, data, method, auth, timeout, content_type="application/json"):
    headers = {"Authorization": auth, "Content-Type": content_type, "Accept": content_type, "Cache-Control": "no-cache"}
    if method == "GET":
        response = requests.get(url, headers=headers, timeout=timeout, verify=False)
    if method == "POST":
        response = requests.post(url, data=data, headers=headers, timeout=timeout, verify=False)
    return response.status_code, response.text, response.elapsed.microseconds / 1000
def check_mail(mail_address):
    rex = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'
    return re.match(rex, mail_address)

def read_line(path,replace,target_mail_address):
    str = ''
    username = target_mail_address.split('@')[0]
    for line in open(path):
        tmp = line.replace('\n', '').replace('{5}', replace[0]).replace('{2}', username).strip()
        if len(replace) > 2:
            tmp = tmp.replace('{3}',replace[1]).replace('{4}',replace[2])
        t = tmp
        ts = ''
        if '{1}' in tmp:
            if len(replace) > 2:
                success_map = replace[3]
            else:
                success_map = replace[1]
            for k,v in success_map.items():
                vs = ''
                for i in v:
                    vs += '<p class="MsoNormal"><span lang="EN-US" style="font-family:&quot;Arial&quot;,sans-serif; color:#333333"><a href=\"'+i+'\">'+i+'</a></span></p>'
                ts += '<tr>'+t.replace('{1}',k)+t.replace('{1}',vs)+'</tr>'
        if ts == '':
            str += tmp
        else:
            str += ts
    print(str)
    return str

def send_mail(notification_url, token, target_mail_address, email_subject, send_message):
    try:
        url = "%s/api/v1.5/Groups/directsend" % notification_url
        if check_mail(target_mail_address) is None:
            email_subject += "--Invalid email adress!User: "+target_mail_address
            target_mail_address = "WISE-PaaS.SRE@advantech.com"
        body, config, sendList = {}, {}, []
        stmp_host = 'smtp.mxhichina.com'
        stmp_username = 'ensaas@wise-paas.com.cn'
        stmp_password = 'XfBX$c4e3E^BQ8#P95kFfcb4A?'
        stmp_port = 465
        stmp_secure = True
        stmp_method = 'ssl'
        sender_email = 'EnSaaS@wise-paas.com.cn'
        config['host'] = stmp_host
        config['port'] = stmp_port
        config['secure'] = stmp_secure
        config['method'] = stmp_method
        config['username'] = stmp_username
        config['password'] = stmp_password
        config['senderEmail'] = sender_email
        config['emailSubject'] = email_subject
        if "WISE-PaaS.SRE@advantech.com"!=target_mail_address:
            sendList.append({'recipientType': 'to',"target": target_mail_address})
            # sendList.append({'recipientType': 'cc', "target": "WISE-PaaS.SRE@advantech.com"})
        else:
            sendList.append({'recipientType': 'to', "target": target_mail_address})
        body['type'] = 'email'
        body['message'] = send_message
        body['config'] = config
        body['sendList'] = sendList
        response = CallRestfulAPI(url,json.dumps(body),"POST", token, 60)
        response_body = json.loads(response[1])[0]
        if (response_body['isSuccess'] is True):
            print(response_body)
        else:
            print(response_body)
    except Exception as e:
        print(e)
if __name__ == '__main__':
    print(sys.argv)
    sso_username = sys.argv[1]
    sso_password = sys.argv[2]
    notification_url = sys.argv[3]
    sso_url = sys.argv[4]
    target_mail_address = sys.argv[5]
    email_subject = sys.argv[6]
    path = sys.argv[7]
    replace_path = str(sys.argv[8])
    print(replace_path)
    send_message = ''
    if ''!=sys.argv[9] and '0'!=sys.argv[9]:
        print(sys.argv[9:])
        for msg in sys.argv[9:]:
            send_message+=msg+' '
        send_mail(notification_url, login(sso_url, sso_username, sso_password), target_mail_address, email_subject,
                  send_message[:-1])
    else:
        replace_path=replace_path.replace('"','')
        replace = replace_path.split(',')
        print(replace)
        re_list = []
        map = {}
        for rep in replace:
            if ':' not in rep:
                re_list.append(rep)
            else:
                l = []
                re_split = rep.split(':')
                for r in rep[len(re_split[0])+1:].split(';'):
                    l.append(r)
                map.setdefault(re_split[0],l)
        re_list.append(map)
        print(re_list)
        if path == 'officialdeliverynotice.html' or path == 'trialdeliverynotice.html':
            send_message = read_line(path,re_list,target_mail_address)
            send_mail(notification_url, login(sso_url, sso_username, sso_password), target_mail_address, email_subject,
                      send_message)