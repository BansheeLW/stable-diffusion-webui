import json
import string

import boto3
import base64
import traceback

from modules.api.models import InvocationsRequest, InvocationsErrorResponse


class PostHook:
    """
    推理产生结果后的回调用通知类
    """

    def __init__(self):
        super()

    def text_to_image_hook(self, req: InvocationsRequest, images: list) -> str:
        """
        将text_to_image task产生的结果转换为回调消息
        Args:
            req: request
            images: 单次task产生的一批图片在S3上的位置的列表
        Returns: 可传输的回调消息通知

        """
        if isinstance(images, list):
            message = {
                "task": req.task,
                "id": req.id,
                "model": req.model,
                "vae": req.vae,
                "quality": req.quality,
                "options": req.options,
                "images": images
            }
        else:
            message = {
                "task": req.task,
                "id": req.id,
                "model": req.model,
                "vae": req.vae,
                "quality": req.quality,
                "options": req.options,
                "images": None,
                "reason": "the images is None or the image is a Base64 stream"
            }
        message = json.dumps(message)
        self._to_sqs(message)

        return json.dumps(message)

    def image_to_image_hook(self, req: InvocationsRequest, images: list) -> str:
        """
        将image_to_image task产生的结果转换为回调消息
        Args:
            req: request
            images: 单次image_to_image task产生的一批图片在S3上的位置的列表
        Returns: 可传输的回调消息通知

        """

        # 暂时逻辑和text_to_image一样，后续可能变动
        message = self.text_to_image_hook(req, images)

        return message

    def extras_single_image_hook(self, req: InvocationsRequest, image: str) -> str:
        """
         将extras_single_image task产生的结果转换为回调消息
         Args:
             req: request
             image: 单次extras_single_image task产生的一张图片在S3上的位置的列表
         Returns: 可传输的回调消息通知
         """
        if isinstance(image, str):
            images = [image, ]
            # 暂时逻辑和text_to_image一样，后续可能变动
            message = self.text_to_image_hook(req, images)
        else:
            message = {
                "task": req.task,
                "id": req.id,
                "model": req.model,
                "vae": req.vae,
                "quality": req.quality,
                "options": req.options,
                "images": None,
                "reason": "extras_single_image_hook: the images is None or the image is a Base64 stream"
            }
            message = json.dumps(message)

        self._to_sqs(message)
        # 暂时逻辑和text_to_image一样，后续可能变动
        return message

    def extras_batch_images_hook(self, req: InvocationsRequest, images: list) -> str:
        """
         将extras_batch_images task产生的结果转换为回调消息
         Args:
             req: request
             images: 单次extras_batch_images task产生的一批图片在S3上的位置的列表
         Returns: 可传输的回调消息通知

         """

        # 暂时逻辑和text_to_image一样，后续可能变动
        message = self.text_to_image_hook(req, images)
        self._to_sqs(message)

        return self.text_to_image_hook(req, images)

    def interrogate_hook(self, req: InvocationsRequest, images: list) -> str:
        # 暂时逻辑和text_to_image一样，后续可能变动
        message = self.text_to_image_hook(req, images)
        self._to_sqs(message)

        return message

    def invalid_task_hook(self, req: InvocationsRequest, response: InvocationsErrorResponse) -> str:
        """
         将invalid task产生的不合法结果
         Args:
             req: request
             response: 单次task产生的不合法结果信息
         Returns: 可传输的回调消息通知

         """
        message = {
            "task": req.task,
            "id": req.id,
            "model": req.model,
            "vae": req.vae,
            "quality": req.quality,
            "options": req.options,
            "images": None,
            "reason": f"invalid_task_hook: {response.error}"
        }
        message = json.dumps(message)
        self._to_sqs(message)

        return message

    def exception_task_hook(self, req: InvocationsRequest, e: Exception) -> str:
        """
         将exception task产生的异常结果
         Args:
             req: request
             e: 单次task产生的异常结果信息
         Returns: 可传输的回调消息通知

         """
        message = {
            "task": req.task,
            "id": req.id,
            "model": req.model,
            "vae": req.vae,
            "quality": req.quality,
            "options": req.options,
            "images": None,
            "reason": f"exception_task_hook: {traceback.format_exc()}"
        }
        message = json.dumps(message)
        self._to_sqs(message)

        return message

    def _to_sqs(self, message: str, queue_url: string = ""):
        """
        通过SQS发生task回执

        Args:
            quque_url: SQS 队列URL
        Returns:
        """
        if not queue_url:
            # todo 这里要指定aws region和aws account
            region = "us-west-2"
            account = "022637123599"
            # queue_url：f"https://sqs.{region}.amazonaws.com/{account}/sagemaker-hook"
            queue_url = f"https://sqs.{region}.amazonaws.com/{account}/aigc_prod"

        payload_bytes = message.encode('utf-8')
        payload_base64 = base64.b64encode(payload_bytes)
        real_message = {
            "biz_type": 0,
            "topic": "inference_completed",
            "metadata": {},
            "payload": payload_base64.decode('utf-8'),
            "queue_tag": -1,
            "key": "",
        }
        real_message = json.dumps(real_message)

        client = boto3.client('sqs')
        response = client.send_message(QueueUrl=queue_url, MessageBody=real_message)
        return response

    def _to_http_endpoint(self):
        """
        通过HTTP endpoint发生task回执
        Returns:
        """
        pass
