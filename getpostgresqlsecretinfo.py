import base64, json, sys
def parseConfig(secretinfofile,postgresinfofile):
    map = {}
    with open(secretinfofile,'r') as f:
        secretinfo = json.load(f)
        data = secretinfo['data']['ENSAAS_SERVICES']
        dbinfo = base64.b64decode(data).decode("ascii")
        dbinfo = json.loads(dbinfo)
        postgresqlinfo=dbinfo['postgresql'][0]
        map['database'] = postgresqlinfo['credentials']['database']
        map['host'] = postgresqlinfo['credentials']['host']
        map['password'] = postgresqlinfo['credentials']['password']
        map['port'] = postgresqlinfo['credentials']['port']
        map['uri'] = postgresqlinfo['credentials']['uri']
        map['username'] = postgresqlinfo['credentials']['username']
    with open(postgresinfofile,'r') as f:
        postgresinfo = json.load(f)
        postgresinfo['database'] = map['database']
        postgresinfo['user'] = map['username']
        postgresinfo['password'] = map['password']
        postgresinfo.secureJsonData['password'] = map['password']
        postgresinfo['url'] = map['host']
        print postgresinfo
        f = open(postgresinfofile, 'w')
        f.write(json.dumps(postgresinfo, indent=2))
        f.close()

if __name__ == '__main__':
    parseConfig(sys.argv[1], sys.argv[2])
