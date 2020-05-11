import os
import uuid

import work_wechat
import time

corpid = os.environ.get("CORPID")
corpsecret = os.environ.get("CORPSECRET")
agentid = int(os.environ.get("agentid"))

ww = work_wechat.WorkWeChat(corpid=corpid, corpsecret=corpsecret)

task_id = str(uuid.uuid4())

btn_approve = work_wechat.TaskCardBtn(key="key111", name="批准", replace_name="已批准", color="red", is_bold=True)
btn_reject = work_wechat.TaskCardBtn(key="key222", name="驳回", replace_name="已驳回")

btn_list = [btn_approve.to_dict(), btn_reject.to_dict()]

task_card = work_wechat.TaskCard(
    title="Jense的礼品申请",
    url="https://qyapi.weixin.qq.com",
    task_id=task_id,
    description="礼品：A31茶具套装<br>用途：赠与小黑科技张总经理",
    btn=btn_list
)

touser = ('Jense',)

ww.message_send(agentid=agentid, taskcard=task_card, touser=touser, msgtype="taskcard")

userids = ('Jense',)

ww.update_taskcard(agentid=agentid, task_id=task_id, clicked_key='key222', userids=userids)
