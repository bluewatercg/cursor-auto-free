from .base import EmailServiceBase
import requests
import re
import time
import logging
from typing import Optional

class TempMailService(EmailServiceBase):
    """自定义邮件服务实现"""
    
    def __init__(self, config: dict):
        """
        初始化自定义邮件服务
        
        Args:
            config: 配置信息，包含:
                - api_domain: API域名
                - admin_password: 管理员密码
                - enable_prefix: 是否启用前缀
                - mail_domain: 邮箱域名
        """
        self.api_domain = config["api_domain"]
        self.admin_password = config["admin_password"]
        self.mail_domain = config["mail_domain"]
        self.enable_prefix = config["enable_prefix"]
        self.jwt_token = None
        self.email_address = None
        self.session = requests.Session()
        
    def _create_mail_address(self) -> bool:
        """创建邮箱地址"""
        try:
            # 从邮箱地址中提取用户名部分
            username = self.email_address.split('@')[0]
            
            res = requests.post(
                f"https://{self.api_domain}/admin/new_address",
                json={
                    "enablePrefix": self.enable_prefix,
                    "name": username,
                    "domain": self.mail_domain,
                },
                headers={
                    'x-admin-auth': self.admin_password,
                    "Content-Type": "application/json"
                }
            )
            
            if res.status_code == 200:
                data = res.json()
                self.jwt_token = data.get("jwt")
                return bool(self.jwt_token)
            
            logging.error(f"创建邮箱失败: {res.text}")
            return False
            
        except Exception as e:
            logging.error(f"创建邮箱出错: {str(e)}")
            return False
            
    def _get_latest_mail(self, limit: int = 10, max_retries: int = 20) -> Optional[str]:
        """获取最新邮件内容
        
        Args:
            limit: 获取邮件数量
            max_retries: 最大重试次数
            
        Returns:
            str: 邮件内容
        """
        if not self.jwt_token:
            logging.error("JWT token未初始化")
            return None
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                res = requests.get(
                    f"https://{self.api_domain}/api/mails",
                    params={"limit": limit, "offset": 0},
                    headers={
                        "Authorization": f"Bearer {self.jwt_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if res.status_code == 200:
                    mail = res.json()
                    if mail:
                      return mail["results"][0]["raw"]
                        
            except Exception as e:
                logging.error(f"获取邮件失败: {str(e)}")
                
            retry_count += 1
            time.sleep(3)
            
        return None
        
    def get_verification_code(self) -> str:
        """获取验证码"""
        try:
            # 获取最新邮件
            mail_content = self._get_latest_mail()
            if not mail_content:
                return None
                
            # 尝试从邮件正文中提取验证码
            code_match = re.search(
                r"(?<![a-zA-Z@.])\b\d{6}\b",
                mail_content,
                re.DOTALL
            )
            
            if code_match:
                return code_match.group()
                
            logging.warning("未能在邮件中找到验证码")
            return None
            
        except Exception as e:
            logging.error(f"获取验证码失败: {str(e)}")
            return None
            
    def cleanup(self) -> bool:
        """清理邮件，这个实现可能不需要清理"""
        return True
        
    def set_email_address(self, email: str):
        """设置要使用的邮箱地址"""
        self.email_address = email
        # 创建邮箱并获取 JWT token
        if not self._create_mail_address():
            raise Exception("创建邮箱地址失败")
        
    def get_email_address(self) -> str:
        """获取当前使用的邮箱地址"""
        if not self.email_address:
            raise ValueError("邮箱地址未设置")
        return self.email_address 