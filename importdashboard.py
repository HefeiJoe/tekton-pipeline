from optparse import OptionParser
import warnings, base64, json, requests, configparser, os, sys
warnings.filterwarnings('ignore')  # ignore warning
def GetBase64Auth(account, psw):
    Auth = ('%s:%s') % (account, psw)
    bytesString = Auth.encode(encoding="utf-8")
    encodestr = base64.b64encode(bytesString)
    token = "Basic %s" % encodestr.decode('ascii')
    return token
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
def CreateDataSource(grafana_url, token, datasource):
    try:
        url = "%s/api/datasources" % grafana_url
        data = json.dumps(datasource)
        method = "POST"
        response = CallRestfulAPI(url, data, method, token, 60)
        print response
        return response
    except Exception as e:
        print e
def ImportBoard(grafana_url, token, dashboard, folder_id, overwrite):
    try:
        url = "%s/api/dashboards/import" % grafana_url
        dashboard['id'] = None
        # dashboard['uid'] = None
        boaydata = {}
        boaydata['dashboard'] = dashboard
        try:
            inputs = []
            if dashboard['__inputs'] != None:
                temp = dashboard['__inputs']
                for i in range(len(temp)):
                    input_dict = temp[i]
                    inputs_dict = {}
                    inputs_dict['name'] = input_dict['name']
                    inputs_dict['pluginId'] = input_dict['pluginId']
                    inputs_dict['type'] = input_dict['type']
                    inputs_dict['value'] = input_dict['label']
                    inputs.append(inputs_dict)
                boaydata['inputs'] = inputs
            elif dashboard['__inputs'] == None:
                boaydata['inputs'] = inputs
        except Exception as e:
            print e
        boaydata['folderId'] = folder_id
        if overwrite == 'true':
            boaydata['overwrite'] = True
        elif overwrite == 'false':
            boaydata['overwrite'] = False
        data = json.dumps(boaydata)
        method = "POST"
        response = CallRestfulAPI(url, data, method, token, 60)
        print response
        return response
    except Exception as e:
        print e
def ImportSRPFrame(grafana_url, token, data):
    try:
        url = "%s/api/frame" % grafana_url
        method = "GET"
        response = CallRestfulAPI(url, '', method, token, 60)
        if response[0] != 200:
            print "Get frame failed!"
            return False
        frames = response[1]
        frame_list = json.loads(frames)
        if len(frame_list) != 0:
            for frame in frame_list:
                if frame['orgId'] == data['orgId'] and frame['srpName'] == data['srpName'] and frame['language'] == \
                        data['language']:
                    print "srpName:%s, orgId:%s, language:%s, exist!" % (
                    data['srpName'], data['orgId'], data['language'])
                    return True
        data_str = json.dumps(data)
        url = "%s/api/frame/import" % grafana_url
        method = "POST"
        response = CallRestfulAPI(url, data_str, method, token, 60)
        print response
        if response[0] == 200:
            return True
        else:
            return False
    except Exception as e:
        print e
        return False
def CreateFolder(grafana_url, token, foldername):
    try:
        folder_name = foldername.lower()
        folder_id = 0
        url = "%s/api/folders" % grafana_url
        method = "GET"
        response = CallRestfulAPI(url, '', method, token, 60)
        if response[0] == 200:
            folder_list = json.loads(response[1])
            for folder in folder_list:
                if folder_name == folder['title']:
                    folder_id = folder['id']
                    return folder_id
        else:
            print "Get folder list failed!!!"
        # if the folder doesn't exist, create folder
        if folder_id == 0:
            method = "POST"
            data = '{"title":"%s"}' % foldername
            response = CallRestfulAPI(url, data, method, token, 60)
            if response[0] == 200:
                folder_info = json.loads(response[1])
                folder_id = folder_info['id']
                return folder_id
            else:
                print "Create folder failed!!!"
        return folder_id
    except Exception as e:
        print e
        return folder_id
if __name__ == '__main__':
    srpframe_replace_count = 0
    datasource_replace_count = 0
    config = configparser.ConfigParser()
    config.read("config_1_3_0.ini")
    account = config.get("user", "account")
    psw = config.get("user", "psw")
    config_url = config.get("target", "grafana_url")
    config_file = config.get("target", "file")
    config_dir = config.get("target", "dir")
    config_type = config.get("target", "type")
    config_overwrite = config.get("target", "overwrite")
    config_datasource_replace = config.get("datasource", "replace")
    config_srpframe_replace = config.get("srpframe", "replace")
    parser = OptionParser()
    parser.add_option("-a", "--address",
                      action="store",
                      type='string',
                      dest="address",
                      default=config_url,
                      help="Please write the address of the target grafana."
                      )
    parser.add_option("-u", "--username",
                      action="store",
                      type='string',
                      dest="username",
                      default=account,
                      help="Please write your username."
                      )
    parser.add_option("-p", "--password",
                      action="store",
                      type='string',
                      dest="password",
                      default=psw,
                      help="Please write your password."
                      )
    parser.add_option("-t", "--type",
                      action="store",
                      type='string',
                      dest="type",
                      default=config_type,
                      help="Import type:dashboard or datasource?"
                      )
    parser.add_option("-f", "--file",
                      action="store",
                      type='string',
                      dest="file",
                      default=None,
                      help="Please write the path of the file."
                      )
    parser.add_option("-d", "--dir",
                      action="store",
                      type='string',
                      dest="dir",
                      default=None,
                      help="Please write the path of the dir."
                      )
    parser.add_option("-o", "--overwrite",
                      action="store",
                      type='string',
                      dest="overwrite",
                      default=config_overwrite,
                      help="Do you want to overwrite the exits dashboard ?"
                      )
    parser.add_option("-r", "--datasourcereplace",
                      action="store",
                      type='string',
                      dest="datasourcereplace",
                      default=config_datasource_replace,
                      help="Do you want to replace datasource url ?"
                      )
    parser.add_option("-e", "--srpframereplace",
                      action="store",
                      type='string',
                      dest="srpframereplace",
                      default=config_srpframe_replace,
                      help="Do you want to replace some string in srpframe ?"
                      )
    (options, args) = parser.parse_args()
    if options.address != None:
        grafana_url = options.address
    if (options.username != None) and (options.password != None):
        auth = GetBase64Auth(options.username, options.password)
    if options.datasourcereplace != "":
        config_datasource_replace_list = str.split(options.datasourcereplace, "***")
        datasource_replace_count = len(config_datasource_replace_list)
        config_datasource_replace_array = [([0] * 2) for i in range(datasource_replace_count)]
        i = 0
        for replace in config_datasource_replace_list:
            replace_list = str.split(replace, ",")
            config_datasource_replace_array[i][0] = replace_list[0]
            config_datasource_replace_array[i][1] = replace_list[1]
            i = i + 1
    if options.srpframereplace != "":
        config_srpframe_replace_list = str.split(options.srpframereplace, "***")
        srpframe_replace_count = len(config_srpframe_replace_list)
        config_srpframe_replace_array = [([0] * 2) for i in range(srpframe_replace_count)]
        i = 0
        for replace in config_srpframe_replace_list:
            replace_list = str.split(replace, ",")
            config_srpframe_replace_array[i][0] = replace_list[0]
            config_srpframe_replace_array[i][1] = replace_list[1]
            i = i + 1
    if options.file == None and options.dir == None:
        options.file = config_file
        options.dir = config_dir
    if options.file != None and options.file != '':
        if not os.path.exists(options.file):
            print "%s doesn't exists!!!" % options.file
            sys.exit()
        filename = os.path.basename(options.file)
        with open(options.file, 'r') as f:
            try:
                if (options.type != None) and (options.type == 'datasource'):
                    datasource = json.loads(f.read())
                    print datasource
                    if datasource_replace_count != 0:
                        for i in range(0, datasource_replace_count):
                            if config_datasource_replace_array[i][0] == filename:
                                datasource["url"] = config_datasource_replace_array[i][1]
                    CreateDataSource(grafana_url, auth, datasource)
                elif (options.type != None) and (options.type == 'dashboard'):
                    dashboard = json.loads(f.read())
                    ImportBoard(grafana_url, auth, dashboard, 0, options.overwrite)
                elif (options.type != None) and (options.type == 'srpframe'):
                    # srpframe = json.loads(f.read())
                    srpframe_data = f.read()
                    if srpframe_replace_count != 0:
                        for i in range(0, srpframe_replace_count):
                            srpframe_data = srpframe_data.replace(config_srpframe_replace_array[i][0],
                                                                  config_srpframe_replace_array[i][1])
                    srpframe_data_json = json.loads(srpframe_data)
                    ImportSRPFrame(grafana_url, auth, srpframe_data_json)
            except Exception as e:
                print e
    if options.dir != None and options.dir != '':
        if not os.path.exists(options.dir):
            print "%s doesn't exists!!!" % options.dir
            sys.exit()
        files = os.listdir(options.dir)
        for file in files:
            filepath = os.path.join(options.dir, file)
            if os.path.isfile(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        if (options.type != None) and (options.type == 'datasource'):
                            datasource = json.loads(f.read())
                            if datasource_replace_count != 0:
                                for i in range(0, datasource_replace_count):
                                    if config_datasource_replace_array[i][0] == file:
                                        datasource["url"] = config_datasource_replace_array[i][1]
                            CreateDataSource(grafana_url, auth, datasource)
                        elif (options.type != None) and (options.type == 'dashboard'):
                            dashboard = json.loads(f.read())
                            ImportBoard(grafana_url, auth, dashboard, 0, options.overwrite)
                    except Exception as e:
                        print e
            elif os.path.isdir(filepath):
                if (options.type != None) and (options.type == 'dashboard'):
                    folder_id = CreateFolder(grafana_url, auth, file)
                    if folder_id != 0:
                        print "%s:%s" % (file, folder_id)
                        for child_root, child_dirs, child_files in os.walk(filepath, followlinks=False):
                            for child_file in child_files:
                                child_filepath = os.path.join(child_root, child_file)
                                with open(child_filepath, 'r', encoding='utf-8') as f:
                                    dashboard = json.loads(f.read())
                                    ImportBoard(grafana_url, auth, dashboard, folder_id, options.overwrite)
                elif (options.type != None) and (options.type == 'srpframe'):
                    for child_root, child_dirs, child_files in os.walk(filepath, followlinks=False):
                        for child_file in child_files:
                            child_filepath = os.path.join(child_root, child_file)
                            with open(child_filepath, 'r', encoding='utf-8') as f:
                                srpframe = json.loads(f.read())
                                if srpframe["srpName"] != file:
                                    srpframe["srpName"] = file
                                srpframe_data = json.dumps(srpframe)
                                if srpframe_replace_count != 0:
                                    for i in range(0, srpframe_replace_count):
                                        srpframe_data = srpframe_data.replace(config_srpframe_replace_array[i][0],
                                                                              config_srpframe_replace_array[i][1])
                                srpframe_data_json = json.loads(srpframe_data)
                                ImportSRPFrame(grafana_url, auth, srpframe_data_json)
                else:
                    pass
            else:
                print "%s is a special file" % file