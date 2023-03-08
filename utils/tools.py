import requests

def upload_file(url, file_path):
    with open(file_path, 'rb') as f:
        file = {'file': f}
        response = requests.post(url, files=file)
        if response.json()['ok'] == True:
            return response.json()['path']
        else:
            return None
