import os
import time
from flask import Flask, request, jsonify, render_template, url_for, redirect
from flask_restful.reqparse import RequestParser
import requests
from utils import tts_helper
from utils.sovits import inference_main
from utils import gpu_woker_quene
from utils import tools
import yaml


config = yaml.safe_load(open("./config.yaml", encoding="utf-8"))

app = Flask(__name__)
app.debug = config["flask"]["debug"]
app.secret_key = config["flask"]["secret_key"]
sqlite_path = config["sqlite"]["path"]
worker_quene = gpu_woker_quene.GPUWorkerQuene()
worker_quene.start()


@app.route("/GetVoice")
def giveBackURL():
    if request.method == "GET":
        # 从./db/character.db中随机取出一条数据，以json返回
        import sqlite3

        conn = sqlite3.connect(sqlite_path + "character.db")
        c = conn.cursor()
        c.execute(
            "SELECT * FROM character WHERE id >= (ABS(RANDOM()) % (SELECT MAX(id) FROM character)) LIMIT 1;"
        )
        result = c.fetchone()
        conn.close()
        # 生成返回的json
        return jsonify(
            {
                "character": result[1],
                "topic": result[2],
                "text": result[3],
                "audio": result[4],
            }
        )


@app.route("/GetVoice/v2")
def giveBackURLv2():
    if request.method == "GET":
        try:
            parser = RequestParser()
            parser.add_argument("character", location="args", required=False)
            parser.add_argument("topic", location="args", required=False)
            parser.add_argument("text", location="args", required=False)
            parser.add_argument("sex", location="args", required=False)
            parser.add_argument("type", location="args", required=False)
            args = parser.parse_args()
            print(args)
            # 替换掉空参数
            if args["character"] == None:
                args["character"] = ""
            if args["topic"] == None:
                args["topic"] = ""
            if args["text"] == None:
                args["text"] = ""
            if args["sex"] == None:
                args["sex"] = ""
            if args["type"] == None:
                args["type"] = ""

            import sqlite3

            conn = sqlite3.connect(sqlite_path + "genshinVoice.db")
            c = conn.cursor()

            with conn:
                # 如果没有参数，随机返回一条数据
                if (
                    args["character"] == None
                    and args["topic"] == None
                    and args["text"] == None
                ):
                    c.execute(
                        "SELECT * FROM character WHERE id >= (ABS(RANDOM()) % (SELECT MAX(id) FROM character)) LIMIT 1;"
                    )
                    result = c.fetchone()
                    return jsonify(result)
                # 如果有参数，根据参数返回数据
                else:
                    sql = """
                    with filtered as (SELECT id
                                    FROM character
                                    WHERE npcNameLocal like ?
                                        AND topic like ?
                                        AND "text" like ?
                                        AND sex like ?
                                        AND type like ?)
                    select *
                    from character
                    where id in (select id from filtered order by random() limit 1)
                    """

                    c.execute(
                        sql,
                        (
                            f"%{args['character']}%",
                            f"%{args['topic']}%",
                            f"%{args['text']}%",
                            f"%{args['sex']}%",
                            f"%{args['type']}%",
                        ),
                    )

                    # 从result中随机取出一条数据
                    results = c.fetchall()
                    # 如果没有数据，返回404
                    if len(results) == 0:
                        return jsonify({"text": "进不去……"}), 404

                    result = results[0]
                    return jsonify(
                        {
                            "npcNameLocal": result[1],
                            "sex": result[2],
                            "type": result[3],
                            "topic": result[4],
                            "text": result[5],
                            "npcNameCode": result[6],
                            "language": result[7],
                            "fileName": result[8],
                            "audioURL": result[9],
                        }
                    )
        except Exception as e:
            print(e)
            return jsonify({"text": "进不去……", "err": str(e)}), 404


@app.route("/GetVoice/v3")
def generateCharaVoice():
    if request.method == "GET":
        try:
            parser = RequestParser()
            # 选择的角色以及将要生成的文本
            parser.add_argument("character", location="args", required=False)
            parser.add_argument("text", location="args", required=True)
            args = parser.parse_args()
            # 如果角色为空，则从配置文件随机选一个角色
            voice_model = {}
            if args["character"] == None:
                import random

                voice_model = random.choice(config["genshin"]["voice_model"])
            else:
                if any(
                    model["character_name"] == args["character"]
                    for model in config["genshin"]["voice_model"]
                ):
                    voice_model = next(
                        model
                        for model in config["genshin"]["voice_model"]
                        if model["character_name"] == args["character"]
                    )

                else:
                    return jsonify({"text": "角色不存在……"}), 404

            tts_output_path = tts_helper.tts_azure(
                tts_config=config["azure"], txt=args["text"]
            )
            infer_args = {
                "model_path": voice_model["model_path"],
                "config_path": voice_model["config_path"],
                "trans": voice_model["key"],
                "spk_list": voice_model["speaker_name"],
                "clean_names": tts_output_path,
            }
            worker_quene.add_task((inference_main.inference, infer_args))

            genshin_voice_path = f'./{tts_output_path.replace("tts", "infer")}_{str(voice_model["key"])+"key"}_{voice_model["speaker_name"]}.flac'
            # 等待生成的音频文件生成, 检查文件是否存在
            start_time = time.time()
            while not os.path.exists(genshin_voice_path):
                time.sleep(0.1)
                # 最多等待120秒
                if time.time() - start_time > 120:
                    return jsonify({"text": "进不去……"}), 404

            # 调用ffmpeg将音频文件转码为ogg
            os.system('/usr/bin/ffmpeg -i '+ genshin_voice_path +' -c:a libopus -b:a 96K  {}.ogg -y'.format(genshin_voice_path.replace('.flac', '')))
            # 删除原始文件
            os.remove(genshin_voice_path)
            genshin_voice_path = genshin_voice_path.replace('.flac', '.ogg')

            upload_url = "{}/upload?token={}".format(
                config["genshin"]["file_server"]["host"],
                config["genshin"]["file_server"]["token"],
            )
            # 将音频文件上传到api服务器
            file_path = tools.upload_file(upload_url, genshin_voice_path)
            if file_path != None:
                voice_url = "{}{}?token={}".format(
                    config["genshin"]["file_server"]["host"],
                    file_path,
                    config["genshin"]["file_server"]["token"],
                )
                return jsonify(
                    {
                        "voice_url": voice_url,
                        "character": voice_model["character_name"],
                        "text": args["text"],
                    }
                )
            else:
                return jsonify({"text": "进不去……"}), 404

        except Exception as e:
            print(e)
            return jsonify({"text": "进不去……", "err": str(e)}), 404

# 自定义SSML生成语音文件
@app.route("/GetVoice/v4")
def generateCharaVoicePro():
    if request.method == "GET":
        try:
            parser = RequestParser()
            # 选择的角色以及将要生成的文本
            parser.add_argument("character", location="args", required=False)
            parser.add_argument("text", location="args", required=True)
            args = parser.parse_args()
            # 如果角色为空，则从配置文件随机选一个角色
            voice_model = {}
            if args["character"] == None:
                import random

                voice_model = random.choice(config["genshin"]["voice_model"])
            else:
                if any(
                    model["character_name"] == args["character"]
                    for model in config["genshin"]["voice_model"]
                ):
                    voice_model = next(
                        model
                        for model in config["genshin"]["voice_model"]
                        if model["character_name"] == args["character"]
                    )

                else:
                    return jsonify({"text": "角色不存在……"}), 404

            tts_output_path = tts_helper.tts_azure_customized(
                tts_config=config["azure"], txt=args["text"]
            )
            infer_args = {
                "model_path": voice_model["model_path"],
                "config_path": voice_model["config_path"],
                "trans": voice_model["key"],
                "spk_list": voice_model["speaker_name"],
                "clean_names": tts_output_path,
            }
            worker_quene.add_task((inference_main.inference, infer_args))

            genshin_voice_path = f'./{tts_output_path.replace("tts", "infer")}_{str(voice_model["key"])+"key"}_{voice_model["speaker_name"]}.flac'
            # 等待生成的音频文件生成, 检查文件是否存在
            start_time = time.time()
            while not os.path.exists(genshin_voice_path):
                time.sleep(0.1)
                # 最多等待120秒
                if time.time() - start_time > 120:
                    return jsonify({"text": "进不去……"}), 404

            # 调用ffmpeg将音频文件转码为ogg
            os.system('ffmpeg -i '+ genshin_voice_path +' -c:a libopus -b:a 96K  {}.ogg -y'.format(genshin_voice_path.replace('.flac', '')))
            # 删除原始文件
            os.remove(genshin_voice_path)
            genshin_voice_path = genshin_voice_path.replace('.flac', '.ogg')

            upload_url = "{}/upload?token={}".format(
                config["genshin"]["file_server"]["host"],
                config["genshin"]["file_server"]["token"],
            )
            # 将音频文件上传到api服务器
            file_path = tools.upload_file(upload_url, genshin_voice_path)
            if file_path != None:
                voice_url = "{}{}?token={}".format(
                    config["genshin"]["file_server"]["host"],
                    file_path,
                    config["genshin"]["file_server"]["token"],
                )
                return jsonify(
                    {
                        "voice_url": voice_url,
                        "character": voice_model["character_name"],
                        "text": args["text"],
                    }
                )
            else:
                return jsonify({"text": "进不去……"}), 404

        except Exception as e:
            print(e)
            return jsonify({"text": "进不去……", "err": str(e)}), 404

def run():
    app.run(host="*0.0.0.0", port=8000)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
