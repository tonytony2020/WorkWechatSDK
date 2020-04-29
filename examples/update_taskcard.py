import os

import work_wechat
import time

corpid = os.environ.get("CORPID")
corpsecret = os.environ.get("CORPSECRET")
agentid = os.environ.get("agentid")

ww = work_wechat.WorkWeChat(corpid=corpid, corpsecret=corpsecret)

task_id = '234336'

btn1 = work_wechat.Btn(key="key111", name="批准", replace_name="已批准", color="red", is_bold=True)
btn2 = work_wechat.Btn(key="key222", name="驳回", replace_name="已驳回")
btnList = [btn1.to_dict(), btn2.to_dict()]

task_card = work_wechat.TaskCard(
    title="Jense的礼品申请",
    url="https://qyapi.weixin.qq.com",
    task_id=task_id,
    description="礼品：A31茶具套装<br>用途：赠与小黑科技张总经理",
    btn=btnList
)

touser = 'Jense'

ww.message_send(agentid=agentid, taskcard=task_card, touser=touser, msgtype="taskcard")

time.sleep(2)

userids = ['Jense']

ww.update_taskcard(agentid=agentid, task_id=task_id, clicked_key='key222', userids=userids)
