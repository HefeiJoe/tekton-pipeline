import warnings, json, requests, sys, datetime
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

# def get_username(sso_url, user_id):
#     try:
#         print('get username, user_id: %s' % user_id)
#         url = "{}/users/username/{}".format(sso_url, user_id)
#         response = call_restful_api(url, '', 'GET', '', 60)
#         code = response[0]
#         if code == 200:
#             res = response[1]
#             return json.loads(res)['username']
#         else:
#             print('get username failed')
#             raise Exception('get username failed')
#     except Exception as e:
#         print(e)
#         raise e

# def add_subscription_id(sso_url, client_token, user_id, subscription_id):
#     try:
#         data = {}
#         username = get_username(sso_url, user_id)
#         data['userName'] = username
#         data['subscriptionRole'] = "admin"
#         print(data)
#         print("add %s to subscriptionid %s" % (username,subscription_id))
#         url = "{}/subscriptions/{}/users".format(sso_url, subscription_id)
#         response = call_restful_api(url, json.dumps(data), 'POST', client_token, 60)
#         print(response)
#         code = response[0]
#         if code != 200 and code != 409:
#             print("add subsription role failed")
#             raise Exception('add subsription role failed')
#     except Exception as e:
#         print(e)
#         raise e

@retry(Exception, tries=3, delay=5)
def identifyuser(sso_url,subscription_id,client_token):
    try:
        print("=====identifyuser start")
        url = "{}/subscriptions/{}/accountInfo".format(sso_url,subscription_id)
        response = call_restful_api(url, '', 'GET', client_token, 60)
        print(response)
        code = response[0]
        if code == 200:
            data = json.loads(response[1])
            # member_type = data['MemberType']
            if data['Status']['isPaid']:
                return 'internal'
            else:
                if data['Status']['isPaid']:
                    return 'official'
                else:
                    return 'trial'
        else:
            raise Exception("identifyuser failed, %s" % response[1])
    except Exception as e:
        print(e)
        raise e

def check_parmas(params):
    try:
        for key, value in params.items():
            if value is None or value == '':
                raise Exception('parma %s is null' % key)
    except Exception as e:
        print(e)
        raise e

if __name__ == '__main__':
    print(sys.argv)
    sso_url = sys.argv[1]
    service_configs = sys.argv[2].replace('\(','(').replace('\)',')')
    service_config = json.loads(service_configs)
    subscription_id = service_config['subscriptionId']
    datacenter_code = sys.argv[3]
    check_parmas({'ssoUrl':sso_url,
                  'subscriptionId':subscription_id,
                  'datacenterCode':datacenter_code})
    grant_type, client_id, client_secret, duration = 'client_credentials', 'pipeline-00000000016', \
                                             'ZTY0MzRkZWYtNmZjNC0xMWVhLWI5ZGUtMzA5YzIzZjMyZjFj-pipeline', 'eternal'
    client_token = get_client_token(sso_url, grant_type, client_id, client_secret, duration)
    # add_subscription_id(sso_url, client_token, user_id, subscription_id)
    identity = identifyuser(sso_url, subscription_id, client_token)
    start_date, end_date = '', ''
    if identity == 'trial':
        start_date = datetime.datetime.now()
        end_date = (start_date + datetime.timedelta(days=30)).strftime('%m/%d/%Y')
        print(end_date)
        start_date = start_date.strftime('%m/%d/%Y')
        print(start_date)
    return_str = '%s:%s:%s:%s:%s' % (service_config['memberType'], identity,start_date,end_date,subscription_id)
    f = open('ssoinfo.txt', 'w')
    f.write(return_str)
    f.close()