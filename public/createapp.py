import warnings, json, requests, sys,time,datetime, random
from retry import retry
warnings.filterwarnings('ignore')  # ignore warning

def gen_lower_str(length):
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join([random.choice(chars) for i in range(length)])

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

def redelivery(appbuy_url, body, service_instance_id, client_token, retry_num):
    try:
        print('redelivery app start!')
        time.sleep(1)
        url = "%s/serviceInstances/redeploy" % appbuy_url
        print(url)
        response = call_restful_api(url,body, "POST", client_token, 60)
        print(response)
        status=get_success_status(appbuy_url, service_instance_id, client_token, 12)
        if status == 200:
            return True
        if retry_num>0 and status != 200:
            retry_num -= 1
            print('redelivery retry_num: ' + str(retry_num))
            redelivery(appbuy_url, body, service_instance_id, client_token, retry_num)
        return False
    except Exception as e:
        print(e)
        raise e

def rollback(appbuy_url, service_instance_id, client_token):
    try:
        status = get_success_status(appbuy_url, service_instance_id, client_token, 0)
        if status != 404:
            unsubscribe_instance(appbuy_url, service_instance_id, client_token)
            status = get_rollback_status(appbuy_url, service_instance_id, client_token, 30)
            if status[0] is False:
                print('delete instance failed!')
            if status[1] != 'null':
                delete_instance_appbuy(appbuy_url, service_instance_id, client_token)
    except Exception as e:
        print(e)
        raise e

def get_rollback_status(appbuy_url, service_instance_id, client_token, retry_num):
    try:
        retry=False
        print('get rollback status start!')
        url = "%s/serviceInstances/%s" % (appbuy_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "GET", client_token, 60)
        print(response)
        if response[0] == 200:
            if response[1] == 'null':
                return True, 'null'
            res = json.loads(response[1])
            print(res)
            if res['lifecycleStatus'] == 'Inactive' and res['deployStatus'] == "Limited":
                return True, ''
            else:
                retry=True
        else:
            retry=True
        if retry_num>0 and retry is True:
            retry_num -= 1
            time.sleep(10)
            print('get rollback status retry_num: ' + str(retry_num))
            get_rollback_status(appbuy_url, service_instance_id, client_token, retry_num)
        return False, ''

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

@retry(Exception, tries=3, delay=5)
def delete_instance_appbuy(appbuy_url, service_instance_id, client_token):
    try:
        print('servicebuy: delete instance start!')
        url = "%s/serviceInstances/%s" % (appbuy_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "DELETE", client_token, 60)
        print(response)
        if response[0]!=204:
            raise Exception('delete appserviceinstance failed, serviceinstanceid is: %s' % service_instance_id)
    except Exception as e:
        print(e)
        raise e

def get_success_status(appbuy_url, service_instance_id, client_token, retry_num):
    try:
        retry=False
        print('get_status start!')
        url = "%s/serviceInstances/%s" % (appbuy_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "GET", client_token, 60)
        print(response)
        if response[0] == 200:
            if response[1] == 'null':
                retry = True
            else:
                res = json.loads(response[1])
                print(res)
                if res['data']['lifecycleStatus'] == "Active" and res['data']['deployStatus'] == "Deployed":
                    return 200
                else:
                    retry=True
        else:
            retry = True
        if retry_num>0 and retry is True:
            retry_num -= 1
            time.sleep(5)
            print('get success status retry_num: ' + str(retry_num))
            get_success_status(appbuy_url, service_instance_id, client_token, retry_num)
        if response[1] == 'null':
            return 404
        return response[0]
    except Exception as e:
        print(e)
        # raise e

def create_app(appbuy_url, client_token, service_config, service_instance_id):
    try:
        print('create app start!')
        url = appbuy_url + "/serviceInstances"
        print(url)
        body = json.dumps(service_config)
        print(body)
        response = call_restful_api(url, body, 'POST', client_token, 60)
        print(response)
        res = response[1]
        print(res)
        status = json.loads(res)['status']
        error = json.loads(res)['error']
        print(status)
        rb = False
        if status != 201:
            rb = True
            print(error)
        else:
            time_out_pause = 360
            start_ime = datetime.datetime.now()
            service_instanceid_info = json.loads(res)['data']
            while True:
                print("get deployment status")
                time.sleep(120)
                url = "{}/serviceInstances/{}".format(appbuy_url, service_instance_id)
                print(url)
                response = call_restful_api(url, '', 'GET', client_token, 60)
                res = response[1]
                status_code = json.loads(res)['status']
                if str(status_code) == "200":
                    lifecycle_status = json.loads(res)['data']['lifecycleStatus']
                    print(lifecycle_status)
                    deploy_status = json.loads(res)['data']['deployStatus']
                    print(deploy_status)
                    if lifecycle_status == "Active" and deploy_status == "Deployed":
                        return_map = {}
                        for service_instance in service_instanceid_info:
                            return_map[service_instance['serviceInstanceName']] = service_instance['appServiceInfo']['portalUrlPrefix']
                        id = ""
                        rb = False
                        break
                    else:
                        id = deploy_status
                    last_time = datetime.datetime.now()
                    period = (last_time - start_ime).seconds
                    print(str(period))
                    if period > time_out_pause:
                        break
                else:
                    print(res)
                    error_message = json.loads(res)['error']
                    id = error_message
                    break
            if id != "":
                rb = True
            else:
                print(return_map)
                f = open('urlprefix.json', 'w')
                f.write(json.dumps(return_map, indent=2))
                f.close()
        if rb:
            print('rollback start!')
            if redelivery(appbuy_url, body, service_instance_id, client_token, 3):
                print('redelivery app SUCCESS!')
            else:
                rollback(appbuy_url, service_instance_id, client_token)
            pass
    except Exception as e:
        print(e)
        raise e

def set_db_info(service):
    db_info,service_parameters = {},{}
    service_parameters['dbServiceInstanceId'] = service['serviceInstanceId']
    service_parameters['dbServiceInstanceName'] = service['serviceInstanceName']
    db_info['deliverType'] = service['deliverType']
    db_info['serviceName'] = service['serviceName']
    db_info['serviceCategory'] = service['serviceCategory']
    db_info['servicePlanName'] = service['servicePlanName']
    db_info['serviceProperty'] = service['serviceProperty']
    db_info['serviceParameters'] = service_parameters
    return db_info

if __name__ == '__main__':
    print(sys.argv)
    cluster_info = sys.argv[1]
    sso_url = sys.argv[2]
    appbuy_url = sys.argv[3]
    service_config = json.loads(read_file(sys.argv[4]))
    service_infos = service_config['serviceInfo']
    app_name = sys.argv[5]
    postgre_service_config = json.loads(read_file(sys.argv[6]))
    service_info, service_instance_id = [], ''
    for service in service_infos:
        if service['serviceName'].lower()==app_name.lower():
            # service['serviceInstanceName'] += gen_lower_str(4)
            service_instance_id = service['serviceInstanceId']
            service_config['deliverType'] = service['deliverType']
            service_info.append(service)
        if app_name.lower() == 'dashboard':
            if service['serviceName'].lower()!='postgresql' and service['deliverType']=='servicebuy':
                service_info.append(set_db_info(service))
        else:
            if service['deliverType']=='servicebuy':
                service_info.append(set_db_info(service))
    if app_name.lower() == 'dashboard':
        service_info.append(set_db_info(postgre_service_config['serviceInfo'][0]))
    service_config['serviceInfo'] = service_info
    cluster_infos = cluster_info.split(':')
    service_config['clusterName'] = cluster_infos[1]
    service_config['workspaceId'] = cluster_infos[2]
    service_config['workspaceName'] = cluster_infos[3]
    service_config['namespaceName'] = cluster_infos[4]
    grant_type, client_id, client_secret, duration = 'client_credentials', 'pipeline-00000000016', \
                 'ZTY0MzRkZWYtNmZjNC0xMWVhLWI5ZGUtMzA5YzIzZjMyZjFj-pipeline','eternal'
    client_token = get_client_token(sso_url, grant_type, client_id, client_secret, duration)
    create_app(appbuy_url, client_token, service_config, service_instance_id)