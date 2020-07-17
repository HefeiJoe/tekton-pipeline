import json
import os
import sys
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
    headers={"Content-Type": content_type, "Accept": content_type, "Cache-Control": "no-cache"}
    if auth is not None:
        headers = {"Authorization": auth, "Content-Type": content_type, "Accept": content_type, "Cache-Control": "no-cache"}
    if method == "GET":
        response = requests.get(url, headers=headers, timeout=timeout, verify=False)
    if method == "POST":
        response = requests.post(url, data=data, headers=headers, timeout=timeout, verify=False)
    return response.status_code, response.text, response.elapsed.microseconds / 1000

@retry(Exception, tries=3, delay=5)   
def get_dashboard_url(dashboardurl_path):
    try:
        serviceurl_str = ''
        if os.path.exists(dashboardurl_path):
            f = open(dashboardurl_path, 'r', encoding='utf-8')
            lines = f.read()
            f.close()
            data_service_str = lines.split('###')
            for data_service in data_service_str:
                data_service = data_service.replace('\n', '').strip()
                if '' != data_service:
                    dahboardurlinfo = json.loads(data_service)
                    length = dahboardurlinfo['length']
                    for i in range(length):
                        index = 'service' + str(i)
                        dashboardurl = dahboardurlinfo[index]['dashboardUrl']
                        serviceurl_str += '"' + dashboardurl + '"'
                        serviceurl_str += ','
            serviceurl_str = serviceurl_str[:-1]
        return serviceurl_str
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def get_urlprefix(listing_system_url, service_name, service_plan, datacenter_code):
    try:
        print('get urlprefix start!')
        url = "%s/deployment/%s/plan/%s?datacenterCode=%s" % (listing_system_url, service_name, service_plan, datacenter_code)
        print(url)
        response = call_restful_api(url,'', "GET", client_token, 60)
        print(response)
        if response[0] == 200:
            res = json.loads(response[1])
            return res['data'][0]['extraParam']['urlPrefix']
        else:
            raise Exception(response[1])
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def get_urlprefix_dict(service_info, listing_system_url, datacenter_code, client_token):
    try:
        urlprefix_dict = {}
        for service in service_info:
            if service['deliverType']!='appbuy':
                continue
            urlprefix_list = get_urlprefix(listing_system_url, service['serviceName'], service['servicePlanName'], datacenter_code)
            urlprefix_dict[service['serviceName']] = urlprefix_list
        return urlprefix_dict
    except Exception as e:
        print(e)
        raise e

@retry(Exception, tries=3, delay=5)
def somketest(urlprefix_path_dict, identity, subscriptionId, start_date, end_date,cluster_namespace,cluster_cluster,
              externaldomain,deviceon_namespace,serviceurl_str):
    try:
        success_map,failed_map = {},{}
        success_str,failed_str='',''
        if "trial" == identity:
            success_str = '"'+subscriptionId+'","'+start_date+'","'+end_date+'",'
        else:
            success_str = '"' + subscriptionId + '",'
        for key in urlprefix_path_dict.keys():
            success_list, failed_list =[], []
            urlprefix_value = urlprefix_path_dict[key]
            for urlprefix in urlprefix_value:
                prefix = 'https://%s-%s-%s.%s'%(urlprefix,cluster_namespace,cluster_cluster,externaldomain)
                if "DeviceOn" == urlprefix:
                    prefix = 'https://%s-%s-%s.%s' % (urlprefix, deviceon_namespace, cluster_cluster, externaldomain)
                print(prefix)
                response = call_restful_api(url=prefix, data=None, method='GET', auth=None, timeout=60)
                code = int(response[0])
                if code <200 or code >400:
                    failed_list.append(prefix)
                else:
                    success_list.append(prefix)
            success_map[urlprefix] = success_list
            failed_map[urlprefix] = failed_list
            if len(success_list) != 0:
                success_str += '"' + urlprefix + '":'
                for success_url in success_list:
                    success_str += '"' + success_url + '";'
                success_str = success_str[:-1]+','
            print(success_str)
            if len(failed_list) != 0:
                failed_str +=urlprefix + ':\n'
        if ''==serviceurl_str:
            success_str = success_str[:-1]
        else:
            success_str += serviceurl_str
        n = open('success_str.txt', 'w', encoding='utf-8')
        n.write(success_str)
        n.close()
        n = open('failed_str.txt', 'w', encoding='utf-8')
        n.write(failed_str)
        n.close()
        if '' != failed_str:
            raise Exception('failed_str is not null')
    except Exception as e:
        print(e)
        raise e

if __name__ == '__main__':
    service_configs = sys.argv[1].replace('\(','(').replace('\)',')')
    service_config = json.loads(service_configs)
    service_info = service_config['serviceInfo']
    datacenter_code = service_config['datacenterCode']
    # urlprefix_path = sys.argv[1]
    # dashboardurl_path = sys.argv[2]
    identity = sys.argv[2]
    subscriptionId = sys.argv[3]
    start_date = sys.argv[4]
    end_date = sys.argv[5]
    cluster_namespace = sys.argv[6]
    cluster_cluster = sys.argv[7]
    externaldomain = sys.argv[8]
    deviceon_namespace = sys.argv[9]
    sso_url = sys.argv[10]
    listing_system_url = sys.argv[11]

    # serviceurl_str = get_dashboard_url(dashboardurl_path)
    serviceurl_str = ''
    grant_type, client_id, client_secret, duration = 'client_credentials', 'pipeline-00000000016', \
                                                     'ZTY0MzRkZWYtNmZjNC0xMWVhLWI5ZGUtMzA5YzIzZjMyZjFj-pipeline', 'eternal'
    client_token = get_client_token(sso_url, grant_type, client_id, client_secret, duration)
    urlprefix_path_dict = get_urlprefix_dict(service_info, listing_system_url, datacenter_code, client_token)
    somketest(urlprefix_path_dict, identity, subscriptionId, start_date, end_date,cluster_namespace,cluster_cluster,
              externaldomain,deviceon_namespace,serviceurl_str)