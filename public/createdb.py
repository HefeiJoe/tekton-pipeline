import warnings, json, requests, os, sys, time,datetime,random
from retry import retry
warnings.filterwarnings('ignore')  # ignore warning

def get_time():
    return str(round(time.time() * 1000))

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
    return response.status_code, response.text, response.elapsed.microseconds / 1000

@retry(Exception, tries=3, delay=5)
def redelivery(service_url, service_instance_id, body, token):
    try:
        print('redelivery db start!')
        time.sleep(1)
        url = "%s/serviceInstances/redeploy" % (service_url)
        print(url)
        response = call_restful_api(url,body, "POST", token, 60)
        print(response)
        status=get_success_status(service_url, service_instance_id, token, 12)
        if status == 200:
            return True
        if status != 200:
            raise Exception(status)
        return False
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def unsubscribe_instance(service_url, service_instance_id, token):
    try:
        print('delete db instance start!')
        url = "%s/serviceInstances/%s/cancel" % (service_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "DELETE", token, 60)
        print(response)
        if response[0]!=204:
            raise Exception('delete db instance failed!')
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def delete_instance_servicebuy(service_url, service_instance_id, token):
    try:
        print('delete db instance start!')
        url = "%s/serviceInstances/%s?purge=false&cascade=true&deleteData=true" % (service_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "DELETE", token, 60)
        print(response)
        if response[0]!=204:
            raise Exception('delete db instance failed!')
    except Exception as e:
        print(e)
        raise e

def rollback(service_url, service_instance_id, token):
    try:
        status = get_success_status(service_url, service_instance_id, token, 0)
        if status != 404:
            unsubscribe_instance(service_url, service_instance_id, token)
            status = get_rollback_status(service_url, service_instance_id, token, 12)
            if status[0] is False:
                print('delete instance failed!')
            if status[1] != 'null':
                delete_instance_servicebuy(service_url, service_instance_id, token)
    except Exception as e:
        print(e)
        raise e

def get_success_status(service_url, service_instance_id, token, retry_num):
    try:
        retry=False
        print('get_status start!')
        url = "%s/serviceInstances/%s" % (service_url, service_instance_id)
        print(url)
        response = call_restful_api(url,'', "GET", token, 60)
        print(response)
        if response[0] == 200:
            if response[1] == 'null':
                retry = True
            else:
                res = json.loads(response[1])
                print(res)
                if res['lifecycleStatus'] == "Active" and res['status'] == "exist":
                    return 200
                else:
                    retry=True
        else:
            retry = True
        if retry_num>0 and retry is True:
            retry_num -= 1
            time.sleep(5)
            print('get success status retry_num: ' + str(retry_num))
            get_success_status(service_url, service_instance_id, token, retry_num)
        if response[1] == 'null':
            return 404
        return response[0]
    except Exception as e:
        print(e)
        raise e

def get_rollback_status(service_url, service_instance_id, token, retry_num):
    try:
        retry=False
        print('get_status start!')
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
            print('get rollback status retry_num: ' + str(retry_num))
            get_rollback_status(service_url, service_instance_id, token, retry_num)
        return False, ''
    except Exception as e:
        print(e)
        raise e

def write_res():
    f = open('dbresult.txt', 'w')
    f.write('SUCCESS')
    f.close()

def create_db(service_url, token, service_configs, cluster_info,db_name):
    try:
        create_db_res = True
        service_info = service_configs['serviceInfo']
        for service in service_info:
            if create_db_res is False:
                break
            service_configs['serviceInfo'] = [service]
            cluster_infos = cluster_info.split(':')
            print(cluster_infos)
            service_instance_id = service['serviceInstanceId']
            serviceName=db_name
            body = json.dumps(service_configs)
            print(body)
            print("creat %s start!" % serviceName)
            url = "{}/serviceInstances".format(service_url)
            print(url)
            response = call_restful_api(url, body, "POST", token, 60)
            print(response)
            rb = False
            if response[0] == 201:
                if serviceName == "Redis":
                    time_out_pause = 300
                    start_time = datetime.datetime.now()
                    while True:
                        time.sleep(15)
                        url = "{}/serviceInstances/{}".format(service_url, service_instance_id)
                        response = call_restful_api(url, "", "GET", token, 60)
                        res = json.loads(response[1])
                        print(res)
                        if res['lifecycleStatus'] == "Active" and res['status'] == "exist":
                            rb = False
                            create_db_res = True
                            break
                        else:
                            rb = True
                            create_db_res = False
                        period = (datetime.datetime.now()-start_time).seconds
                        print(str(period))
                        if period > time_out_pause:
                            create_db_res = False
                            rb = True
                            break
                else:
                    if get_success_status(service_url, service_instance_id, token, 12) != 200:
                        create_db_res = False
                        rb = True
                    else:
                        create_db_res = True
                        rb = False
                        continue
            else:
                create_db_res = False
                rb = True
            if rb:
                print('rollback start!')
                if serviceName != "Redis":
                    if redelivery(service_url, service_instance_id, body, token):
                        create_db_res = True
                    else:
                        create_db_res = False
                rollback(service_url, service_instance_id, token)
            else:
                create_db_res = True
        if create_db_res:
            write_res()
    except Exception as e:
        raise e


if __name__ == '__main__':
    print(sys.argv)
    service_url = sys.argv[1]
    sso_url = sys.argv[2]
    cluster_info = sys.argv[3]
    service_config = json.loads(read_file(sys.argv[4]))
    service_infos = service_config['serviceInfo']
    db_name = sys.argv[5]
    postgre_service_config = json.loads(read_file(sys.argv[6]))['serviceInfo']
    service_info = []
    for service in service_infos:
        if service['serviceName'].lower()==db_name.lower():
            service_config['deliverType'] = service['deliverType']
            # service['serviceInstanceName'] += gen_lower_str(4)
            service_info.append(service)
            break
    if db_name.lower() == 'postgresql':
        # postgre_service_config[0]['serviceInstanceName'] += gen_lower_str(4)
        service_info.append(postgre_service_config[0])
    service_config['serviceInfo'] = service_info
    cluster_infos = cluster_info.split(':')
    print(cluster_infos)
    service_config['clusterName'] = cluster_infos[1]
    service_config['workspaceId'] = cluster_infos[2]
    service_config['workspaceName'] = cluster_infos[3]
    service_config['namespaceName'] = cluster_infos[4]
    grant_type, client_id, client_secret, duration = 'client_credentials', 'pipeline-00000000016', \
                                                     'ZTY0MzRkZWYtNmZjNC0xMWVhLWI5ZGUtMzA5YzIzZjMyZjFj-pipeline', 'eternal'
    client_token = get_client_token(sso_url, grant_type, client_id, client_secret, duration)
    create_db(service_url, client_token, service_config, cluster_info,db_name)