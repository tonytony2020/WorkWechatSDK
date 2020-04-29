# About

A non-official WorkWeChat SDK in Pythonic Python.

非官方 Python 企业微信SDK 。

特点：

 - Pythonic
   - 没有异常就是 Keep It Simple Stupid ： 比如获取某个讨论组不存在的时候，返回 None 而不是抛出异常；
   - 可自定义官方接口 errcode 哪些情况抛出异常，哪些不抛出，具体见 SDK 中 `appchat_get` 函数实现；
   - 写/修改类操作，默认空返回表示成功；读类操作，默认返回空表示找不到相关资源对象；
 - 函数和参数命名尽可能和官方接口一直，比如 通讯录 创建成员 "/user/create" 对应 SDK 函数为 "user_create"；


## 接口完成度

前置接口

接口或模块 | 完成状态
------------ | -------------
获取access_token | 已完成
获取企业微信API域名IP段 | 已完成


通讯录管理

接口或模块 | 完成状态
------------ | -------------
成员管理 | 已完成
部门管理 | TBD.
标签管理 | TBD.
异步批量接口 | TBD.
开启通讯录回调通知 | TBD.


应用管理

接口或模块 | 完成状态
------------ | -------------
获取应用 | 已完成
设置应用 | TBD.
自定义菜单 | TBD.


消息推送

接口或模块 | 完成状态
------------ | -------------
发送应用消息 | 已完成
更新任务卡片消息状态 | 已完成
接收消息与事件 | TBD.
发送消息到群聊会话 | 已完成
互联企业消息推送 | TBD.
查询应用消息发送统计 | TBD.


其他

接口或模块 | 完成状态
------------ | -------------
群机器人 | 已完成
外部联系人管理 | TBD.
身份验证 | TBD.
素材管理 | TBD.
OA数据接口 | TBD.
日程 | TBD.
企业支付 | TBD.
电子发票 | TBD.


## 如何使用

通过 [pipenv](https://pipenv.kennethreitz.org/) 安装 WorkWeChatSDK

    pipenv install WorkWeChatSDK



注意：

官方文档中「通过 corpid、 corpidsecret 生成 access_token」，
corpsecret 其实是 自建或内置应用(agent) 对应的 Secret，起这个歧义名字会误导用户以为 corpidsecret 跟 corpid 对应；
因为 应用可以有多个，所以 corpidsecret 在不同的上下文应用中，可能是不同的值。


例子：创建自定义讨论群组

    import os

    import work_wechat

    corpid = os.environ.get("CORPID")
    corpsecret = os.environ.get("CORPSECRET")
    content = "hello world"

    ww = work_wechat.WorkWeChat(
        corpid=corpid,
        corpsecret=corpsecret,
        debug=True, # 打印请求 URL
        http_timeout=5,
    )

    # 可选，调用其他需要token的API时，会自动检测 token 是否存在、过期决定是否需要刷新
    token = ww.get_access_token()
    print('token=%s' % token)

    chatid = ww.appchat_create(
        userlist=("zhangsan", "lisi", "wangwu"),
        chatid="BigNewRoom",
        owner="zhangsan",
        name="搞个大新闻",
    )

注意：只允许企业自建应用调用「创建群聊会话」，且应用的可见范围必须是根部门；每企业创建群数不可超过1000/天。


例子：通过[群机器人](https://work.weixin.qq.com/api/doc/90000/90136/91770)推送信息

    import os

    import work_wechat

    webhook_key = os.environ.get("WEBHOOK_KEY")
    content = "hello world"

    work_wechat.WorkWeChat().webhook_send(
        key=webhook_key,
        content=content,
    )


异常处理

    import os

    import work_wechat

    webhook_key = os.environ.get("WEBHOOK_KEY")
    content = "hello world"

    try:
        work_wechat.WorkWeChat().webhook_send(
            key=webhook_key,
            content=content,
        )
    except work_wechat.WorkWeChatException as ex:
        # errcode 和 errmsg 分别对应接口响应中字段，ex.rs 为完整 HTTP response
        print(ex.errcode, ex.errmsg, ex.rs)

例子：发送图文信息https://work.weixin.qq.com/api/doc/90000/90135/90236

    import os

    import work_wechat
    
    corpid = os.environ.get("CORPID")
    corpsecret = os.environ.get("CORPSECRET")
    agentid = os.environ.get("agentid")

    def send_news_message():
        """发送图文信息"""
        
        news_articles1 = work_wechat.NewsArticle(
            picurl="http://wwcdn.weixin.qq.com/node/wwnl/wwnl/style/images/independent/favicon/favicon_48h$c976bd14.png",
            title="图文信息发送测试",
            ''''''
        )
        
        touser = 'Jense'
        
        ww.message_send(agentid=agentid, msgtype="news", touser=touser, news_articles=(news_articles1))
    
    
NewsArticle用于规范数据接口，其定义在__init__.py文件中，具体定义如下:
    
    class LikeDict(object):
        def __init__(self, **kwargs):
            self.update(**kwargs)
    
        def to_dict(self) -> dict:
            return dict((k, v) for k, v in self.__dict__.items() if not k.startswith("_"))
    
        def update(self, **kwargs):
            for k, v in kwargs.items():
                if k in self.__dict__:
                    self.__dict__[k] = v
                
    class NewsArticle(LikeDict):
        """ https://work.weixin.qq.com/help?doc_id=13376#图文类型 """

        def __init__(self, **kwargs):
        
            self.title = None
            self.description = None
            
            self.url = None
            self.picurl = None
            
            super().__init__(**kwargs)
    
例子： 发送卡片信息(https://work.weixin.qq.com/api/doc/90000/90135/90236)
    
    import os

    import work_wechat
    
    corpid = os.environ.get("CORPID")
    corpsecret = os.environ.get("CORPSECRET")
    agentid = os.environ.get("agentid")
    
    def send_file_message():
        """发送文件信息"""
        
        file_path = 'D:/'
        file_name = "啊.txt"
        
        media = work_wechat.Media(file_path=file_path, file_name=file_name, file_type='file')
        media_id = ww.media_upload(media=media)
        
        touser = 'Jense'
        
        ww.message_send(agentid=agentid, msgtype="file", touser=touser, media_id=media_id)
    
    


其他例子见目录 examples/ .
