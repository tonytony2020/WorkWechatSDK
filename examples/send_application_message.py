# encoding: utf-8

import os

import work_wechat

corpid = os.environ.get("CORPID")
corpsecret = os.environ.get("CORPSECRET")
agentid = os.environ.get("agentid")

ww = work_wechat.WorkWeChat(corpid=corpid, corpsecret=corpsecret)


def send_text_message():
    text_content = dict(content=" 你的快递已到，请携带工卡前往邮件中心领取。\n出发前可查看<a href=\"http://work.weixin.qq.com\">"
                                "邮件中心视频实况</a>，聪明避开排队。")
    touser = "Jense"
    """发送文本信息"""
    ww.message_send(agentid=agentid, content=text_content, touser=touser, msgtype="text")


def send_file_message():
    """发送文件信息"""
    file_path = 'D:/'
    file_name = "啊.txt"
    media = work_wechat.Media(file_path=file_path, file_name=file_name, file_type='file')
    touser = 'Jense'
    media_id = ww.media_upload(media=media)
    content = dict(media_id=media_id)
    ww.message_send(agentid=agentid, msgtype="file", touser=touser, content=content)


def send_image_message():
    """发送照片信息"""
    file_path = 'D:/'
    file_name = "jense.jpg"
    media = work_wechat.Media(file_path=file_path, file_name=file_name, file_type='image')
    touser = 'Jense'
    media_id = ww.media_upload(media=media)
    content = dict(media_id=media_id)
    ww.message_send(agentid=agentid, msgtype="image", touser=touser, content=content)


def send_task_card_message():
    """发送任务卡片"""
    task_id = '464fsf6'
    task_card = dict(title="Jense的礼品申请", url="https://qyapi.weixin.qq.com", task_id=task_id,
                     description="礼品：A31茶具套装<br>用途：赠与小黑科技张总经理")

    btn = [dict(key="key111", name="批准", replace_name="已批准", color="red", is_bold=True),
           dict(key="key222", name="驳回", replace_name="已驳回")]
    task_card['btn'] = btn
    touser = 'Jense'
    ww.message_send(agentid=agentid, content=task_card, touser=touser, msgtype="taskcard")


send_file_message()
send_image_message()
send_text_message()
send_task_card_message()
