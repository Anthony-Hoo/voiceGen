from flask import Flask, request, jsonify, render_template, url_for, redirect


app = Flask(__name__)
app.config.from_object("config")
app.secret_key = '1234567'







@app.route('/getVoice')
def giveBackURL():
    if(request.method == "GET"):
        # 从./db/character.db中随机取出一条数据，以json返回
        import sqlite3
        conn = sqlite3.connect('./db/character.db')
        c = conn.cursor()
        c.execute("SELECT * FROM character WHERE id >= (ABS(RANDOM()) % (SELECT MAX(rowid) FROM character)) LIMIT 1;")
        result = c.fetchone()
        conn.close()
        # 生成返回的json
        return jsonify({
            'character': result[1],
            'topic': result[2],
            'text': result[3],
            'audio': result[4],
        })




if __name__ == '__main__':
    
    app.run(host="127.0.0.1",
            port=8000)