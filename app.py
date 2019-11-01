from flask import Flask, request, abort
import os
import json
import unicodedata
import psycopg2
import datetime

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


class Send:
    def __init__(self):
        self.uid = "ss"
        self.messageBlock = ""

    def sendText(self, reply_token, message):
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=message))


class DB:
    def __init__(self):
        """
        Below are mainly used for putting data fetched from DB.
        Using this to send reply.
        """
        self.uid = ""
        self.DoW = []
        self.dates = []
        self.types = []
        self.text = []

    def get_connection(self):
        dsn = "***"
        return psycopg2.connect(dsn)

    def checkUser(self, uid):
        self.uid = uid
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    sqlStr = f"select notification from userdata where uid='{self.uid}'"
                    cur.execute(sqlStr)
                    results = cur.fetchall()
                    NumberOfRecord = len(results)
                    if NumberOfRecord == 0:
                        sqlStr = f"insert into userdata(uid) values ('{self.uid}')"
                        cur.execute(sqlStr)

                    return True
                except:
                    return False

    def addtoDB(self, texts, uid):
        """
        Syntax: .add {DoW+Period} {text} {due date} {type:default is memo}
        :param texts: raw data sended to this Bot
        :return:
        """
        param = texts.split()
        DoW = param[1]
        text = param[2]
        dates = int(param[3])
        if len(param) <= 4:
            types = "memo"
        else:
            types = param[4]
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    sqlStr = "INSERT INTO todo(uid,dow,dates,types,text) VALUES (%s,%s,%s,%s,%s)"
                    cur.execute(sqlStr, (uid, DoW, dates, types, text))
                    return True
                except:
                    return False

    def getToDo(self, uid):
        self.DoW = []
        self.dates = []
        self.types = []
        self.text = []

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    sqlStr = "SELECT dow,dates,types,text FROM todo WHERE uid = (%s)"
                    cur.execute(sqlStr, (uid,))
                    result = cur.fetchall()
                    arrSize = len(result)
                    for rows in result:
                        self.DoW.append(rows[0])
                        self.dates.append(rows[1])
                        self.types.append(rows[2])
                        self.text.append(rows[3])
                    return
                except:
                    return False


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
        self.messageBlock = ""

    def receiveMsg(self, reply_token, text, uid):
        """
        Classifying operation type. ie. Add,Modify,Delete...etc
        :param reply_token: as it is.
        :param text: raw data sended to this Bot
        """
        send = Send()
        connectDB = DB()

        if '.add' in text:
            if self.add(text):
                if connectDB.addtoDB(text, uid):
                    message = "Successfully added to DB:)"
                else:
                    message = "Failed to add your todo to DB:("
            else:
                message = "Invalid Syntax.\n.add {DoW+Period} {text} {due date} {type:default is memo}"
            send.sendText(reply_token, message)
        elif '.mod' in text:
            process.modify(text)
        elif '.del' in text:
            process.delete(text)
        elif 'send' in text:
            connectDB.getToDo(uid)
            arrSize=len(connectDB.DoW)
            for _i in range(0,arrSize):
                self.sampleAdd(connectDB.DoW[_i], connectDB.types[_i], connectDB.dates[_i], connectDB.text[_i])

            if len(connectDB.DoW) == 0:
                message = "There is no new todo tasks."
            else:
                message = self.messagePrepare()
            send.sendText(reply_token, message)
        else:
            self.sampleAdd("月1", "assignment", 110119, text)
            send.sendText(reply_token, self.messagePrepare())

    def messagePrepare(self):
        """
        :return: messageBlock : returns a block of all recorded todo schedule
        """
        arrSize = len(self.msg)
        for _i in range(0, arrSize):
            month = str(self.date[_i])[:2]
            day = str(self.date[_i])[2:4]
            dates = month + '/' + day
            # DoW_jp = self.DoW_list[self.DoW[_i]]
            self.messageBlock += "[{dates}][{period}]{type}{text}" \
                .format(dates=dates, period=self.DoW[_i], type=self.Type_list[self.type[_i]], text=self.msg[_i])
            if _i != arrSize - 1:
                self.messageBlock += "\n"
        return self.messageBlock

    def add(self, text):
        """
        Syntax: .add {DoW+Period} {text} {due date} {type:default is memo}
        :param text: raw data sended to this Bot
        :return:
        """
        param = text.split()
        if len(param) <= 4:
            types = "memo"
        else:
            types = param[4]
        if checkDoW(param[1]) and checkDate(param[3]) and checkType(types):
            # add this to sql
            self.sampleAdd(param[1], types, param[3], param[2])
            return True
        else:
            return False

    def modify(self, text):
        pass

    def delete(self, text):
        pass

    def sampleAdd(self, DoW, types, dates, msg):
        """
        Append each data to the array. Temp storage for next Sending process.
        :param DoW: (str) Day of Week. This also includes lecture period.
        :param types: (str) type of your text. [assignment or memo]
        :param dates: (int) Due date. 6-digits:(mmddyy)
        :param msg: (str) Text to notify.
        """
        self.DoW.append(DoW)
        self.type.append(types)
        self.date.append(dates)
        self.msg.append(msg)

    def display(self):
        """
        Test function to make sure the array is correctly used.
        :return:
        """

        # getting number of posts.
        arrSize = len(self.msg)

        for _i in range(0, arrSize):
            month = str(self.date[_i])[:2]
            day = str(self.date[_i])[2:4]
            dates = month + '/' + day
            DoW_jp = self.DoW_list[self.DoW[_i]]

            print("[{}][{}]{}{}".format(dates, self.DoW[_i], self.Type_list[self.type[_i]], self.msg[_i]))


def checkDoW(text):
    DoW = text[0]
    period = text[1]
    if DoW in '月火水木金' and period in '12345':
        return True
    else:
        return False


def checkDate(num):
    month = int(str(num[:2]))
    date = int(str(num[2:4]))
    year = int(str(num[4:6]))
    try:
        check = "%04d/%02d/%02d" % (year + 2000, month, date)
        checking = datetime.datetime.strptime(check, "%Y/%m/%d")
        return True
    except ValueError:
        return False


def checkType(text):
    if text == "assignment" or text == "memo":
        return True
    else:
        return False


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
    uid = event.source.user_id

    process = ProcessReplyMsg(uid)
    send = Send()
    connectDB = DB()

    # process.sampleAdd("月1", "assignment", 100119, "線形台数レポート")
    # process.sampleAdd("月2", "memo", 103119, "明日は雨")

    # connectDB.get_connection()
    if connectDB.checkUser(uid):
        pass
    else:
        send.sendText(event.reply_token, "Failed to connect to DB. Please try again.")

    connectDB.getToDo(uid)
    print(connectDB.DoW)
    process.receiveMsg(event.reply_token, event.message.text, uid)

    # process.display()


if __name__ == "__main__":
    #    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
