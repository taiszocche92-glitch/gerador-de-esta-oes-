import os
from dotenv import load_dotenv
from urllib import request, parse
import json

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

KEY_SLOTS = ['GEMINI_API_KEY_4', 'GEMINI_API_KEY_1', 'GEMINI_API_KEY_2', 'GEMINI_API_KEY_3']
base_url = 'https://generativelanguage.googleapis.com/v1/models'

for slot in KEY_SLOTS:
    key = os.getenv(slot)
    print(f'\n---\nSlot: {slot} -> {repr(key)}')
    if not key:
        print('  no key')
        continue
    key = key.strip()
    url = base_url + '?key=' + parse.quote(key)
    print('  Testing URL:', url)
    try:
        req = request.Request(url, method='GET')
        with request.urlopen(req, timeout=15) as resp:
            status = resp.getcode()
            body = resp.read().decode('utf-8', errors='replace')
            print('   status:', status)
            models = json.loads(body).get('models', [])
            print(f'   {len(models)} modelos encontrados:')
            for m in models:
                print('    -', m.get('name'), '|', m.get('displayName'))
    except Exception as e:
        print('   error:', repr(e))
print('\nDone')
