import ldap
from uuid import UUID
import base64
import json
import requests
import re

import config

cfg = config.TestConfig

VCARD_SERVER_URL = cfg.VCARD_SERVER + '/api/v1.0/sync/{}'

token = "my token"
headers = {'Authorization': 'Bearer ' + token, "Content-Type": "application/json", 'x-api-key': cfg.API_KEY}

field_map = {
    "FN;CHARSET=UTF-8":     {"template": "%s %s",   "fields": ['givenName', 'sn']},
    "N;CHARSET=UTF-8":      {"template": "%s;%s",   "fields": ['sn', 'givenName']},
    "TEL;WORK;VOICE":       {"template": "%s",      "fields": ['telephoneNumber']},
    "TEL;CELL;VOICE":       {"template": "%s",      "fields": ['mobile']},
    "TITLE;CHARSET=UTF-8":  {"template": "%s",      "fields": ['displayName']},
    "EMAIL;TYPE=work":      {"template": "%s",      "fields": ['mail']},
    "PHOTO;ENCODING=BASE64;TYPE=JPEG": {"template": "%s", "fields": ['thumbnailPhoto']}
}


def format_phone(data):
    return re.sub(r'[ .-]', '', data.decode('utf-8', 'ignore'))


def get_attr(data, attr_name):
    if attr_name in data:
        if attr_name == 'objectGUID':
            return UUID(bytes=data[attr_name][0])
        if attr_name == 'mobile':
            return format_phone(data[attr_name][0])
        if attr_name == 'telephoneNumber':
            return format_phone(data[attr_name][0])
        elif attr_name == 'thumbnailPhoto':
            return base64.b64encode(data[attr_name][0])
        return data[attr_name][0].decode('utf-8', 'ignore')
    return ""


def get_attrs(data, attr_names):
    values = ()
    for attr_name in attr_names:
        values += (get_attr(data, attr_name),)
    return values


def is_attr(data, attr_names):
    for attr_name in attr_names:
        if attr_name in data:
            return True
    return False


if __name__ == '__main__':

    con = ldap.initialize(cfg.LDAP_PROVIDER_URL, bytes_mode=False)
    con.simple_bind_s(cfg.LDAP_BIND_DN, cfg.LDAP_BIND_PW)
    results = con.search_s(cfg.LDAP_BASE_DN, ldap.SCOPE_SUBTREE, cfg.LDAP_SEARCH_FILTER, cfg.LDAP_RETRIEVE_ATTRIBUTES)

    for result in results:
        if is_attr(result[1], ["objectGUID"]):
            uid = get_attr(result[1], "objectGUID")
            rest_data = {}
            print(uid, get_attrs(result[1], ['sn', 'givenName']))
            for field in field_map:
                if is_attr(result[1], field_map[field]["fields"]):
                    rest_data[field] = field_map[field]["template"] % (get_attrs(result[1], field_map[field]["fields"]))
            response = requests.put(VCARD_SERVER_URL.format(uid), data=json.dumps(rest_data), headers=headers)
            print(response.text)
            resp = json.loads(response.text)
            if resp[str(uid)]['new'] > 0:
                print(uid, 'new', resp[str(uid)]['new'])
            if resp[str(uid)]['updated'] > 0:
                print(uid, 'updated', resp[str(uid)]['updated'])
            # print(resp[str(uid)]['updated'])
