import requests

TEST_UID0 = '00000000-0000-0000-0000-000000000000'
TEST_UID1 = '00000000-0000-0000-0000-000000000001'
API_KEY = '1234567890'

if __name__ == '__main__':
    data = {
        'N': 'Gump;Forrest;;Mr.;',
        'FN': 'Forrest Gump',
        'ORG': 'Bubba Gump Shrimp Co.',
        'TITLE': 'Shrimp Man'
    }
    headers = {'x-api-key': API_KEY}
    r = requests.put('http://localhost:8082/api/v1.0/vcards/%s' % TEST_UID0, json=data, headers=headers)
    r.raise_for_status()
    r = requests.delete('http://localhost:8082/api/v1.0/vcards/%s' % TEST_UID1, headers=headers)
    r.raise_for_status()
