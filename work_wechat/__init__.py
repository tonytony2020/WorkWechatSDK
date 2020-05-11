import copy
import json
import logging
import time
import typing
import urllib.parse
import requests
import mimetypes


class LikeDict(object):
    def __init__(self, **kwargs):
        self.update(**kwargs)

    def to_dict(self) -> dict:
        return dict((k, v) for k, v in self.__dict__.items() if not k.startswith("_"))

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v


class ErrCode:
    ERROR = -1
    SUCCESS = 0

    INVALID_USERID_LIST = 40031
    INVALID_PARTY_LIST = 40066
    API_FORBIDDEN = 48002

    DEPARTMENT_NOT_FOUND = 60003
    NO_PRIVILEGE_TO_ACCESS_OR_MODIFY = 60011
    USERID_EXISTED = 60102
    USERID_NOT_FOUND = 60111
    INVALID_NAME = 60112

    CHATID_INVALID = 86001
    CHATID_EXISTED = 86215


class WorkWeChatException(Exception):
    def __init__(self, errcode: int, errmsg: str, rs: dict):
        self.errcode = errcode
        self.errmsg = errmsg
        self.rs = rs

    def __str__(self) -> str:
        return "%s" % self.rs


class QrCodeSizeType(object):
    SMALL = 1  # 171x171
    MEDIUM = 2  # 399x399
    LARGE = 3  # 741x741
    EXTRA_LARGE = 4  # 2052x2052


class MsgType:
    TEXT = "text"
    IMAGE = "image"

    FILE = "file"
    NEWS = "news"
    VIDEO = "video"
    VOICE = "voice"

    TEXTCARD = "textcard"
    MPNEWS = "mpnews"
    MARKDOWN = "markdown"
    TASKCARD = "taskcard"


MIMETYPE2WWTYPE = {

    "image/jpeg": "image",

    "audio/amr": "voice",

    "video/mp4": "video",

}

DEFAULT_CONTENT_TYPE = 'file'


class NewsArticle(LikeDict):
    """ https://work.weixin.qq.com/help?doc_id=13376#图文类型 """

    def __init__(self, **kwargs):
        self.title = None
        self.description = None

        self.url = None
        self.picurl = None

        super().__init__(**kwargs)


class Media(object):
    """https://work.weixin.qq.com/api/doc/90000/90135/90253#临时媒体类型"""

    def __init__(self, file_name: str, file_data: typing.BinaryIO):
        self.file_name = file_name
        self.file_data = file_data
        self.file_type = mimetypes.guess_type(file_name)[0]


class Video(LikeDict):
    """https://work.weixin.qq.com/api/doc/90000/90135/90236#视频类型"""

    def __init__(self, **kwargs):
        self.media_id = None
        self.title = None
        self.description = None

        super().__init__(**kwargs)


class TaskCardBtn(LikeDict):
    """https://work.weixin.qq.com/api/doc/90000/90135/90253#按键类型"""

    def __init__(self, **kwargs):
        self.key = None
        self.name = None

        self.replace_name = None
        self.color = None
        self.is_bold = None

        super().__init__(**kwargs)


class TextCard(LikeDict):
    """https://work.weixin.qq.com/api/doc/90000/90135/90236#文本卡片信息"""

    def __init__(self, **kwargs):
        self.title = None
        self.description = None

        self.url = None
        self.btntxt = None

        super().__init__(**kwargs)


class TaskCard(LikeDict):
    """https://work.weixin.qq.com/api/doc/90000/90135/90236#任务卡片信息"""

    def __init__(self, **kwargs):
        self.title = None
        self.description = None

        self.url = None
        self.btn = None
        self.task_id = None

        super().__init__(**kwargs)


class MpNew(LikeDict):
    """https://work.weixin.qq.com/api/doc/90000/90135/90236#图文信息(mpnews)"""

    def __init__(self, **kwargs):
        self.title = None
        self.thumb_media_id = None

        self.author = None
        self.content_source_url = None
        self.content = None
        self.digest = None

        super().__init__(**kwargs)


mimetypes.add_type("audio/amr", ".amr")


class WorkWeChat(object):

    def __init__(self, corpid: str = None, corpsecret: str = None, verbose: bool = False, http_timeout: int = 5):
        self._corpid = corpid
        self._corpsecret = corpsecret
        self._verbose = verbose

        self._url_prefix = "https://qyapi.weixin.qq.com/cgi-bin"
        self._http_timeout = http_timeout

        self._access_token_expires_in = 0
        self._access_token = None

    def _update_access_token(self):
        now = int(time.time())
        if not self._access_token or now > self._access_token_expires_in:
            rs = self.gettoken()

            self._access_token_expires_in = int(time.time()) + rs["expires_in"]
            self._access_token = rs["access_token"]

    def get_access_token(self) -> str:
        self._update_access_token()
        return self._access_token

    def _send_req(
            self,
            method: str,
            path: str,
            params_qs: dict = None,
            params_post: dict = None,
            errcodes_accepted: typing.Tuple[int, ...] = None,
            auto_update_token: bool = True,
    ) -> dict:
        if not errcodes_accepted:
            errcodes_accepted = (ErrCode.SUCCESS,)

        if not params_qs:
            params_qs = dict()

        if auto_update_token:
            params_qs["access_token"] = self.get_access_token()

        qs = urllib.parse.urlencode(params_qs)
        url = self._url_prefix + path + "?" + qs

        data_post = None
        if params_post:
            data_post = json.dumps(params_post)

        if self._verbose:
            logging.debug("%s %s" % (method, url))
        r = requests.request(method=method, url=url, timeout=self._http_timeout, data=data_post)
        assert r.status_code == 200, r.headers
        rs = r.json()
        if rs["errcode"] not in errcodes_accepted:
            raise WorkWeChatException(errcode=rs["errcode"], errmsg=rs["errmsg"], rs=rs)

        return rs

    def gettoken(self) -> dict:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/91039
        """
        params_qs = dict(
            corpid=self._corpid,
            corpsecret=self._corpsecret,
        )
        qs = urllib.parse.urlencode(params_qs)
        url = self._url_prefix + "/gettoken?" + qs
        r = requests.get(url=url, timeout=self._http_timeout)
        rs = r.json()
        assert rs["errcode"] == ErrCode.SUCCESS
        """
        {
           "errcode": 0,
           "errmsg": "ok",
           "access_token": "accesstoken000001",
           "expires_in": 7200
        }
        """
        return dict(
            access_token=rs["access_token"],
            expires_in=rs["expires_in"],
        )

    def get_api_domain_ip(self) -> typing.List[str]:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/92520
        """

        rs = self._send_req(
            method="GET",
            path="/get_api_domain_ip",
        )
        """
        {
            "ip_list":[
                "182.254.11.176",
                "182.254.78.66"
            ],
            "errcode":0,
            "errmsg":"ok"
        }
        """
        return rs["ip_list"]

    def appchat_get(self, chatid: str) -> typing.Optional[dict]:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90247
        """

        params_qs = dict(chatid=chatid)
        errcodes_accepted = (ErrCode.SUCCESS, ErrCode.CHATID_INVALID)
        rs = self._send_req(
            method="GET",
            path="/appchat/get",
            params_qs=params_qs,
            errcodes_accepted=errcodes_accepted,
        )
        """
         {
           "errcode" : 0,
           "errmsg" : "ok"
           "chat_info" : {
              "chatid" : "CHATID",
              "name" : "NAME",
              "owner" : "userid2",
              "userlist" : ["userid1", "userid2", "userid3"]
           }
         }
        """
        return rs["chat_info"]

    def appchat_send(self, chatid: str, content: str):
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90248
        """
        data = dict(
            chatid=chatid,
            msgtype="text",
            text=dict(
                content=content,
            ),
            safe=0,
        )

        self._send_req(method="POST", path="/appchat/send", params_post=data)
        """
         {
           "errcode" : 0,
           "errmsg" : "ok",
         }
        """

    def appchat_create(
            self,
            userlist: typing.Tuple[str, ...],
            chatid: str = None,
            owner: str = None,
            name: str = None,
    ) -> str:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90245
        """
        data = dict(
            userlist=userlist,
        )
        if chatid:
            data["chatid"] = chatid
        if owner:
            data["owner"] = owner
        if name:
            data["name"] = name

        errcodes_accepted = (ErrCode.SUCCESS, ErrCode.CHATID_EXISTED)
        rs = self._send_req(
            method="POST",
            path="/appchat/create",
            params_post=data,
            errcodes_accepted=errcodes_accepted,
        )
        """
         {
           "errcode" : 0,
           "errmsg" : "ok",
           "chatid" : "CHATID"
         }
         """

        if rs["errcode"] == ErrCode.CHATID_EXISTED:
            return chatid

        return rs["chatid"]

    def appchat_update(
            self, chatid: str,
            name: str = None,
            owner: str = None,
            add_user_list: typing.Set[str] = None,
            del_user_list: typing.Set[str] = None,
    ):
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90246
        """

        data = dict(chatid=chatid)

        if name is not None:
            data["name"] = name
        if owner is not None:
            data["owner"] = owner
        if add_user_list is not None:
            data["add_user_list"] = list(add_user_list)
        if del_user_list is not None:
            data["del_user_list"] = list(del_user_list)

        self._send_req(method="POST", path="/appchat/update", params_post=data)
        """
         {
           "errcode" : 0,
           "errmsg" : "ok"
         }

        """

    def webhook_send(
            self,
            key: str,
            text_content: str = None,
            markdown_content: str = None,
            image_base64: str = None,
            image_md5: str = None,
            news_articles: typing.List[NewsArticle] = None,
            mentioned_list: typing.List[str] = None,
            mentioned_mobile_list: typing.List[str] = None,
    ):
        """
        https://work.weixin.qq.com/help?doc_id=13376
        """
        if key.startswith("https"):
            # user pass a url such as "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
            key = key.split("key=")[-1]

        data_qs = dict(
            key=key,
        )

        data_post = dict()
        if text_content:
            data_post["msgtype"] = "text"
            data_post["text"] = dict(
                content=text_content,
            )
            if mentioned_list:
                data_post["text"]["mentioned_list"] = mentioned_list
            if mentioned_mobile_list:
                data_post["text"]["mentioned_mobile_list"] = mentioned_mobile_list

        if markdown_content:
            data_post["msgtype"] = "markdown"
            data_post["markdown"] = dict(
                content=markdown_content,
            )
        if image_base64 and image_md5:
            data_post["msgtype"] = "image"
            data_post["image"] = dict(
                base64=image_base64,
                md5=image_md5,
            )
        if news_articles:
            data_post["msgtype"] = "news"
            data_post["news"] = dict(articles=[i.to_dict() for i in news_articles])

        self._send_req(
            auto_update_token=False,
            method="POST",
            path="/webhook/send",
            params_qs=data_qs,
            params_post=data_post,
        )

    def agent_get(
            self,
            agentid: int,
    ) -> dict:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90227
        """
        data_qs = dict(agentid=agentid)
        rs = self._send_req(method="POST", path="/agent/get", params_qs=data_qs)
        """
        {
           "errcode": 0,
           "errmsg": "ok",
           "agentid": 1000005,
           "name": "HR助手",
           "square_logo_url":  "https://p.qlogo.cn/bizmail/FicwmI50icF8GH9ib7rUAYR5kicLTgP265naVFQKnleqSlRhiaBx7QA9u7Q/0",
           "description": "HR服务与员工自助平台",
           "allow_userinfos": {
               "user": [
                     {"userid": "zhangshan"},
                     {"userid": "lisi"}
               ]
            },
           "allow_partys": {
               "partyid": [1]
            },
           "allow_tags": {
               "tagid": [1,2,3]
            },
           "close": 0,
           "redirect_domain": "open.work.weixin.qq.com",
           "report_location_flag": 0,
           "isreportenter": 0,
           "home_url": "https://open.work.weixin.qq.com"
        }
        """
        rs = copy.deepcopy(rs)
        for i in (
                "errcode",
                "errmsg",
        ):
            rs.pop(i)
        return rs

    def _drop_fields(self, rs: dict, fields=None) -> dict:
        fields_default = (
            "errcode",
            "errmsg",
        )
        if not fields:
            fields = fields_default
        rs = copy.deepcopy(rs)
        for i in fields:
            try:
                rs.pop(i)
            except KeyError:
                pass
            return rs

    def user_get(self, userid: str) -> typing.Optional[dict]:
        """
        注意：在通讯录同步助手中此接口可以读取企业通讯录的所有成员信息，而自建应用可以读取该应用设置的可见范围内的成员信息。
        https://open.work.weixin.qq.com/api/doc/90000/90135/90196
        """
        data_qs = dict(
            userid=userid,
        )
        errcodes_accepted = (ErrCode.SUCCESS, ErrCode.USERID_NOT_FOUND)
        rs = self._send_req(
            method="GET",
            path="/user/get",
            params_qs=data_qs,
            errcodes_accepted=errcodes_accepted,
        )
        if rs["errcode"] == ErrCode.USERID_NOT_FOUND:
            return
        """
        {
            "errcode": 0,
            "errmsg": "ok",
            "userid": "zhangsan",
            "name": "李四",
            "department": [1, 2],
            "order": [1, 2],
            "position": "后台工程师",
            "mobile": "13800000000",
            "gender": "1",
            "email": "zhangsan@gzdev.com",
            "is_leader_in_dept": [1, 0],
            "avatar": "http://wx.qlogo.cn/mmopen/ajNVdqHZLLA3WJ6DSZUfiakYe37PKnQhBIeOQBO4czqrnZDS79FH5Wm5m4X69TBicnHFlhiafvDwklOpZeXYQQ2icg/0",
            "thumb_avatar": "http://wx.qlogo.cn/mmopen/ajNVdqHZLLA3WJ6DSZUfiakYe37PKnQhBIeOQBO4czqrnZDS79FH5Wm5m4X69TBicnHFlhiafvDwklOpZeXYQQ2icg/100",
            "telephone": "020-123456",
            "alias": "jackzhang",
            "address": "广州市海珠区新港中路",
            "open_userid": "xxxxxx",
            "main_department": 1,
            "extattr": {
                "attrs": [
                    {
                        "type": 0,
                        "name": "文本名称",
                        "text": {
                            "value": "文本"
                        }
                    },
                    {
                        "type": 1,
                        "name": "网页名称",
                        "web": {
                            "url": "http://www.test.com",
                            "title": "标题"
                        }
                    }
                ]
            },
            "status": 1,
            "qr_code": "https://open.work.weixin.qq.com/wwopen/userQRCode?vcode=xxx",
            "external_position": "产品经理",
            "external_profile": {
                "external_corp_name": "企业简称",
                "external_attr": [{
                        "type": 0,
                        "name": "文本名称",
                        "text": {
                            "value": "文本"
                        }
                    },
                    {
                        "type": 1,
                        "name": "网页名称",
                        "web": {
                            "url": "http://www.test.com",
                            "title": "标题"
                        }
                    },
                    {
                        "type": 2,
                        "name": "测试app",
                        "miniprogram": {
                            "appid": "wx8bd80126147dFAKE",
                            "pagepath": "/index",
                            "title": "my miniprogram"
                        }
                    }
                ]
            }
        }        
        """
        rs = copy.deepcopy(rs)
        for i in (
                "errcode",
                "errmsg",
        ):
            rs.pop(i)
        return rs

    def user_create(
            self,
            userid: str,
            name: str,
            department: typing.List[int],
            is_leader_in_dept: typing.List[int],
            mobile: str = None,
            email: str = None,
            **kwargs
    ):
        """
        注意：
        1.需要修改 管理工具-通讯录同步-权限 「只读」为「编辑」 https://work.weixin.qq.com/wework_admin/frame#apps/contactsApi；
        2. 截止 2020-04-20 文档 https://work.weixin.qq.com/api/doc/90000/90135/90195 中 department 和 is_leader_in_dept 参数为非必填，实际是必填。

        https://work.weixin.qq.com/api/doc/90000/90135/90195
        """
        assert mobile or email
        assert len(department) == len(is_leader_in_dept)

        params_post = dict(
            userid=userid,
            name=name,
            department=department,
            is_leader_in_dept=is_leader_in_dept,
        )
        if mobile:
            params_post["mobile"] = mobile
        if email:
            params_post["email"] = email
        params_post.update(**kwargs)

        errcodes_accepted = (ErrCode.SUCCESS, ErrCode.USERID_EXISTED)

        self._send_req(
            method="POST",
            path="/user/create",
            params_post=params_post,
            errcodes_accepted=errcodes_accepted,
        )
        """
        {
           "errcode": 0,
           "errmsg": "created"
        }
        """

    def user_update(self, userid: str, **kwargs):
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90197
        """
        params_post = dict(
            userid=userid,
        )
        params_post.update(**kwargs)
        self._send_req(
            method="POST",
            path="/user/update",
            params_post=params_post,
        )
        """
        {
           "errcode": 0,
           "errmsg": "updated"
        }        
        """

    def user_delete(self, userid: str):
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90198
        """
        params_qs = dict(
            userid=userid,
        )
        self._send_req(
            method="GET",
            path="/user/delete",
            params_qs=params_qs,
        )
        """
        {
           "errcode": 0,
           "errmsg": "deleted"
        }
        """

    def user_batchdelete(self, useridlist: typing.List[str]):
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90199
        """
        params_post = dict(
            useridlist=useridlist,
        )
        self._send_req(
            method="POST",
            path="/user/batchdelete",
            params_post=params_post,
        )
        """
        {
           "errcode": 0,
           "errmsg": "deleted"
        }
        """

    def user_simplelist(
            self,
            department_id: int,
            fetch_child: bool = False
    ) -> typing.Optional[typing.List[dict]]:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90200
        """
        data = dict(
            department_id=department_id,
            fetch_child=int(fetch_child),
        )
        rs = self._send_req(method="GET", path="/user/simplelist", params_qs=data)
        """
        {
           "errcode": 0,
           "errmsg": "ok",
           "userlist": [
                   {
                          "userid": "zhangsan",
                          "name": "李四",
                          "department": [1, 2],
                          "open_userid": "xxxxxx"
                   }
             ]
        }        
        """
        return rs["userlist"]

    def user_list(
            self,
            department_id: int,
            fetch_child: bool = False
    ) -> typing.Optional[typing.List[dict]]:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90201
        """
        data = dict(
            department_id=department_id,
            fetch_child=int(fetch_child),
        )
        rs = self._send_req(method="GET", path="/user/list", params_qs=data)
        """
        {
            "errcode": 0,
            "errmsg": "ok",
            "userlist": [{
                "userid": "zhangsan",
                "name": "李四",
                "department": [1, 2],
                "order": [1, 2],
                "position": "后台工程师",
                "mobile": "13800000000",
                "gender": "1",
                "email": "zhangsan@gzdev.com",
                "is_leader_in_dept": [1, 0],
                "avatar": "http://wx.qlogo.cn/mmopen/ajNVdqHZLLA3WJ6DSZUfiakYe37PKnQhBIeOQBO4czqrnZDS79FH5Wm5m4X69TBicnHFlhiafvDwklOpZeXYQQ2icg/0",
                "thumb_avatar": "http://wx.qlogo.cn/mmopen/ajNVdqHZLLA3WJ6DSZUfiakYe37PKnQhBIeOQBO4czqrnZDS79FH5Wm5m4X69TBicnHFlhiafvDwklOpZeXYQQ2icg/100",
                "telephone": "020-123456",
                "alias": "jackzhang",
                "status": 1,
                "address": "广州市海珠区新港中路",
                "hide_mobile" : 0,
                "english_name" : "jacky",
                "open_userid": "xxxxxx",
                "main_department": 1,
                "extattr": {
                    "attrs": [
                        {
                            "type": 0,
                            "name": "文本名称",
                            "text": {
                                "value": "文本"
                            }
                        },
                        {
                            "type": 1,
                            "name": "网页名称",
                            "web": {
                                "url": "http://www.test.com",
                                "title": "标题"
                            }
                        }
                    ]
                },
                "qr_code": "https://open.work.weixin.qq.com/wwopen/userQRCode?vcode=xxx",
                "external_position": "产品经理",
                "external_profile": {
                    "external_corp_name": "企业简称",
                    "external_attr": [{
                            "type": 0,
                            "name": "文本名称",
                            "text": {
                                "value": "文本"
                            }
                        },
                        {
                            "type": 1,
                            "name": "网页名称",
                            "web": {
                                "url": "http://www.test.com",
                                "title": "标题"
                            }
                        },
                        {
                            "type": 2,
                            "name": "测试app",
                            "miniprogram": {
                                "appid": "wx8bd80126147dFAKE",
                                "pagepath": "/index",
                                "title": "miniprogram"
                            }
                        }
                    ]
                }
            }]
        }
        """
        return rs["userlist"]

    def user_convert_to_openid(self, userid: str) -> str:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90202
        """
        params_qs = dict(
            userid=userid,
        )
        rs = self._send_req(method="POST", path="/user/convert_to_openid", params_qs=params_qs)
        """
        {
           "errcode": 0,
           "errmsg": "ok",
           "openid": "oDjGHs-1yCnGrRovBj2yHij5JAAA"
        }
        """
        return rs["openid"]

    def user_convert_to_userid(self, openid: str) -> str:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90202
        """
        params_qs = dict(
            openid=openid,
        )
        rs = self._send_req(method="POST", path="/user/convert_to_openid", params_qs=params_qs)
        """
        {
           "errcode": 0,
           "errmsg": "ok",
           "userid": "zhangsan"
        }
        """
        return rs["userid"]

    def user_authsucc(self, userid: str):
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90203
        """
        params_qs = dict(
            userid=userid,
        )
        self._send_req(method="POST", path="/user/authsucc", params_qs=params_qs)
        """
        {
           "errcode": 0,
           "errmsg": "ok"
        }
        """

    def batch_invite(
            self,
            user: typing.List[str] = None,
            party: typing.List[int] = None,
            tag: typing.List[str] = None
    ):
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90975
        """
        maxItem = 1000
        assert user or party or tag

        params_post = dict()
        if user:
            assert len(user) < maxItem
            params_post["user"] = user
        if party:
            assert len(party) < maxItem
            params_post["party"] = party
        if tag:
            assert len(tag) < maxItem
            params_post["tag"] = tag

        rs = self._send_req(method="POST", path="/batch/invite", params_post=params_post)
        """
         {
           "errcode" : 0,
           "errmsg" : "ok",
           "invaliduser" : ["UserID1", "UserID2"],
           "invalidparty" : [PartyID1, PartyID2],
           "invalidtag": [TagID1, TagID2]
         }
        """
        rs = copy.deepcopy(rs)
        for i in (
                "errcode",
                "errmsg",
        ):
            rs.pop(i)
        return rs

    def corp_get_join_qrcode(self, size_type: int = None) -> str:
        """
        注意：须拥有通讯录的管理权限，使用通讯录同步的Secret。

        https://work.weixin.qq.com/api/doc/90000/90135/91714
        """
        params_qs = dict()
        if size_type:
            params_qs["size_type"] = size_type
        rs = self._send_req(method="GET", path="/corp/get_join_qrcode", params_qs=params_qs)
        """
        {
           "errcode": 0,
           "errmsg": "ok",
           "join_qrcode": "https://work.weixin.qq.com/wework_admin/genqrcode?action=join&vcode=3db1fab03118ae2aa1544cb9abe84&r=hb_share_api_mjoin&qr_size=3"
        }
        """
        return rs["join_qrcode"]

    def user_get_mobile_hashcode(self, mobile: str, state: str = None) -> str:
        """
        注意：仅限自建应用调用。
        https://work.weixin.qq.com/api/doc/90000/90135/91735
        """
        params_post = dict(
            mobile=mobile,
        )
        if state:
            params_post["state"] = state
        rs = self._send_req(method="POST", path="/user/get_mobile_hashcode", params_post=params_post)
        """
        {
           "errcode": 0,
           "errmsg": "ok",
           "hashcode": "1abcd2xaba3dxab4sdxa"
        }
        """
        return rs["hashcode"]

    def user_get_active_stat(self, date: str) -> int:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/92714
        """
        params_post = dict(
            date=date,
        )
        rs = self._send_req(method="POST", path="/user/get_active_stat", params_post=params_post)
        """
        {
           "errcode": 0,
           "errmsg": "ok",
           "active_cnt": 100
        }
        """
        return rs["active_cnt"]

    def media_upload(self, media: Media) -> str:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/90253
        """
        params_qs = dict(type=MIMETYPE2WWTYPE.get(media.file_type, DEFAULT_CONTENT_TYPE))

        """
        POST https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token=accesstoken001&type=file HTTP/1.1
        Content-Type: multipart/form-data; boundary=-------------------------acebdf13572468
        Content-Length: 220
        ---------------------------acebdf13572468
        Content-Disposition: form-data; name="media";filename="wework.txt"; filelength=6
        Content-Type: application/octet-stream
        mytext
        ---------------------------acebdf13572468--

        """
        params_qs["access_token"] = self.get_access_token()
        qs = urllib.parse.urlencode(params_qs)
        url = self._url_prefix + "/media/upload" + "?" + qs
        files = {
            "media": (media.file_name, media.file_data, media.file_data)
        }
        r = requests.post(
            url=url,
            files=files,
        )
        """
        {
           "errcode": 0,
           "errmsg": ""，
           "type": "image",
           "media_id": "1G6nrLmr5EC3MMb_-zK1dDdzmd0p7cNliYu9V5w7o8K0",
           "created_at": "1380000000"
        }
        """
        rs = r.json()

        if rs["errcode"] is not ErrCode.SUCCESS:
            raise WorkWeChatException(errcode=rs["errcode"], errmsg=rs["errmsg"], rs=rs)

        return rs['media_id']

    def message_send(
            self,
            msgtype: str,
            agentid: int,
            content: str = None,
            media_id: str = None,
            video: Video = None,
            textcard: TextCard = None,
            news_articles: typing.Tuple[NewsArticle, ...] = None,
            mpnews_articles: typing.Tuple[MpNew, ...] = None,
            taskcard: TaskCard = None,
            touser: typing.Tuple[str, ...] = None,
            toparty: str = None,
            totag: str = None,
            safe: int = 0,
            enable_id_trans: int = 0,
            enable_duplicate_check: int = 0,
            duplicate_check_interval: int = 1800
    ) -> str:

        """
        https://work.weixin.qq.com/api/doc/90000/90135/90236
        """
        data = dict(
            msgtype=msgtype,
            agentid=agentid,
            enable_duplicate_check=enable_duplicate_check,
            enable_id_trans=enable_id_trans,
            duplicate_check_interval=duplicate_check_interval,
            safe=safe
        )

        object_type_dict = dict(
            news=news_articles,
            video=video,
            textcard=textcard,
            mpnews=mpnews_articles,
            taskcard=taskcard
        )

        if msgtype == MsgType.TEXT or msgtype == MsgType.MARKDOWN:
            data[msgtype] = dict(content=content)
        elif msgtype == MsgType.FILE or msgtype == MsgType.IMAGE or msgtype == MsgType.VOICE:
            data[msgtype] = dict(media_id=media_id)
        elif msgtype == MsgType.NEWS or msgtype == MsgType.MPNEWS:
            data[msgtype] = dict(articles=[i.to_dict() for i in object_type_dict[msgtype]])
        else:
            data[msgtype] = object_type_dict[msgtype].to_dict()

        if touser:
            user = [user + '|' for user in touser]
            data["touser"] = ''.join(user)
        if toparty:
            data["toparty"] = toparty
        if totag:
            data["totag"] = totag
        """
        {
           "touser" : "UserID1|UserID2|UserID3",
           "toparty" : "PartyID1|PartyID2",
           "totag" : "TagID1 | TagID2",
           "msgtype" : "text",
           "agentid" : 1,
           "text" : {
               "content" : "你的快递已到，请携带工卡前往邮件中心领取。\n出发前可查看<a href=\"http://work.weixin.qq.com\">邮件中心视频实况</a>，聪明避开排队。"
           },
           "safe":0,
           "enable_id_trans": 0,
           "enable_duplicate_check": 0,
           "duplicate_check_interval": 1800
        }
        """

        rs = self._send_req(
            method="POST",
            path="/message/send",
            params_post=data,
        )
        """
         {
           "errcode" : 0,
           "errmsg" : "ok",
           "invaliduser" : "userid1|userid2",
           "invalidparty" : "partyid1|partyid2",
           "invalidtag": "tagid1|tagid2"
         }
        """

        return rs["invaliduser"]

    def update_taskcard(
            self,
            userids: typing.Tuple[str, ...],
            agentid: int,
            task_id: str,
            clicked_key: str
    ) -> typing.List[str]:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/91579
        """
        params_post = dict(userids=userids, agentid=agentid, task_id=task_id, clicked_key=clicked_key)
        errcodes_accepted = (ErrCode.SUCCESS, ErrCode.CHATID_INVALID)
        """
        {
            "userids" : ["userid1","userid2"],
            "agentid" : 1,
            "task_id": "taskid122",
            "clicked_key": "btn_key123"
        }   
        """
        rs = self._send_req(
            method="POST",
            path="/message/update_taskcard",
            params_post=params_post,
            errcodes_accepted=errcodes_accepted,
        )
        """
         {
           "errcode" : 0,
           "errmsg" : "ok",
           "invaliduser" : ["userid1","userid2"], // 不区分大小写，返回的列表都统一转为小写
         }
        """
        return rs["invaliduser"]

    def message_get_statistics(self, time_type: int = 0) -> typing.List[dict]:
        """
        https://work.weixin.qq.com/api/doc/90000/90135/92369
        """
        params_post = dict(time_type=time_type)

        """
        {
           "time_type": 0
        }
        """
        rs = self._send_req(
            method="POST",
            path="/message/get_statistics",
            params_post=params_post
        )
        """
        {
           "errcode" : 0,
           "errmsg" : "ok",
           "statistics": [
               {
                    "agentid": 1000002,
                   "app_name": "应用1",
                   "count": 101
               }，
               {
                   "agentid": 1000003,
                   "app_name": "应用2",
                   "count": 102
               }
           ]
        }
        """
        return rs["statistics"]
