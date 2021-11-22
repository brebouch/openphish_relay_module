import argparse
import subprocess
import http.client
import base64
import json
import string
import secrets
import ssl

parser = argparse.ArgumentParser(description='SecureX Relay Deployment Tool.', prog='SecureX Relay Deployer')
parser.add_argument('o', help='Operation to be performed, can be "deploy or remove"')
parser.add_argument('u', help='Url')
parser.add_argument('-x', help='SecureX Region US, EU, APJC. Example: "-i US"')
parser.add_argument('-i', help='SecureX API Client ID. Example: "-i client_......"')
parser.add_argument('-s', help='SecureX API Client Secret')

module_name = 'OpenPhish'
base_url = 'visibility.amp.cisco.com'


def get_module(url, sec):
    with open('module_type.json', 'r') as module_file:
        module = json.loads(module_file.read())
        module['properties']['url'] = url
        module['properties']['configuration-token-key'] = sec
        return module


def get_region(r):
    if r.lower() == 'us':
        return '86aad484-6344-42df-922d-916b9947ec47'
    elif r.lower() == 'eu':
        return 'a80c5f4a-74cc-4f4a-8934-571bee72acb5'
    elif r.lower() == 'apjc':
        return 'bab9277c-221f-49f9-a56e-b62641ae348a'


def get_token(i, s):
    b64 = base64.b64encode((i + ':' + s).encode()).decode()
    payload = 'grant_type=client_credentials'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + b64
    }
    data = rest_call(method='POST', body=payload, headers=headers, uri='/iroh/oauth2/token', responses=[200])
    if data:
        print('Obtained SecureX Auth Token')
        return data['access_token']
    print('Issue Generating Token, Please Check Configuration and Try Again  \n')


def get_headers(token):
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + token
    }


def rest_call(**kwargs):
    conn = http.client.HTTPSConnection(base_url, context=ssl._create_unverified_context())
    headers = kwargs['headers']
    conn.request(kwargs['method'], kwargs['uri'], kwargs['body'], headers)
    res = conn.getresponse()
    data = res.read()
    for r in kwargs['responses']:
        if res.status == r:
            if data:
                return json.loads(data.decode("utf-8"))
            else:
                return res.status


def post_module(module, token):
    response = rest_call(method='POST', body=json.dumps(module), headers=get_headers(token),
                         uri='/iroh/iroh-int/module-type', responses=[201])
    if response:
        print('SecureX Integration Module Created  \n')
        return response
    print('Issue Deploying Module, Please Check Configuration and Try Again  \n')


def post_module_config(module, token):
    response = rest_call(method='POST', body=json.dumps(module), headers=get_headers(token),
                         uri='/iroh/iroh-int/module-instance', responses=[201])
    if response:
        print('SecureX Integration Module Configured  \n')
        return response
    print('Issue Deploying Module Config, Please Configure Manually Using The Following Configuration Output:  \n')


def get_module_types(token):
    return rest_call(method='GET', body={}, headers=get_headers(token), uri='/iroh/iroh-int/module-type',
                     responses=[200])


def get_module_configs(mod, token):
    return rest_call(method='GET', body={}, headers=get_headers(token),
                     uri='/iroh/iroh-int/module-instance?module_type_id=' + mod, responses=[200])


def delete_module_config(module, token):
    response = rest_call(method='DELETE', body={}, headers=get_headers(token),
                         uri='/iroh/iroh-int/module-instance/' + module, responses=[204, 404])
    if response:
        print('SecureX Integration Module Instance Deleted \n')
        return response
    print('Issue Deleting Module Config, Please Remove Manually\n')


def delete_module(module, token):
    response = rest_call(method='DELETE', body={}, headers=get_headers(token),
                         uri='/iroh/iroh-int/module-type/' + module, responses=[204, 404])
    if response:
        print('SecureX Integration Module Deleted \n')
        return response
    print('Issue Deleting Module, Please Remove Manually\n')


def get_mod_id(token):
    mod = get_module_types(token)
    for m in mod:
        if m['default_name'] == module_name:
            return m['id']


def delete_mod_and_configs(token):
    mod_type_id = get_mod_id(token)
    if mod_type_id:
        mod_config = get_module_configs(mod_type_id, token)
        for config in mod_config:
            delete_module_config(config['id'], token)
        return delete_module(mod_type_id, token)


def configure_module(mod_id):
    try:
        with open('module_config.json', 'r') as cfg_reader:
            cfg = json.loads(cfg_reader.read())
        cfg['name'] = 'OpenPhish'
        cfg['module_type_id'] = mod_id
        return cfg
    except Exception as e:
        print(e)
        return


def generate_secret_key():
    """Generate a random 256-bit (i.e. 64-character) secret key."""
    alphabet = string.ascii_letters + string.digits
    print('Encryption Secret Generated')
    return ''.join(secrets.choice(alphabet) for _ in range(64))


def check_operation(o):
    if o.lower() == 'deploy' or o.lower() == 'update' or o.lower() == 'remove':
        return o.lower()


def run_app():
    import app_5
    app_5.app.run(host='0.0.0.0', port=4000)


def kill_app():
    result = subprocess.run(['lsof', '-i', '-P'], stdout=subprocess.PIPE)
    results = result.stdout.decode('utf-8').split('\n')
    for r in results:
        if '4000' in r and 'Python' in r:
            split = r.split(' ')
            for s in split:
                try:
                    int(s)
                    subprocess.run(['kill', s], stdout=subprocess.PIPE)
                    break
                except TypeError:
                    continue
                except ValueError:
                    continue


def main():
    args = vars(parser.parse_args())
    op = check_operation(args['o'])
    url = args['u']
    securex_region = get_region(args['x'])
    subprocess.run(['pip', 'install', '-r', 'requirements.txt'], stdout=subprocess.PIPE)
    token = get_token(args['i'], args['s'])
    if not securex_region:
        print('Unknown value for region, must be US, EU, or APJC')
        return
    if op == 'deploy':
        encrypt_sec = generate_secret_key()
        if get_mod_id(token):
            delete_mod_and_configs(token)
        module_config = get_module(url, encrypt_sec)
        if module_config:
            data = post_module(module_config, token)
            cfg = configure_module(data['id'])
            post_module_config(cfg, token)
        try:
            run_app()
        except OSError:
            print('Background process still running, terminating it now')
            kill_app()
            run_app()
    if op == 'remove':
        delete_mod_and_configs(token)
        kill_app()


if __name__ == '__main__':
    main()
