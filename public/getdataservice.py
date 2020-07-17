import json
import sys


def get_data_services(path):
    try:
        f = open(path, 'r', encoding='utf-8')
        lines = f.read()
        f.close()
        data_serviceinfo_map, data_serviceinfo_list = {}, []
        data_service_str = lines.split('###')
        print(data_service_str)
        for data_service in data_service_str:
            data_service = data_service.replace('\n', '').strip()
            if '' != data_service:
                data_serviceinfo = json.loads(data_service)['dataServiceinfo'][0]
                data_serviceinfo_list.append(data_serviceinfo)
        data_serviceinfo_map.setdefault('dataServiceinfo', data_serviceinfo_list)

        n = open('dataService.json', 'w', encoding='utf-8')
        n.write(json.dumps(data_serviceinfo_map, indent=4))
        n.close()
    except Exception as e:
        print(e)


if __name__ == '__main__':
    path = sys.argv[1]
    get_data_services(path)