import json
import sys
import requests
import logging

def validation(ssoUsername,sso_password,sso_token):
    if sso_token == '0' and (ssoUsername == '0' or sso_password == '0'):
        logging.error('Permission check failed!')

def get_service(service_info):
    service_info_list = service_info.split(':')
    main_service_name = service_info_list[0]
    main_service_plan_name = service_info_list[1]
    main_service_chart_version = ''
    main_service_secret_name = ''
    length = len(service_info_list)
    if length == 3:
        main_service_secret_name = service_info_list[2]
    if length == 4:
        main_service_chart_version = service_info_list[3]
    return main_service_name,main_service_plan_name,main_service_chart_version,main_service_secret_name

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


def parseConfig(sso_token,getdeploymenturl):
    deployment = get_app_info(sso_token,getdeploymenturl)
    # print(deployment)
    data = deployment['data'][0]
    print(data)

    apps = data['apps']
    map = {}
    for i in range(len(apps)):
        map["app%d" % i] = {}
        if isinstance(apps[i], dict):
            dt = apps[i]
            for key in dt:
                if isinstance(dt[key], dict):
                    dm = dt[key]
                    for key in dm:
                        if isinstance(dm[key], dict):
                            df = dm[key]
                            for key in df:
                                map["app%d" % i][key] = df[key]
                        else:
                            map["app%d" % i][key] = dm[key]

                else:
                    map["app%d" % i][key] = dt[key]

    map['param'] = {}
    map['param']['appNums'] = len(apps)
    map['param']['version'] = data['chartVersion']
    map['urlprefix'] = {}
    t = data['extraParam']['urlPrefix']
    str = ""
    for i in range(len(t)):
        if i == len(t) - 1:
            str = str + t[i]
        else:
            str = str + t[i] + ","
    map['urlprefix'] = str
    # map['appServiceLength'] = len(app_services)
    map['param']['srp_name'] = data['serviceName']
    map['param']['plan_name'] = data['planName']
    map['param']['chartname'] = data['chartName']
    map['param']['memory'] = data['memory']
    map['param']['cpu'] = data['cpu']
    map['param']['ephemeralStorage'] = data['ephemeralStorage']
    map['values'] = data['values']
    app_services = []
    appServicesDependency = data['appServicesDependency']
    for i in range(len(appServicesDependency) - 1):
        app_services[i] = appServicesDependency[i]['serviceName'] + '-' + appServicesDependency[i]['chartVersion']
    map['appServicesDependency'] = app_services
    write_file("./values.yaml",data['values'].replace('\"', '"'))
    return map

def get_app_info(sso_token,getdeploymenturl):
	headers = {}
	headers.setdefault('Authorization', sso_token)
	response = requests.get(getdeploymenturl, headers=headers)
	return response.json()

def get_external_domain(route_url, internal_domain):
    url = "/domain/{}/external".format(internal_domain)
    url = route_url + url
    print(url)
    response = requests.get(url)
    res = response.json()['data']
    return res

def CallRestfulAPI(url, data, method, auth, timeout, content_type="application/json"):
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

def get_kubeconfig(mp_url, token, datacentercode,cluster):
    datacenterCode = datacentercode
    Cluster = cluster
    url = "/datacenter/{}/cluster/{}/config?type=string".format(datacenterCode,Cluster)
    url = mp_url + url
    method = "GET"
    response = CallRestfulAPI(url,"",method,token, 60)
    res = response[1]
    return res

def write_file(file_path, content):
    f = open(file_path, 'w')
    f.write(content)
    f.close()

def get_urls(listingsystem_url,datacenter_code):
    listingsystemurl = "%s/datacenter?datacenterCode=%s" % (listingsystem_url, datacenter_code)
    response = requests.get(listingsystemurl)
    datacenterUrls = response.json()
    urls = datacenterUrls["data"][0]["datacenterUrl"]
    sso_internal_url = urls['api-sso']['internalUrl']
    ssourl = urls['api-sso']['externalUrl']
    mg_internal_url = urls['api-mg']['internalUrl']
    mg_url = urls['api-mg']['externalUrl']
    dccs_internal_url = urls['api-dccs']['internalUrl']
    dccs_url = urls['api-dccs']['externalUrl']
    license_internal_url = urls['api-license']['internalUrl']
    license_url = urls['api-license']['externalUrl']
    service_internal_url = urls['api-service']['internalUrl']
    service_url = urls['api-service']['externalUrl']
    ensaas_datacentercode = urls['ensaas']['datacenterCode']
    ensaas_internal_url = urls['ensaas']['internalUrl']
    ensaas_url = urls['ensaas']['externalUrl']
    mp_url = urls['api-mp']['externalUrl']
    route_url = urls['api-router']['externalUrl']
    return sso_internal_url,ssourl,mg_internal_url,mg_url,dccs_internal_url,dccs_url,license_internal_url,\
           license_url,service_internal_url,service_url,ensaas_datacentercode,ensaas_internal_url,ensaas_url,\
           mp_url,route_url

if __name__ == '__main__':
    service_info = sys.argv[1]
    datacenter_code = sys.argv[2]
    cluster = sys.argv[3]
    namespace = sys.argv[4]
    internal_domain = sys.argv[5]
    external_domain = sys.argv[6]
    sso_username = sys.argv[7]
    sso_password = sys.argv[8]
    sso_token = sys.argv[9]
    listingsystem_internal_url = sys.argv[10]
    listingsystem_url = sys.argv[11]
    appdepency_sevice = sys.argv[12]
    # workspace_id = sys.argv[4]
    # repo = sys.argv[8]
    # image_username = sys.argv[10]
    # image_password = sys.argv[11]
    # harbor_username = sys.argv[12]
    # harbor_password = sys.argv[13]
    #get main servicename/planname/secretname
    main_service_name, main_service_plan_name, main_service_chart_version, main_service_secret_name =\
        get_service(service_info)
    #get urls
    sso_internal_url, ssourl, mg_internal_url, mg_url, dccs_internal_url, dccs_url, license_internal_url, \
    license_url, service_internal_url, service_url, ensaas_datacentercode, ensaas_internal_url, ensaas_url, \
    mp_url, route_url = get_urls(listingsystem_url,datacenter_code)
    if sso_token == '0':
        sso_token = login(ssourl, sso_username, sso_password)
    else:
        sso_token = 'Bearer '+ sso_token
    getdeploymenturl = '%s/deployment/%s/plan/%s?chartVersion=%s' % (listingsystem_url,main_service_name,
                                main_service_plan_name,main_service_chart_version)
    logging.info('getdeploymenturl: '+getdeploymenturl)
    print getdeploymenturl
    apps = parseConfig(sso_token, getdeploymenturl)
    # get hosts
    hosts = ".%s.%s" % (namespace, internal_domain)
    chart_name = apps['param']['chartname']
    chart_version = apps['param']['version']
    if external_domain == '0':
        external_domain = get_external_domain(route_url, internal_domain)
    service_name = main_service_name.lower()
    release_name = '%s-%s' % (service_name, namespace)
    appdepency_sevice_info_list = []
    if appdepency_sevice != '0':
        appdepency_sevice_info_list = appdepency_sevice.split(',')
    app_service_name_list = []
    for app_service_info in appdepency_sevice_info_list:
        app_service =app_service_info.split(':')
        app_service_name =app_service[0]
        app_service_name_list.append(app_service_name)
    return_map = {}
    return_map.setdefault('chart_name',chart_name)
    return_map.setdefault('chart_version', chart_version)
    return_map.setdefault('main_service_secret_name', main_service_secret_name)
    return_map.setdefault('hosts',hosts)
    return_map.setdefault('sso_internal_url', sso_internal_url)
    return_map.setdefault('ssourl', ssourl)
    return_map.setdefault('mg_internal_url', mg_internal_url)
    return_map.setdefault('mg_url', mg_url)
    return_map.setdefault('dccs_internal_url', dccs_internal_url)
    return_map.setdefault('dccs_url', dccs_url)
    return_map.setdefault('license_internal_url', license_internal_url)
    return_map.setdefault('license_url', license_url)
    return_map.setdefault('listingsystem_internal_url', listingsystem_internal_url)
    return_map.setdefault('listingsystem_url', listingsystem_url)
    return_map.setdefault('service_internal_url', service_internal_url)
    return_map.setdefault('service_url', service_url)
    return_map.setdefault('ensaas_datacentercode', ensaas_datacentercode)
    return_map.setdefault('ensaas_internal_url', ensaas_internal_url)
    return_map.setdefault('ensaas_url', ensaas_url)
    kubeconfig = get_kubeconfig(mp_url, sso_token, datacenter_code,cluster)
    write_file('/tekton/home/getparams/params.json', json.dumps(return_map, indent=2))
    write_file('/tekton/home/getparams/values.yaml', apps['values'].replace('\"','"'))
    write_file('/tekton/home/getparams/kubeconfig', kubeconfig)
