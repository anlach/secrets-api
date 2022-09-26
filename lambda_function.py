import boto3
import json
import base64
import subprocess
import urllib.parse

print('Loading function')
dynamo = boto3.resource('dynamodb')
table = dynamo.Table('secrets-db')


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': json.dumps(str(err)) if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def encrypt(message, key):
    encrypt_proc = subprocess.Popen(
        ['gpg', '-v', '--no-options', '--batch', '--passphrase', key, '-c', '-'], 
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    encrypted = encrypt_proc.communicate(input=message.encode())
    return encrypted
    

def decrypt(message, key):
    decrypt_proc = subprocess.Popen(
        ['gpg','--no-options', '--batch', '--passphrase', key, '-d', '-'], 
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    decrypted = decrypt_proc.communicate(input=message.value)[0]
    return decrypted.decode()


def get_index():
    page = open('index.html').read()
    return {
        'statusCode': '200',
        'body': page,
        'headers': {
            'Content-Type': 'text/html',
        },
    }


def get_message(event):
    if 'queryStringParameters' not in event:
        return respond(ValueError("No key in query string for decryption"))
    params = event['queryStringParameters']
    if "key" not in params:
        return respond(ValueError("No key in query string for decryption"))
        
    dbid = event['pathParameters']['message-id']
    res = table.get_item(
        Key={
            "id": dbid
        }
    )
    if "Item" not in res:
        return respond(ValueError(f"No message stored with id '{dbid}'"))

    decrypted = decrypt(res["Item"]["message"], params["key"])
    status = '200'
    if decrypted == "":
        decrypted = "Failed to decrypt! Check key in URL"
        status = '400'
    return {
        'statusCode': status,
        'body': json.dumps(decrypted),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def post_message(event):
    print(event)
    
    if 'body' not in event:
        return respond(ValueError("No body in post - must include message"))
        
    print(event['body'])
    ct = event['headers']['content-type']
    if ct != 'application/x-www-form-urlencoded' and ct != 'application/json':
        return respond(ValueError("POST body must be json or x-www-form-urlencoded"))
    
    if (event['isBase64Encoded']):
        body = base64.b64decode(event['body']).decode()
    else:
        body = event['body']
    
    if ct == 'application/x-www-form-urlencoded':
        body = urllib.parse.parse_qs(body);
        message = body["message"][0]
    else:
        body = json.loads(body)
        message = body["message"]
        
    if "message" not in body:
        return respond(ValueError('No "message" key in POST body'))
    
    
    if 'queryStringParameters' not in event:
        return respond(ValueError("No key in query string for encryption"))
    params = event['queryStringParameters']
    if "key" not in params:
        return respond(ValueError("No key in query string for encryption"))
    key = params['key']
        
    dbid = event['pathParameters']['message-id']
    
    encrypted=encrypt(message, key)
    print("gpg stderr", encrypted[1])
    item = {
        "id": dbid,
        "message": encrypted[0]
    }
    res = table.put_item(
        Item=item
    )

    print("table put response", res)
    page = open('url.html').read()
    page = page.format(
        gpg=encrypted[1].split(b'\n')[3].decode(),
        encrypted=base64.b64encode(encrypted[0]).decode(),
        url=f"?key={key}")
    return {
        'statusCode': '200',
        'body': page,
        'headers': {
            'Content-Type': 'text/html',
        },
    }


def get_style():
    style = open('style.css').read()
    return {
        'statusCode': '200',
        'body': style,
        'headers': {
            'Content-Type': 'text/css',
        },
    }


def lambda_handler(event, context):
    '''
    '''
    print("Processing", event['routeKey'])
    
    if event['routeKey'] == 'GET /':
        return get_index()
    if event['routeKey'] == 'GET /style.css':
        return get_style()
    if event['routeKey'] == 'GET /message/{message-id}':
        return get_message(event)
    elif event['routeKey'] == 'POST /message/{message-id}':
        return post_message(event)
    else:
        return respond(ValueError(
            'Unsupported method "{}"'.format(event['routeKey'])))

