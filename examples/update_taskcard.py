# encoding: utf-8
import os

import work_wechat
import time

corpid = os.environ.get("CORPID")
corpsecret = os.environ.get("CORPSECRET")
agentid = os.environ.get("agentid")

ww = work_wechat.WorkWeChat(corpid=corpid, corpsecret=corpsecret)

task_id = 'f6fsad'
task_card = dict(title="Jense的卡片更新测试申请", url="https://qyapi.weixin.qq.com", task_id=task_id,
                 description="目的：进行更新卡片<br>用途：进行工作 测试")

btn = [dict(key="key111", name="批准", replace_name="已批准", color="red", is_bold=True),
       dict(key="key222", name="驳回", replace_name="已驳回")]
task_card['btn'] = btn

# 发送任务卡片
ww.message_send(agentid=agentid, content=task_card, touser="Jense", msgtype="taskcard")

time.sleep(2)
userids = ['Jense']
ww.update_taskcard(agentid=agentid, task_id=task_id, clicked_key='key222', userids=userids)
