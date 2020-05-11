import os
import uuid

import work_wechat

corpid = os.environ.get("CORPID")
corpsecret = os.environ.get("CORPSECRET")
agentid = int(os.environ.get("AGENTID"))

ww = work_wechat.WorkWeChat(corpid=corpid, corpsecret=corpsecret)


def send_text_message():
    """发送文本信息"""
    text_content = """ 你的快递已到，请携带工卡前往邮件中心领取。
                   \n出发前可查看<a href=\"http://work.weixin.qq.com\">邮件中心视频实况</a>，聪明避开排队。"""

    touser = ("Jense",)
    ww.message_send(agentid=agentid, content=text_content, touser=touser, msgtype="text")


def send_image_message():
    """发送照片信息"""
    file_path = "D:/jense.jpg"
    file_name = os.path.basename(file_path)
    file_data = open(file_path, "rb")

    media = work_wechat.Media(file_name=file_name, file_data=file_data)
    touser = ('Jense',)

    media_id = ww.media_upload(media=media)
    ww.message_send(agentid=agentid, msgtype=work_wechat.MsgType.IMAGE, touser=touser, media_id=media_id)


def send_video_message():
    """发送语音信息"""
    file_path = "D:/语音测试.amr"
    file_name = os.path.basename(file_path)

    file_data = open(file_path, "rb")

    media = work_wechat.Media(file_name=file_name, file_data=file_data)
    touser = ('Jense',)

    media_id = ww.media_upload(media=media)
    ww.message_send(agentid=agentid, msgtype=work_wechat.MsgType.VOICE, touser=touser, media_id=media_id)


def send_video_mp4_message():
    """发送视频信息"""
    file_path = 'D:/video.mp4'
    file_name = os.path.basename(file_path)
    file_data = open(file_path, "rb")

    media = work_wechat.Media(file_name=file_name, file_data=file_data)
    touser = ('Jense',)

    media_id = ww.media_upload(media=media)
    video = work_wechat.Video(media_id=media_id, title="mp4测试", description="just a mp4 test")
    ww.message_send(agentid=agentid, msgtype=work_wechat.MsgType.VIDEO, touser=touser, video=video)


def send_file_message():
    """发送文件信息"""
    file_path = 'D:/啊.txt'
    file_name = os.path.basename(file_path)
    file_data = open(file_path, "rb")

    media = work_wechat.Media(file_name=file_name, file_data=file_data)
    media_id = ww.media_upload(media=media)

    touser = ('Jense',)
    ww.message_send(agentid=agentid, msgtype=work_wechat.MsgType.FILE, touser=touser, media_id=media_id)


def send_text_card_meesage():
    """发送文本卡片信息"""
    textcard = work_wechat.TextCard(
        title="WorkWechat test",
        description="this is a demo",
        url="https://work.weixin.qq.com",
        btntxt="更多"
    )

    touser = ('Jense',)

    ww.message_send(agentid=agentid, msgtype="textcard", touser=touser, textcard=textcard)


def send_news_message():
    """发送图文信息"""
    news_articles1 = work_wechat.NewsArticle(
        picurl="http://wwcdn.weixin.qq.com/node/wwnl/wwnl/style/images/independent/favicon/favicon_48h$c976bd14.png",
        title="图文信息发送测试",
        url="https://work.weixin.qq.com/api/doc/90000/90135/90236#文件消息",
        description="详情"
    )

    touser = ('Jense',)

    ww.message_send(agentid=agentid, msgtype=work_wechat.MsgType.NEWS, touser=touser, news_articles=(news_articles1,))


def send_mpnews_message():
    """发送图文信息"""
    file_path = 'D:/jense.jpg'
    file_name = os.path.basename(file_path)
    file_data = open(file_path, "rb")

    media = work_wechat.Media(file_name=file_name, file_data=file_data)
    media_id = ww.media_upload(media)

    mpnew_articles1 = work_wechat.MpNew(
        title="WorkWeChat 图文信息推送测试",
        thumb_media_id=media_id,
        author="Nobody",
        concontent_source_url='https://work.weixin.qq.com/api/doc/90000/90135/90236',
        content="正文内容，支持HTML标签",
        digest="这是我的微信头像"
    )

    mpnew_articles2 = work_wechat.MpNew(
        title="WorkWeChat 图文信息推送测试",
        thumb_media_id=media_id,
        author="aaaa",
        concontent_source_url='https://work.weixin.qq.com/api/doc/90000/90135/90236',
        content="正文内容，支持HTML标签,啦啦啦",
        digest="微信头像"
    )

    touser = ('Jense', 'Lucy',)

    ww.message_send(
        agentid=agentid,
        msgtype=work_wechat.MsgType.MPNEWS,
        touser=touser,
        mpnews_articles=(mpnew_articles1, mpnew_articles2)
    )


def send_markdown_message():
    """发送markdown信息"""

    markdown_content = """您的会议室已经预定，稍后会同步到`邮箱` 
                >**事项详情** 
                >事　项：<font color=\"info\">开会</font> 
                >组织者：@miglioguan 
                >参与者：@miglioguan、@kunliu、@jamdeezhou、@kanexiong、@kisonwang 
                > 
                >会议室：<font color=\"info\">广州TIT 1楼 301</font> 
                >日　期：<font color=\"warning\">2018年5月18日</font> 
                >时　间：<font color=\"comment\">上午9:00-11:00</font> 
                > 
                >请准时参加会议。 
                > 
                >如需修改会议信息，请点击：[修改会议信息](https://work.weixin.qq.com)"""

    touser = ('Jense',)

    ww.message_send(agentid=agentid, msgtype='markdown', touser=touser, content=markdown_content)


def send_task_card_message():
    """发送任务卡片"""
    task_id = str(uuid.uuid4())
    btn1 = work_wechat.TaskCardBtn(key="key111", name="批准", replace_name="已批准", color="red", is_bold=True)
    btn2 = work_wechat.TaskCardBtn(key="key222", name="驳回", replace_name="已驳回")
    btnList = [btn1.to_dict(), btn2.to_dict()]

    task_card = work_wechat.TaskCard(
        title="Jense的礼品申请",
        url="https://qyapi.weixin.qq.com",
        task_id=task_id,
        description="礼品：A31茶具套装<br>用途：赠与小黑科技张总经理",
        btn=btnList
    )

    touser = ('Jense',)

    ww.message_send(agentid=agentid, taskcard=task_card, touser=touser, msgtype="taskcard")


send_text_message()
send_image_message()

send_video_message()
send_video_mp4_message()

send_file_message()
send_text_card_meesage()

send_news_message()
send_mpnews_message()

send_markdown_message()
send_task_card_message()
