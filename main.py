from flask import Flask, request, abort
import os
import json
import unicodedata

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, CarouselTemplate, CarouselColumn, FlexSendMessage,
    BubbleContainer, ImageComponent, URIAction
)

app = Flask(__name__)

# 環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# class Data:
#     DoW_list = {
#         "月1": "Wrightin",
#         "月2": "Wrightin2"
#     }
#
#     def __init__(self, uid):
#         """
#
#         :param uid: UID allocated to individual LINE account.
#         """
#         self.uid = uid
#         self.DoW = ""
#         self.type = ""
#         self.date = 0
#         self.msg = ""
#
#     def add(self, DoW, type, date, msg):
#         """
#         Used to
#         :param DoW:
#         :param type:
#         :param date:
#         :param msg:
#         :return:
#         """
#         self.DoW = DoW
#         self.type = type
#         self.date = date
#         self.msg = msg
#
#     def modify(self, DoW, type, msg):
#         pass
#

class Send:
    def __init__(self, uid):
        self.uid = uid

    def add(self):
        pass

    def messagePrepare(self, message):
        pass


class ProcessReplyMsg:
    """
    This class is designed to prepare for reply message.
    """

    DoW_list = {
        "月1": "Wrightin",
        "月2": "Wrightin2"
    }
    Type_list = {
        "assignment": "",
        "memo": "[*]"
    }

    def __init__(self, uid):
        """
        Initialize variable.
        :param uid: UID allocated to individual LINE account.
        """
        self.uid = uid
        self.DoW = []
        self.type = []
        self.date = []
        self.msg = []

    def receiveMsg(self,text):
        """
        Classifying operation type. ie. Add,Modify,Delete...etc
        :param text: raw data send to this Bot
        """
        if '.add' in text:
            process.addPrepare(text)
        elif '.mod' in text:
            process.modify(text)
        elif '.del' in text:
            process.delete(text)
        elif 'check schedule' in text:
            pass
        else:
            pass

    def addPrepare(self, text):
        #shori
        # process.add()
        pass

    def modify(self, text):
        pass

    def delete(self, text):
        pass

    def add(self, DoW, type, date, msg):
        """
        Append each data to the array. Temp storage for next Sending process.
        :param DoW: (str) Day of Week. This also includes lecture period.
        :param type: (str) type of your text. [assignment or memo]
        :param date: (int) Due date. 6-digits:(mmddyy)
        :param msg: (str) Text to notify.
        """
        self.DoW.append(DoW)
        self.type.append(type)
        self.date.append(date)
        self.msg.append(msg)

    def display(self):
        """
        Test function to make sure the array is correctly used.
        :return:
        """

        #getting number of posts.
        arrSize = len(self.msg)

        for _i in range(0, arrSize):
            month = str(self.date[_i])[:2]
            day = str(self.date[_i])[2:4]
            dates = month + '/' + day
            DoW_jp = self.DoW_list[self.DoW[_i]]

            print("[{}][{}]{}{}".format(dates, self.DoW[_i], self.Type_list[self.type[_i]], self.msg[_i]))

    def send(self):

        pass



@app.route("/")
def hello_world():
    return "hello world!"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # SQLから来たのを分解後
    # message = Data("das08")
    # message.add("月1","assignment",103119,"線形台数レポート")
    uid=line_bot_api.get_profile(user_id)

    process = ProcessReplyMsg("das08")
    process.add("月1", "assignment", 100119, "線形台数レポート")
    process.add("月2", "memo", 103119, "明日は雨")
    process.display()
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=uid.user_id))

if __name__ == "__main__":
    #    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)