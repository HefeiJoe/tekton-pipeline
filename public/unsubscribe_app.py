import json
import sys
import requests
import time
from retry import retry

def read_file(path):
    f = open(path, 'r', encoding='utf-8')
    res = f.read()
    f.close()
    return res

@retry(Exception, tries=3, delay=5)
def get_client_token(sso_url, grant_type , client_id, client_secret, duration):
    url = "%s/oauth/token?grant_type=%s&client_id=%s&client_secret=%s&duration=%s" % (
        sso_url, grant_type , client_id, client_secret, duration)
    headers = {'Content-Type': 'application/json;charset=UTF-8'}
    try:
        response = requests.post(url, '', headers=headers)
        token = response.json()['accessToken']
        Token = "Bearer %s" % token
        return Token
    except Exception as e:
        print(e)
        raise e

def call_restful_api(url, data, method, auth, timeout, content_type="application/json"):
    headers = {"Authorization": auth, "Content-Type": content_type, "Accept": content_type, "Cache-Control": "no-cache"}
    if method == "GET":
        response = requests.get(url, headers=headers, timeout=timeout, verify=False)
    if method == "POST":
        response = requests.post(url, data=data, headers=headers, timeout=timeout, verify=False)
    if method == "PUT":
        response = requests.put(url, data=data, headers=headers, timeout=timeout, verify=False)
    if method == "DELETE":
        response = requests.delete(url, headers=headers, timeout=timeout, verify=False)
    if method == "PATCH":
        response = requests.patch(url, data=data, headers=headers, timeout=timeout, verify=False)
    return response.status_code, response.text, response.elapsed.microseconds / 1000

def get_app_instance_status(appbuy_url, service_instance_id, client_token, retry_num):
    try:
        retry=False
        print('get_status start!')
        url = "%s/serviceInstances/%s" % (appbuy_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "GET", client_token, 60)
        print(response)
        if response[0] == 200:
            if response[1] == 'null':
                return False
            else:
                res = json.loads(response[1])
                print(res)
                lifecycle_status = res['data']['lifecycleStatus']
                if lifecycle_status == "Inactive" or lifecycle_status == "None":
                    return False
                else:
                    return True
        else:
            retry = True
        if retry_num>0 and retry is True:
            retry_num -= 1
            time.sleep(5)
            print('get app_instance status retry_num: ' + str(retry_num))
            get_app_instance_status(appbuy_url, service_instance_id, client_token, retry_num)
        return False
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def unsubscribe_instance(appbuy_url, service_instance_id, client_token):
    try:
        print('delete app instance start!')
        url = "%s/serviceInstances/%s/cancel" % (appbuy_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "DELETE", client_token, 60)
        print(response)
        if response[0]!=204:
            raise Exception('delete app instance failed!')
    except Exception as e:
        print(e)
        raise e
    
def unsubscribe_app(appbuy_url, service_info, client_token):
    try:
        for service in service_info:
            if service['deliverType']!='appbuy':
                continue
            service_instance_id = service['serviceInstanceId']
            if get_app_instance_status(appbuy_url, service_instance_id, client_token, 5):
                unsubscribe_instance(appbuy_url, service_instance_id, client_token)
    except Exception as e:
        print(e)
        raise e

if __name__ == '__main__':
    print(sys.argv)
    sso_url = sys.argv[1]
    appbuy_url = sys.argv[2]
    service_info = json.loads(read_file(sys.argv[3]))
    grant_type, client_id, client_secret, duration = 'client_credentials', 'pipeline-00000000016', \
                                                     'ZTY0MzRkZWYtNmZjNC0xMWVhLWI5ZGUtMzA5YzIzZjMyZjFj-pipeline', 'eternal'
    client_token = get_client_token(sso_url, grant_type, client_id, client_secret, duration)
    unsubscribe_app(appbuy_url, service_info, client_token)