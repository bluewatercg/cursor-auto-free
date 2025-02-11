from abc import ABC, abstractmethod

class EmailServiceBase(ABC):
    """邮件服务基类"""
    
    @abstractmethod
    def get_verification_code(self) -> str:
        """获取验证码"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """清理邮件"""
        pass
    
    @abstractmethod
    def get_email_address(self) -> str:
        """获取邮箱地址"""
        pass 