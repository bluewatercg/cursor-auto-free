import random
import string
import time

class EmailGenerator:
    """邮箱生成器工具类"""
    
    @staticmethod
    def generate_random_string(length: int = 8) -> str:
        """生成随机字符串"""
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(length))
    
    @staticmethod
    def generate_random_name(length: int = 8) -> str:
        """生成随机邮箱名称，包含时间戳"""
        random_str = EmailGenerator.generate_random_string(length)
        timestamp = str(int(time.time()))[-6:]  # 使用时间戳后6位
        return f"{random_str}{timestamp}" 