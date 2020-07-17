import json
import sys
import time
import requests
from retry import retry

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

def get_app_roolback_status(appbuy_url, service_instance_id, client_token, retry_num):
    try:
        retry=False
        print('get_app_roolback_status start!')
        url = "%s/serviceInstances/%s" % (appbuy_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "GET", client_token, 60)
        print(response)
        if response[0] == 200:
            if response[1] == 'null':
                return True, 'null'
            res = json.loads(response[1])
            print(res)
            if res['data']['lifecycleStatus'] == 'Inactive' and res['data']['deployStatus'] == "Limited":
                return True, ''
            else:
                retry=True
        else:
            retry=True
        if retry_num>0 and retry is True:
            retry_num -= 1
            time.sleep(10)
            print('get_app_roolback_status retry_num: ' + str(retry_num))
            get_app_roolback_status(appbuy_url, service_instance_id, client_token, retry_num)
        return False, ''

    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def get_app_instance_status(appbuy_url, service_instance_id, client_token):
    try:
        print('get_app_instance_status start!')
        url = "%s/serviceInstances/%s" % (appbuy_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "GET", client_token, 60)
        print(response)
        if response[0] == 200:
            if response[1] == 'null':
                return False, False
            else:
                res = json.loads(response[1])
                lifecycle_status, deploy_status = res['data']['lifecycleStatus'], res['data']['deployStatus']
                if lifecycle_status == 'None':
                    return False,False
                if lifecycle_status == "Active" and lifecycle_status == "Deployed":
                    return True,True
                if lifecycle_status == 'Inactive' and lifecycle_status == 'Limited':
                    return False,True
                else:
                    return False,True
        else:
            return False,False
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def delete_instance_appbuy(appbuy_url, service_instance_id, client_token):
    try:
        print('servicebuy: delete instance start!')
        url = "%s/serviceInstances/%s" % (appbuy_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "DELETE", client_token, 60)
        print(response)
        if response[0]!=204:
            print(response)
            # raise Exception('delete appserviceinstance failed, serviceinstanceid is: %s' % service_instance_id)
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def unsubscribe_instance_app(appbuy_url, service_instance_id, client_token):
    try:
        print('delete app instance start!')
        url = "%s/serviceInstances/%s/cancel" % (appbuy_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "DELETE", client_token, 60)
        print(response)
        status = response[0]
        if status!=204 and status!=404:
            raise Exception('delete app instance failed!')
    except Exception as e:
        print(e)
        raise e

def get_db_roolback_status(service_url, service_instance_id, token, retry_num):
    try:
        retry=False
        print('get_db_roolback_status start!')
        url = "%s/serviceInstances/%s" % (service_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "GET", token, 60)
        print(response)
        if response[0] == 200:
            if response[1] == 'null':
                return True, 'null'
            res = json.loads(response[1])
            print(res)
            if res['lifecycleStatus'] == 'Inactive' and res['status'] == "detached":
                return True,''
            else:
                retry=True
        else:
            retry = True
        if retry_num>0 and retry is True:
            retry_num -= 1
            time.sleep(5)
            print('get_db_roolback_status retry_num: ' + str(retry_num))
            get_db_roolback_status(service_url, service_instance_id, token, retry_num)
        return False, ''
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def get_db_instance_status(service_url, service_instance_id, token):
    try:
        print('get db instance status start!')
        url = "%s/serviceInstances/%s" % (service_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "GET", token, 60)
        print(response)
        if response[0] == 200:
            if response[1] == 'null':
                return False,False
            else:
                res = json.loads(response[1])
                if res['lifecycleStatus'] == 'Inactive' and res['status'] == "detached":
                    return False,True
                return True,True
        else:
            return False,False
    except Exception as e:
        print(e)
        raise e

# def get_ws_roolback_status(mpbuy_url, service_instance_id, token, retry_num):
#     try:
#         retry=False
#         print('get_ws_roolback_status start!')
#         url = "%s/serviceInstances/%s" % (appbuy_url, service_instance_id)
#         print(url)
#         response = call_restful_api(url,'', "GET", token, 60)
#         print(response)
#         if response[0] == 404:
#             return True
#         else:
#             retry = True
#         if retry_num>0 and retry is True:
#             retry_num -= 1
#             time.sleep(5)
#             print('get_ws_roolback_status: ' + str(retry_num))
#             get_ws_roolback_status(mpbuy_url, service_instance_id, token, retry_num)
#         return False
#     except Exception as e:
#         print(e)
#         raise e

@retry(Exception, tries=3, delay=5)
def get_ws_instance_status(mpbuy_url, service_instance_id, token):
    try:
        print('get db instance status start!')
        url = "%s/serviceInstances/%s" % (mpbuy_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "GET", token, 60)
        print(response)
        res = json.loads(response[1])
        if response[0] == 200:
            if res['content']['lifecycleStatus'] == 'Inactive' and res['content']['deployStatus']=='Success':
                return False,True
            return True,True
        return False,False
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def delete_instance_servicebuy(service_url, service_instance_id, token):
    try:
        print('servicebuy: delete instance start!')
        url = "%s/serviceInstances/%s?purge=false&cascade=true&deleteData=true" % (service_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "DELETE", token, 60)
        print(response)
        if response[0]!=204:
            raise Exception('servicebuy: delete instance failed!')
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def delete_workspace(mpbuy_url, service_instance_id, token):
    try:
        print('delete workspace start!')
        url = "%s/serviceInstances/%s" % (mpbuy_url, service_instance_id)
        res = call_restful_api(url,'', "DELETE", token, 60)
        print(res)
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def unsubscribe_instance_db(service_url, service_instance_id, token):
    try:
        print('delete db instance start!')
        url = "%s/serviceInstances/%s/cancel" % (service_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "DELETE", token, 60)
        print(response)
        status = response[0]
        if status!=204 and status!=404:
            raise Exception('delete db instance failed!')
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def unsubscribe_instance_ws(mpbuy_url, service_instance_id, token):
    try:
        print('unsubscribe ws instance start!')
        url = "%s/serviceInstances/%s/cancel" % (mpbuy_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "DELETE", token, 60)
        print(response)
        if response[0]!=200:
            raise Exception('unsubscribe ws instance failed!')
    except Exception as e:
        print(e)
        raise e

def roolback_app(appbuy_url, service_info, client_token):
    try:
        for service in service_info:
            if service['deliverType']!='appbuy':
                continue
            service_instance_id = service['serviceInstanceId']
            status0 = get_app_instance_status(appbuy_url, service_instance_id, client_token)
            if status0[0]:
                unsubscribe_instance_app(appbuy_url, service_instance_id, client_token)
            if status0[1]:
                status = get_app_roolback_status(appbuy_url, service_instance_id, client_token, 30)
                if status[0] is False:
                    print('delete instance failed!')
                if status[1] != 'null':
                    delete_instance_appbuy(appbuy_url, service_instance_id, client_token)
    except Exception as e:
        print(e)
        raise e

def roolback_db(service_url, service_info, token):
    try:
        for service in service_info:
            if service['deliverType'] != 'servicebuy':
                continue
            service_instance_id = service['serviceInstanceId']
            status0 = get_db_instance_status(service_url, service_instance_id, token)
            if status0[0]:
                unsubscribe_instance_db(service_url, service_instance_id, token)
            if status0[1]:
                status = get_db_roolback_status(service_url, service_instance_id, token, 12)
                if status[0] is False:
                    print('delete instance failed!')
                if status[1] != 'null':
                    delete_instance_servicebuy(service_url, service_instance_id, token)
    except Exception as e:
        print(e)
        raise e
def roolback_ws(mpbuy_url, service_info, token):
    for service in service_info:
        if service['deliverType'] == 'mpbuy':
            service_instance_id = service['serviceInstanceId']
            status = get_ws_instance_status(mpbuy_url, service_instance_id, token)
            if status[0]:
                unsubscribe_instance_ws(mpbuy_url, service_instance_id, token)
            if status[1]:
                delete_workspace(mpbuy_url, service_instance_id, token)
if __name__ == '__main__':   
    print(sys.argv)
    mp_url = sys.argv[1]
    sso_url = sys.argv[2]
    mpbuy_url = sys.argv[3]
    appbuy_url = sys.argv[4]
    service_url = sys.argv[5]
    service_config = sys.argv[6].replace('\(','(').replace('\)',')')
    service_info = json.loads(service_config)['serviceInfo']
    grant_type, client_id, client_secret, duration = 'client_credentials', 'pipeline-00000000016', \
                                                     'ZTY0MzRkZWYtNmZjNC0xMWVhLWI5ZGUtMzA5YzIzZjMyZjFj-pipeline', 'eternal'
    client_token = get_client_token(sso_url, grant_type, client_id, client_secret, duration)
    roolback_app(appbuy_url, service_info, client_token)
    roolback_db(service_url, service_info, client_token)
    roolback_ws(mpbuy_url, service_info, client_token)