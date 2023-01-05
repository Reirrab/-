# -*- coding:utf-8 -*-

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import websocket   #爬取网站
import hashlib    #加密解密作用
import base64   #用于小型数据传输    编码解码
import hmac     #保证消息的完整性
import json     #一种字符串类型
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import pyaudio    #录音   播放   生成wav文件
import requests
from tkinter import *
import threading
import tkinter
global Time

#录制时间
STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

import string
def removePunctuation(text):                       #去除标点，使翻译不出问题
    newtext = ''
    for i in text:
        if (i == '.' or i == '?' or i == '。' or i == '？'):
            continue
        else:
            newtext = newtext + i
    return newtext
def huanyuan(text):                                 #将原标点还原  并且翻译
    new=''
    for i in text:
        if(i=='.'):
            new=new+'。'
        elif(i=='?'):
            new=new+'？'
        elif (i == '。'):
            new = new + '.'
        elif (i == '？'):
            new = new + '.'
        else:
            continue
    return new
class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret


        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo":1,"vad_eos":10000}

    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url


# 收到websocket消息的处理

def on_message(ws, message):
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))

        else:
            data = json.loads(message)["data"]["result"]["ws"]
            result = ""
            for i in data:
                for w in i["cw"]:
                    result += w["w"]

            if result == '。' or result=='.。' or result==' .。' or result==' 。':
                pass
            else:
                t2.insert(END, result)                                                #将文字打在屏幕上
                result2=result                                                       #将带有标点的输出结果存档   方便后续操作
                result=removePunctuation(result)
                print("输出结果: " , result)
                url = 'http://fanyi.youdao.com/translate'
                headera = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'}
                data = {
                    'i': result,

                    'doctype': 'json',

                }
                response = requests.post(url, headers=headera, data=data)
                dict_str = json.loads(response.content.decode())
                tran = dict_str['translateResult'][0][0]['tgt']                        #tran就是翻译出来的句子    如果需要在出一个屏幕   只需写  t.insert(END,tran)
                bd=huanyuan(result2)                                                   #取标点并还原回去使句子连贯
                t3.insert(END,bd)
                t3.insert(END, tran)          # 打印在第二块屏幕上，但要根据第二块屏幕的定义进行操作

                print("翻译结果：",tran)
    except Exception as e:
        print("receive msg,but parse exception:", e)


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws):
    pass
    # print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
    def run(*args):
        status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧
        CHUNK = 520                 # 定义数据流块
        FORMAT = pyaudio.paInt16  # 16bit编码格式
        CHANNELS = 1  # 单声道
        RATE = 16000  # 16000采样频率
        p = pyaudio.PyAudio()
        # 创建音频流
        stream = p.open(format=FORMAT,  # 音频流wav格式
                        channels=CHANNELS,  # 单声道
                        rate=RATE,  # 采样率16000
                        input=True,
                        frames_per_buffer=CHUNK)

        print("- - - - - - - Start Recording ...- - - - - - - ")

        for i in range(0,int(RATE/CHUNK*60)):
            buf = stream.read(CHUNK)
            if not buf:
                status = STATUS_LAST_FRAME
            if status == STATUS_FIRST_FRAME:

                d = {"common": wsParam.CommonArgs,
                     "business": wsParam.BusinessArgs,
                     "data": {"status": 0, "format": "audio/L16;rate=16000",
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": "raw"}}
                d = json.dumps(d)
                ws.send(d)
                status = STATUS_CONTINUE_FRAME
                # 中间帧处理
            elif status == STATUS_CONTINUE_FRAME:
                d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": "raw"}}
                ws.send(json.dumps(d))

            # 最后一帧处理
            elif status == STATUS_LAST_FRAME:
                d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                              "audio": str(base64.b64encode(buf), 'utf-8'),
                              "encoding": "raw"}}
                ws.send(json.dumps(d))
                time.sleep(1)
                break

        stream.stop_stream()
        stream.close()
        p.terminate()
        ws.close()
    thread.start_new_thread(run,())


def run():
    global wsParam
    wsParam = Ws_Param(APPID='',
                       APIKey='',
                       APISecret='')
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_timeout=2)

# TODO 记得修改 APPID、APIKey、APISecret


def thread_it(func, *args):
    time = IntVar()
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)
    t.start()

###存储###
import tkinter.filedialog
import os

def saveas(text):
    saveasroot = tkinter.Tk()  # 创建一个Tkinter.Tk()实例
    saveasroot.withdraw()  # 将Tkinter.Tk()实例隐藏
    filename = tkinter.filedialog.asksaveasfilename(title=u'保存文件', filetypes=[("文本文档 ", ".txt")])
    with open(filename+'.txt', 'w', encoding='utf-8') as fin:
           fin.write(text)
    saveasroot.destroy()

###

root = Tk()
root.title("实时语音翻译系统")
t = Text(root)
t2=Text(root)
t3=Text(root)
t.pack()
t2.pack()
t3.pack()
t2.insert(END,"以下是录音内容（The following is the transcript）：\n")
t3.insert(END,"以下是翻译内容（The following is the translation）：\n")
btprint=Button(t,text="启动录音",fg="blue",bg="pink",command=lambda :thread_it(run,))                    #按钮
btprint.grid(row=1,column=1)
# tkinter.Button(root, text='启动录音', command=lambda :thread_it(run,)).pack()

def getTextInput():
    result = t2.get("1.0", "end")  # 获取文本输入框的内容
    saveas(result)  # 输出结果

def sourcegetTextInput():
    result = t3.get("1.0", "end")  # 获取文本输入框的内容
    saveas(result)  # 输出结果


btnRead = Button(t, text="原文保存", command=getTextInput)  # command绑定获取文本框内容的方法
btnRead.grid(row=1,column=3)
btnRead1 = Button(t, text="翻译保存", command=sourcegetTextInput)  # command绑定获取文本框内容的方法
btnRead1.grid(row=1,column=4)
root.mainloop()