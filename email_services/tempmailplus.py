from .base import EmailServiceBase
import requests
import re
import time
import logging

class TempMailPlusService(EmailServiceBase):
    """TempMail Plus 邮件服务实现"""
    
    def __init__(self, config: dict):
        """
        初始化 TempMail Plus 服务
        
        Args:
            config: 配置信息，包含:
                - epin: TempMail Plus 的 EPIN
                - extension: 邮箱后缀，如 @mailto.plus
                - username: TempMail Plus 的用户名
        """
        self.epin = config["epin"]
        self.extension = config["extension"]
        self.username = config["username"]  # 移除默认值
        self.session = requests.Session()
        
    def set_email_address(self, email: str):
        """设置要使用的邮箱地址"""
        self.email_address = email
        
    def get_email_address(self) -> str:
        """获取当前使用的邮箱地址"""
        if not self.email_address:
            raise ValueError("邮箱地址未设置")
        return self.email_address
        
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
        delete_url = "https://tempmail.plus/api/mails/"
        payload = {
            "email": f"{self.username}{self.extension}",
            "first_id": mail_id,
            "epin": self.epin,
        }

        for _ in range(5):
            try:
                response = requests.delete(delete_url, data=payload)
                if response.json().get("result") is True:
                    return True
            except Exception as e:
                logging.error(f"删除邮件失败: {str(e)}")
            time.sleep(0.5)

        return False
        
    def _get_latest_mail_code(self) -> tuple[str, str]:
        """获取最新邮件的验证码
        
        Returns:
            tuple: (验证码, 邮件ID)
        """
        # 获取邮件列表
        mail_list_url = (
            f"https://tempmail.plus/api/mails?"
            f"email={self.username}{self.extension}&limit=20&epin={self.epin}"
        )
        mail_list_response = requests.get(mail_list_url)
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
            f"email={self.username}{self.extension}&epin={self.epin}"
        )
        mail_detail_response = requests.get(mail_detail_url)
        mail_detail_data = mail_detail_response.json()
        time.sleep(0.5)
        
        if not mail_detail_data.get("result"):
            return None, None

        # 从邮件文本中提取6位数字验证码
        mail_text = mail_detail_data.get("text", "")
        code_match = re.search(r"(?<![a-zA-Z@.])\b\d{6}\b", mail_text, re.DOTALL | re.IGNORECASE)

        if code_match:
            return code_match.group(1), first_id
        return None, None 