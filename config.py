from dotenv import load_dotenv
import os
import sys
from logger import logging


class Config:
    def __init__(self):
        # 获取应用程序的根目录路径
        if getattr(sys, "frozen", False):
            # 如果是打包后的可执行文件
            application_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            application_path = os.path.dirname(os.path.abspath(__file__))

        # 指定 .env 文件的路径
        dotenv_path = os.path.join(application_path, ".env")

        if not os.path.exists(dotenv_path):
            raise FileNotFoundError(f"文件 {dotenv_path} 不存在")

        # 加载 .env 文件
        load_dotenv(dotenv_path)

        # 基础配置
        self.domain = os.getenv("DOMAIN", "").strip()
        self.email_service = os.getenv("EMAIL_SERVICE", "temp_mail").strip()
        
        # TempMail 配置
        self.temp_mail_api_domain = f"mail.{self.domain}"  # 使用 mail.domain 作为 API 域名
        self.temp_mail_admin_password = os.getenv("TEMP_MAIL_ADMIN_PASSWORD", "").strip()
        self.temp_mail_domain = self.domain  # 直接使用主域名
        self.temp_mail_enable_prefix = os.getenv("TEMP_MAIL_ENABLE_PREFIX", "true").lower() == "true"
        
        # TempMail Plus 配置
        self.temp_mail_plus_username = os.getenv("TEMP_MAIL_PLUS_USERNAME", "").strip()
        self.temp_mail_plus_epin = os.getenv("TEMP_MAIL_PLUS_EPIN", "").strip()
        self.temp_mail_plus_domain = self.domain  # 使用相同的域名
        self.temp_mail_plus_api_domain = f"mail.{self.domain}"  # 使用相同的 API 域名
        self.temp_mail_plus_ext = os.getenv("TEMP_MAIL_PLUS_EXT", "@mailto.plus").strip()
        
        # IMAP 配置 - 不依赖 CF Workers，需要完整的服务器配置
        self.imap_server = os.getenv("IMAP_SERVER", "").strip()
        self.imap_port = os.getenv("IMAP_PORT", "").strip()
        self.imap_user = os.getenv("IMAP_USER", "").strip()
        self.imap_pass = os.getenv("IMAP_PASS", "").strip()
        self.imap_dir = os.getenv("IMAP_DIR", "inbox").strip()

        self.check_config()

    def get_email_service_config(self) -> dict:
        """获取当前选择的邮件服务配置"""
        if self.email_service == "temp_mail":
            return {
                "api_domain": self.temp_mail_api_domain,
                "admin_password": self.temp_mail_admin_password,
                "mail_domain": self.temp_mail_domain,
                "enable_prefix": self.temp_mail_enable_prefix
            }
        elif self.email_service == "temp_mail_plus":
            return {
                "epin": self.temp_mail_plus_epin,
                "extension": self.temp_mail_plus_ext,
                "username": self.temp_mail_plus_username
            }
        elif self.email_service == "imap":
            return {
                "server": self.imap_server,
                "port": self.imap_port,
                "user": self.imap_user,
                "password": self.imap_pass,
                "mailbox": self.imap_dir
            }
        return {}

    def get_domain(self):
        return self.domain

    def check_config(self):
        """检查配置有效性"""
        # 检查基础配置
        if not self.check_is_valid(self.domain):
            raise ValueError("域名未配置，请在 .env 文件中设置 DOMAIN")
        
        if not self.check_is_valid(self.email_service):
            raise ValueError("邮件服务类型未配置，请在 .env 文件中设置 EMAIL_SERVICE")
        
        # 检查当前选择的邮件服务的配置
        service_configs = {
            "temp_mail": {
                "name": "TempMail",
                "required": [
                    (self.temp_mail_admin_password, "TEMP_MAIL_ADMIN_PASSWORD")
                ]
            },
            "temp_mail_plus": {
                "name": "TempMail Plus",
                "required": [
                    (self.temp_mail_plus_username, "TEMP_MAIL_PLUS_USERNAME"),
                    (self.temp_mail_plus_epin, "TEMP_MAIL_PLUS_EPIN"),
                    (self.temp_mail_plus_ext, "TEMP_MAIL_PLUS_EXT")
                ]
            },
            "imap": {
                "name": "IMAP",
                "required": [
                    (self.imap_server, "IMAP_SERVER"),
                    (self.imap_port, "IMAP_PORT"),
                    (self.imap_user, "IMAP_USER"),
                    (self.imap_pass, "IMAP_PASS")
                ]
            }
        }
        
        # 获取当前服务的配置要求
        service_config = service_configs.get(self.email_service)
        if not service_config:
            raise ValueError(f"不支持的邮件服务类型: {self.email_service}")
        
        # 检查必需的配置项
        missing_configs = []
        for value, name in service_config["required"]:
            if not self.check_is_valid(value):
                missing_configs.append(name)
            
        if missing_configs:
            raise ValueError(
                f"{service_config['name']} 配置不完整，缺少以下配置项:\n" + 
                "\n".join(f"- {name}" for name in missing_configs)
            )

    def check_is_valid(self, value):
        """检查配置项是否有效
        Args:
            value: 配置项的值

        Returns:
            bool: 配置项是否有效
        """
        return isinstance(value, str) and len(str(value).strip()) > 0

    def print_config(self):
        logging.info(f"\033[32m当前使用的邮件服务: {self.email_service}\033[0m")
        if self.email_service == "temp_mail":
            logging.info(f"\033[32mAPI域名: {self.temp_mail_api_domain}\033[0m")
            logging.info(f"\033[32m邮箱域名: {self.temp_mail_domain}\033[0m")
        elif self.email_service == "temp_mail_plus":
            logging.info(f"\033[32m临时邮箱: {self.temp_mail_plus_username}{self.temp_mail_plus_ext}\033[0m")
        elif self.email_service == "imap":
            logging.info(f"\033[32mIMAP服务器: {self.imap_server}\033[0m")
            logging.info(f"\033[32mIMAP用户名: {self.imap_user}\033[0m")
        logging.info(f"\033[32m域名: {self.domain}\033[0m")


# 使用示例
if __name__ == "__main__":
    try:
        config = Config()
        print("环境变量加载成功！")
        config.print_config()
    except ValueError as e:
        print(f"错误: {e}")
