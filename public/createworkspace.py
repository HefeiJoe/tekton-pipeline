# -*- coding: utf-8 -*-
import copy
import json
import sys
import requests
import time
import random
from retry import retry

def get_time():
    return str(round(time.time() * 1000))
def gen_lower_str(length):
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join([random.choice(chars) for i in range(length)])

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

def create_service_instance(mpbuy_url, service_config, token, namespace_name, mp_url, datacenter_code, workspace_name, retry):
    try:
        url = "%s/serviceInstances" % mpbuy_url
        print(url)
        workspace_id, cluster_name, service_instance_id = '', '', service_config['serviceInfo'][0]['serviceInstanceId']
        print(json.dumps(service_config))
        response = call_restful_api(url,json.dumps(service_config),"POST", token, 60)
        print(response)
        response_body = json.loads(response[1])
        if (response_body['status']==200 or response_body['status']==201):
            res = response_body['content']
            workspace_id, cluster_name = res['workspaceId'], res['clusterName'],
        else:
            raise Exception(response[1])
        namespace_lists = namespace_name.split(',')
        namespace_list, return_str = [],''
        for ns in namespace_lists:
            ns = ns[0:3]+get_time()
            namespace_list.append(ns)
            create_namespace(mp_url, datacenter_code, cluster_name, workspace_id, ns, token)
            return_str += '%s:%s:%s:%s:%s:%s ' % (datacenter_code,cluster_name,workspace_id,workspace_name,ns,'shared')
        return_str = return_str.strip()
        print(return_str)
        print(service_instance_id)
        f = open('return_str.txt', 'w')
        f.write(return_str)
        f.close()
    except Exception as e:
        print(e)
        roolback_ws(mpbuy_url, service_instance_id, token)
        retry -=1
        if retry>0:
            time.sleep(5)
            create_service_instance(mpbuy_url, service_config, token, namespace_name, mp_url, datacenter_code, workspace_name, retry)
        else:
            raise e

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
def unsubscribe_instance(mpbuy_url, service_instance_id, token):
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

def roolback_ws(mpbuy_url, service_instance_id, token):
    status = get_ws_instance_status(mpbuy_url, service_instance_id, token)
        # status = get_ws_instance_status(mpbuy_url, service_instance_id, token, 12)
        # if status is False:
    if status[0]:
        unsubscribe_instance(mpbuy_url, service_instance_id, token)
    if status[1]:
        delete_workspace(mpbuy_url, service_instance_id, token)

@retry(Exception, tries=3, delay=5)
def create_namespace(mp_url, datacenter_code, cluster, workspace, name, token):
    try:
        url = "%s/datacenter/%s/cluster/%s/namespace" % (mp_url, datacenter_code, cluster)
        body,metadata,labels = {}, {}, {}
        labels['workspace'] = workspace
        metadata['labels'] = labels
        metadata['name'] = name
        body['metadata'] = metadata
        print(url)
        print("###create_namespace body: ")
        print(json.dumps(body, indent=4))
        response = call_restful_api(url,json.dumps(body), "POST", token, 60)
        print(response)
        response_body = json.loads(response[1])
        print(response[0])
        print(response_body)
    except Exception as e:
        print(e)
        raise e

def write_file(file_path, content):
    f = open(file_path, 'w')
    f.write(content)
    f.close()

if __name__ == '__main__':
    print(sys.argv)
    mp_url = sys.argv[1]
    sso_url = sys.argv[2]
    mpbuy_url = sys.argv[3]
    service_configs = sys.argv[4].replace('\(','(').replace('\)',')')
    service_config = json.loads(service_configs)
    for service in service_config['serviceInfo']:
        if service['servicePlanName']!='General-Workspace':
            service['serviceInstanceName'] += gen_lower_str(4)
    service_infos = service_config['serviceInfo']
    print(service_infos)
    datacenter_code, subscription_id = service_config['datacenterCode'], service_config['subscriptionId']
    workspace_name = 'mkp' + get_time()
    namespace_name = 'default'
    service_config_tmp = ''.join(service_configs.split())
    dashboard_postgre_info = []
    svs = ''
    for service in service_infos:
        svs+=service['serviceName']+' '
    write_file('svs.txt', svs[0:-1])
    if service_config_tmp.count('"serviceName":"PostgreSQL"')==2:
        for service in service_infos:
            if service['serviceName'].lower() == 'postgresql':
                dashboard_postgre_info.append(service)
                break
    for service in service_infos:
            if service['serviceName'].lower() == 'deviceon':
                namespace_name += ',deviceon'
                break
    service_infos.remove(dashboard_postgre_info[0])

    service_config_copy = copy.deepcopy(service_config)
    service_config_copy['serviceInfo'] = service_infos
    # print('serviceInfo: \n' + json.dumps(service_config_copy, indent=2))
    write_file('./serviceInfo.json', json.dumps(service_config_copy, indent=2))

    service_config_copy['serviceInfo'] = dashboard_postgre_info
    # print('postgreServiceInfo: \n'+json.dumps(service_config_copy, indent=2))
    write_file('./postgreServiceInfo.json', json.dumps(service_config_copy, indent=2))
    for service in service_infos:
        if service['servicePlanName']=='General-Workspace':
            service['serviceInstanceName'] = workspace_name
            service_config['serviceInfo'] = [service]
            service_config['deliverType'] = service['deliverType']
            break
    # print('service_config: \n' + json.dumps(service_config, indent=2))
    grant_type, client_id, client_secret, duration = 'client_credentials', 'pipeline-00000000016', \
                                                     'ZTY0MzRkZWYtNmZjNC0xMWVhLWI5ZGUtMzA5YzIzZjMyZjFj-pipeline', 'eternal'
    client_token = get_client_token(sso_url, grant_type, client_id, client_secret, duration)
    create_service_instance(mpbuy_url, service_config, client_token, namespace_name, mp_url, datacenter_code, workspace_name, 3)
