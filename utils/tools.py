import re
import requests

def upload_file(url, file_path):
    with open(file_path, 'rb') as f:
        file = {'file': f}
        response = requests.post(url, files=file)
        if response.json()['ok'] == True:
            return response.json()['path']
        else:
            return None

def remove_spaces_between_chinese_characters(text: str) -> str:
    pattern = re.compile(r'([\u4e00-\u9fa5])\s+')
    while pattern.search(text):
        text = pattern.sub(r'\1', text)
    return text