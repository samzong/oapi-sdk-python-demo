"""
发送图片消息，使用到两个OpenAPI：
1. [上传图片](https://open.feishu.cn/document/server-docs/im-v1/image/create)
2. [发送消息](https://open.feishu.cn/document/server-docs/im-v1/message/create)
"""

import lark_oapi as lark
from lark_oapi.api.im.v1 import *


class SendImageRequest(object):

    def __init__(self) -> None:
        self.image: Optional[IO[Any]] = None  # 图片，必填
        self.receive_id_type: Optional[str] = None  # 消息接收者ID类型，必填
        self.receive_id: Optional[str] = None  # 消息接收者的ID，必填
        self.uuid: Optional[str] = None  # 消息uuid，选填


class SendImageResponse(BaseResponse):
    def __init__(self) -> None:
        super().__init__()
        self.create_image_response: Optional[CreateImageResponseBody] = None
        self.create_message_response: Optional[CreateMessageResponseBody] = None

# 异常处理
def handle_api_response(response: BaseResponse) -> BaseResponse:
    if not response.success():
        lark.logger.error(
            f"API call failed, "
            f"code: {response.code}, "
            f"msg: {response.msg}, "
            f"log_id: {response.get_log_id()}")
    return response

# 发送图片消息
def send_image(client: lark.Client, request: SendImageRequest) -> BaseResponse:
    # 上传图片
    create_image_req = CreateImageRequest.builder() \
        .request_body(CreateImageRequestBody.builder()
                      .image_type("message")
                      .image(request.image)
                      .build()) \
        .build()

    create_image_resp = client.im.v1.image.create(create_image_req)

    if not create_image_resp.success():
        return create_image_resp

    # 发送消息
    option = lark.RequestOption.builder().headers({"X-Tt-Logid": create_image_resp.get_log_id()}).build()
    create_message_req = CreateMessageRequest.builder() \
        .receive_id_type(request.receive_id_type) \
        .request_body(CreateMessageRequestBody.builder()
                      .receive_id(request.receive_id)
                      .msg_type("image")
                      .content(lark.JSON.marshal(create_image_resp.data))
                      .uuid(request.uuid)
                      .build()) \
        .build()

    create_message_resp: CreateMessageResponse = client.im.v1.message.create(create_message_req, option)

    if not create_message_resp.success():
        return create_message_resp

    # 返回结果
    response = SendImageResponse()
    response.code = 0
    response.msg = "success"
    response.create_image_response = create_image_resp.data
    response.create_message_response = create_message_resp.data

    return response
