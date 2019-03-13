import ldap
from uuid import UUID
import base64
import json
import requests
import re
from datetime import datetime
import config

# cfg = config.TestConfig
cfg = config.ProductionConfig

API_KEY = cfg.API_KEY
VCARD_SERVER = cfg.VCARD_SERVER
LDAP_PROVIDER_URL = cfg.LDAP_PROVIDER_URL
LDAP_BIND_DN = cfg.LDAP_BIND_DN
LDAP_BIND_PW = cfg.LDAP_BIND_PW
LDAP_BASE_DN = cfg.LDAP_BASE_DN
DEFAULT_ATTRS = cfg.DEFAULT_ATTRS

SYNC_URL = cfg.VCARD_SERVER + '/api/v1.0/sync/{}'
VCARDS_URL = cfg.VCARD_SERVER + '/api/v1.0/vcards/{}'

LDAP_RETRIEVE_ATTRIBUTES = ["sn", "givenName", "displayName", "telephoneNumber", "mobile", "mail",
                            "objectGUID", "title", "department", "company"]
LDAP_SEARCH_FILTER = u'(&(objectClass=user)(objectClass=top)(objectClass=person))'
LDAP_PROTOCOL_VERSION = 3

token = "my token"
headers = {'Authorization': 'Bearer ' + token, "Content-Type": "application/json", 'x-api-key': cfg.API_KEY}

"""
N: LASTNAME; FIRSTNAME; ADDITIONAL NAME; NAME PREFIX(Mr.,Mrs.); NAME SUFFIX
ADR;TYPE=home:;;123 Main St.;Springfield;IL;12345;USA
ORG:Google;GMail Team;Spam Detection Squad
PHOTO;TYPE=JPEG;ENCODING=b:[base64-data]
ROLE:Executive
TITLE:V.P. Research and Development
ADR;TYPE=home:;;123 Main St.;Springfield;IL;12345;USA
LOGO;TYPE=PNG;ENCODING=b:[base64-data]

#    "PHOTO;ENCODING=BASE64;TYPE=JPEG": {"template": "%s", "fields": ['thumbnailPhoto']},
"""

field_map = {
    "FN;CHARSET=UTF-8":     {"template": "%s",   "fields": ['displayName']},
    "N;CHARSET=UTF-8":      {"template": "%s;%s;;;",   "fields": ['sn', 'givenName']},
    "TEL;WORK;VOICE":       {"template": "%s",      "fields": ['telephoneNumber']},
    "TEL;CELL;VOICE":       {"template": "%s",      "fields": ['mobile']},
    "TITLE;CHARSET=UTF-8":  {"template": "%s",      "fields": ['title']},
    "EMAIL;TYPE=work":      {"template": "%s",      "fields": ['mail']},
    "ORG": {"template": "%s;%s", "fields": ['company', 'department']}
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

    con = ldap.initialize(LDAP_PROVIDER_URL, bytes_mode=False)
    con.simple_bind_s(LDAP_BIND_DN, LDAP_BIND_PW)
    results = con.search_s(LDAP_BASE_DN, ldap.SCOPE_SUBTREE, LDAP_SEARCH_FILTER, LDAP_RETRIEVE_ATTRIBUTES)

    updated_count = 0
    new_count = 0
    for result in results:
        if is_attr(result[1], ["objectGUID"]):
            uid = get_attr(result[1], "objectGUID")
            rest_data = {'REV': datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
            for attr in DEFAULT_ATTRS:
                field, val = attr.split(':')
                rest_data[field] = val
            for field in field_map:
                if is_attr(result[1], field_map[field]["fields"]):
                    rest_data[field] = field_map[field]["template"] % (get_attrs(result[1], field_map[field]["fields"]))
            # print(rest_data)
            # response = requests.delete(VCARDS_URL.format(uid), headers=headers)
            # r.raise_for_status()
            response = requests.put(SYNC_URL.format(uid), json=rest_data, headers=headers)
            resp = json.loads(response.text)
            new_count += int(resp[str(uid)]['new'])
            updated_count += int(resp[str(uid)]['updated'])
            print('{} {}: [u:{},n:{}]'.format(uid, get_attrs(result[1], ['displayName'])[0], resp[str(uid)]['updated'],
                                              resp[str(uid)]['new']))
    print('New: {} Updated: {}'.format(new_count, updated_count))
