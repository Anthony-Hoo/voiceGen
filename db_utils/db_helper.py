

class CharacterDTO:
    # 文件名
    fileName = ''
    # 不同语言的名字
    npcNameLocal = ''
    # 对话文本
    text = ''
    # 对话类型
    type = ''
    # 对话主题
    topic = ''
    # 代码中的名字
    npcNameCode = ''
    # 文本语言
    language = ''
    # url
    audioURL = ''

    def printAll(self):
        print(self.fileName, self.npcNameLocal, self.text, self.type, self.topic, self.npcNameCode, self.language, self.audioURL)


# 从result.py读取数据，并写入到./db/genshinVoice.db中
def writeData():
    import sqlite3
    conn = sqlite3.connect('./db/genshinVoice.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS character")
    c.execute("CREATE TABLE character (id INTEGER PRIMARY KEY AUTOINCREMENT, npcNameLocal TEXT, sex BOOL, type TEXT, topic TEXT, text TEXT, npcNameCode TEXT, language TEXT, fileName TEXT, audioURL TEXT)")
    
    import json
    with open('./db/result.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        for i in data:
            if data.get(i).get('language') == 'CHS':
                chadto = CharacterDTO()
                chadto.language = data.get(i).get('language')
                chadto.fileName = data.get(i).get('fileName')
                chadto.npcNameLocal = data.get(i).get('npcName')
                chadto.text = data.get(i).get('text')
                chadto.type = data.get(i).get('type')

                fileInfo = chadto.fileName.split('\\')
                # 拿到codename
                chadto.npcNameCode = fileInfo[-2].lower().replace('vo_', '')
                # 如果是futter对话，拿到topic
                if chadto.type == 'Fetter':
                    chadto.topic = '_'.join(fileInfo[-1].split('.')[0].split('_')[-2:])
                # 转换url
                chadto.audioURL = 'https://raw.githubusercontent.com/CSUSTers/mys-voice-genshin/main/res/audio/chs34v/Merged_Chinese_Wav/' + '/'.join(chadto.fileName.split('\\')[1:]).replace('.wem', '.ogg')
                # 将chadto写入到数据库中
                sql = "INSERT INTO character (npcNameLocal, sex, type, topic, text, npcNameCode, language, fileName, audioURL) VALUES ('{}', '{}', '{}', '{}','{}', '{}', '{}', '{}','{}')".format(
                    chadto.npcNameLocal, 
                    None, 
                    chadto.type, 
                    chadto.topic, 
                    chadto.text, 
                    chadto.npcNameCode, 
                    chadto.language, 
                    chadto.fileName, 
                    chadto.audioURL
                )
                c.execute(sql)
                conn.commit()
    conn.close()

if __name__ == '__main__':
    writeData()