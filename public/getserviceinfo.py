import json
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

def write_file(file_path, content):
    f = open(file_path, 'w')
    f.write(content)
    f.close()

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

# def get_config_id(catalog_url, config_id, client_token):
#     try:
#         print('get_config_id start!')
#         url = "%s/serviceInstance/%s" % (catalog_url, config_id)
#         print(url)
#         response = call_restful_api(url,'', "GET", client_token, 60)
#         print(response)
#         if response[0] == 200:
#             return json.loads(response[0])['configId']
#         else:
#             raise Exception(str(response))
#     except Exception as e:
#         print(e)
#         raise e

@retry(Exception, tries=3, delay=5)
def get_service_info(catalog_url, service_package_id, subscription_id, client_token):
    try:
        print('get_service_config start!')
        url = "%s/serviceInstances?subscriptionId=%s&packageId=%s" % (catalog_url, subscription_id, service_package_id)
        print(url)
        response = call_restful_api(url,'', "GET", client_token, 60)
        print(response)
        if response[0] == 200:
            return json.loads(response[1])['data']
        else:
            return []
    except Exception as e:
        print(e)
        raise e

if __name__ == "__main__":
    print(sys.argv)
    sso_url = sys.argv[1]
    catalog_url = sys.argv[2]
    service_package_id = sys.argv[3]
    subscription_id = sys.argv[4]
    grant_type, client_id, client_secret, duration = 'client_credentials', 'pipeline-00000000016', \
                                                        'ZTY0MzRkZWYtNmZjNC0xMWVhLWI5ZGUtMzA5YzIzZjMyZjFj-pipeline', 'eternal'
    client_token = get_client_token(sso_url, grant_type, client_id, client_secret, duration)
    service_config = get_service_info(catalog_url, service_package_id, subscription_id, client_token)
    write_file('./serviceInfo.json', json.dumps(service_config, indent=2))
