import pymongo

# 连接数据库
client = pymongo.MongoClient("127.0.0.1", 27017)
db = client["voicehash"]
hashSet = db["hashset"]


def parse():
    print("b")
    with open("./static/hashList.txt", encoding="utf-8") as fp:
        hashList = fp.readlines()
        print("a")
        for hash in hashList:
            info = {
                "voiceHash" : hash.replace("\n", "")
            }
            print(info)
            hashSet.insert(info)

if __name__ == '__main__':
    parse()
