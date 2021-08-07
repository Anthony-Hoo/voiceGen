from flask import Flask, request, jsonify, render_template, url_for, redirect
import pymongo



app = Flask(__name__)
app.config.from_object("config")
app.secret_key = '1234567'

client = pymongo.MongoClient("127.0.0.1", 27017)
db = client["voicehash"]
hashSet = db["hashset"]

# 服务器url
url = "https://res.imirai.xyz/voice/"

def popMongoID(mongoJSON):
    resultJSON = [s.copy() for s in mongoJSON]
    for r in resultJSON:
        r.pop("_id")
    return resultJSON

@app.route('/voice')
def giveBackURL():
    if(request.method == "GET"):
        mongoJSON = hashSet.aggregate([{ '$sample': { 'size': 1 } }])
        result = popMongoID(mongoJSON)
        # print(result[0])
        url_to_voice = url + result[0]["voiceHash"]
        return url_to_voice



if __name__ == '__main__':
    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run(host="127.0.0.1",
            port=8000)