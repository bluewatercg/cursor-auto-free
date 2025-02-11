from .base import EmailServiceBase
from .utils import EmailGenerator
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
                - mail_name: 邮箱名称
                - mail_domain: 邮箱域名
        """
        self.api_domain = config["api_domain"]
        self.admin_password = config["admin_password"]
        self.mail_domain = config["mail_domain"]
        self.enable_prefix = config["enable_prefix"]
        # 生成随机邮箱名
        self.mail_name = EmailGenerator.generate_random_name()
        self.jwt_token = None
        self.email_address = None
        
    def _create_mail_address(self) -> bool:
        """创建邮箱地址"""
        try:
            res = requests.post(
                f"https://{self.api_domain}/admin/new_address",
                json={
                    "enablePrefix": self.enable_prefix,
                    "name": self.mail_name,
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
                if self.enable_prefix:
                    prefix = data.get("prefix", "")
                    self.email_address = f"{prefix}{self.mail_name}@{self.mail_domain}"
                else:
                    self.email_address = f"{self.mail_name}@{self.mail_domain}"
                logging.info(f"创建邮箱成功: {self.email_address}")
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
            # 使用新的正则表达式模式匹配6位数字验证码
            code_match = re.search(
                r'Enter the code below.*?(\d{6})',
                mail_content,
                re.DOTALL | re.IGNORECASE
            )
            
            if code_match:
                return code_match.group(1)
                
            logging.warning("未能在邮件中找到验证码")
            return None
            
        except Exception as e:
            logging.error(f"获取验证码失败: {str(e)}")
            return None
            
    def cleanup(self) -> bool:
        """清理邮件，这个实现可能不需要清理"""
        return True
        
    def get_email_address(self) -> str:
        """获取邮箱地址，如果还没有创建则先创建"""
        if not self.email_address:
            if not self._create_mail_address():
                raise Exception("创建邮箱地址失败")
        return self.email_address 