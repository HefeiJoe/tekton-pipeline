from optparse import OptionParser
import warnings, base64, json, requests, configparser, os, sys
from retry import retry
warnings.filterwarnings('ignore')  # ignore warning

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
def get_kube_config(mp_url,client_token,datacenter_code,cluster):
    try:
        url = "{}/datacenter/{}/cluster/{}/config?type=string".format(mp_url, datacenter_code,cluster)
        print(url)
        response = call_restful_api(url,'','GET',client_token, 60)
        print(response)
        if response[0] != 200:
            raise Exception(response[1])
        file_object = open("./kubeconfig.txt", 'w')
        file_object.write(response[1])
        file_object.close()
    except Exception as e:
        print(e)
        raise e
if __name__ == '__main__':
    datacenter_code = sys.argv[1]
    cluster = sys.argv[2]
    sso_url = sys.argv[3]
    mp_url = sys.argv[4]
    grant_type, client_id, client_secret, duration = 'client_credentials', 'pipeline-00000000016', \
                                                    'ZTY0MzRkZWYtNmZjNC0xMWVhLWI5ZGUtMzA5YzIzZjMyZjFj-pipeline', 'eternal'
    client_token = get_client_token(sso_url, grant_type, client_id, client_secret, duration)
    get_kube_config(mp_url,client_token,datacenter_code,cluster)