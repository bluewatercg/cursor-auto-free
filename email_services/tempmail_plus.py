from .base import EmailServiceBase
from .utils import EmailGenerator
import requests
import re
import time
import logging

class TempMailPlusService(EmailServiceBase):
    def __init__(self, config: dict):
        self.username = EmailGenerator.generate_random_name()
        self.epin = config["epin"]
        self.extension = config["extension"]
        self.session = requests.Session()
        
    def get_verification_code(self) -> str:
        """获取验证码"""
        try:
            # 等待并获取最新邮件
            code, first_id = self._get_latest_mail_code()
            if code:
                # 清理邮件
                self.cleanup(first_id)
            return code
        except Exception as e:
            logging.error(f"获取验证码失败: {str(e)}")
            return None
        
    def cleanup(self, mail_id: str) -> bool:
        """清理邮件"""
        # 构造删除请求的URL和数据
        delete_url = "https://tempmail.plus/api/mails/"
        payload = {
            "email": self.get_email_address(),
            "first_id": mail_id,
            "epin": self.epin,
        }

        # 最多尝试5次
        for _ in range(5):
            try:
                response = self.session.delete(delete_url, data=payload)
                result = response.json().get("result")
                if result is True:
                    return True
            except Exception as e:
                logging.error(f"删除邮件失败: {str(e)}")
            # 如果失败,等待0.5秒后重试
            time.sleep(0.5)

        return False
        
    def get_email_address(self) -> str:
        """获取完整邮箱地址"""
        return f"{self.username}{self.extension}"
        
    def _get_latest_mail_code(self) -> tuple[str, str]:
        """获取最新邮件的验证码
        
        Returns:
            tuple: (验证码, 邮件ID)
        """
        # 获取邮件列表
        mail_list_url = (
            f"https://tempmail.plus/api/mails?"
            f"email={self.get_email_address()}&limit=20&epin={self.epin}"
        )
        mail_list_response = self.session.get(mail_list_url)
        mail_list_data = mail_list_response.json()
        time.sleep(0.5)
        
        if not mail_list_data.get("result"):
            return None, None

        # 获取最新邮件的ID
        first_id = mail_list_data.get("first_id")
        if not first_id:
            return None, None

        # 获取具体邮件内容
        mail_detail_url = (
            f"https://tempmail.plus/api/mails/{first_id}?"
            f"email={self.get_email_address()}&epin={self.epin}"
        )
        mail_detail_response = self.session.get(mail_detail_url)
        mail_detail_data = mail_detail_response.json()
        time.sleep(0.5)
        
        if not mail_detail_data.get("result"):
            return None, None

        # 从邮件文本中提取6位数字验证码
        mail_text = mail_detail_data.get("text", "")
        # 确保6位数字不紧跟在字母或域名相关符号后面
        code_match = re.search(r"(?<![a-zA-Z@.])\b\d{6}\b", mail_text)

        if code_match:
            return code_match.group(), first_id
        return None, None 