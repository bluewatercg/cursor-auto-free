from typing import Optional
from .base import EmailServiceBase
from .tempmail import TempMailService
from .tempmailplus import TempMailPlusService
from .imap import ImapService

class EmailServiceFactory:
    """邮件服务工厂类"""
    
    @staticmethod
    def create_service(service_type: str, config: dict) -> Optional[EmailServiceBase]:
        """
        创建邮件服务实例
        
        Args:
            service_type: 服务类型 (temp_mail/temp_mail_plus/imap)
            config: 服务配置信息
            
        Returns:
            EmailServiceBase: 邮件服务实例
        """
        if service_type == "temp_mail":
            return TempMailService(config=config)
        elif service_type == "temp_mail_plus":
            return TempMailPlusService(config=config)
        elif service_type == "imap":
            return ImapService(config=config)
            
        raise ValueError(f"不支持的邮件服务类型: {service_type}") 