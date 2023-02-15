from flask import Flask, request, jsonify, render_template, url_for, redirect



app = Flask(__name__)
app.config.from_object("config")
app.secret_key = 'd25ba7735e13a52601fd339fd28f9d869b5ba3759e9e464d3911224820f3a22a'







@app.route('/getVoice')
def giveBackURL():
    if(request.method == "GET"):
        # 从./db/character.db中随机取出一条数据，以json返回
        import sqlite3
        conn = sqlite3.connect('/var/www/character.db')
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

def run():
    app.run(host="*0.0.0.0", port=8000)


if __name__ == '__main__':
    
    app.run(host="127.0.0.1", port=8000)