from .base import EmailServiceBase

import imaplib
import email
import re
import time
import logging


class ImapService(EmailServiceBase):
    def __init__(self, config: dict):
        """
        初始化 IMAP 服务
        
        Args:
            config: 配置信息，包含:
                - server: IMAP 服务器地址
                - port: IMAP 服务器端口
                - user: IMAP 用户名/邮箱
                - password: IMAP 密码
                - mailbox: 邮箱文件夹(例如: inbox)
        """
        self.server = config["server"]
        self.port = config["port"]
        self.user = config["user"]
        self.password = config["password"]
        self.mailbox = config["mailbox"]
        self.mail = None

    def set_email_address(self, email: str):
        """设置要接收验证码的目标邮箱地址"""
        return self.user
        
    def get_email_address(self) -> str:
        """获取当前使用的邮箱地址"""
        return self.user

    def get_verification_code(self, max_retries: int = 20) -> str:
        """获取验证码
        
        Args:
            max_retries: 最大重试次数
            
        Returns:
            str: 验证码
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                if retry_count > 0:
                    time.sleep(3)
                
                # 连接到IMAP服务器
                self.mail = imaplib.IMAP4_SSL(self.server, self.port)
                self.mail.login(self.user, self.password)
                self.mail.select(self.mailbox)

                # 搜索来自Cursor的邮件
                status, messages = self.mail.search(None, 'FROM', '"no-reply@cursor.sh"')
                if status != 'OK':
                    retry_count += 1
                    continue

                mail_ids = messages[0].split()
                if not mail_ids:
                    retry_count += 1
                    continue

                # 获取最新邮件
                latest_mail_id = mail_ids[-1]
                status, msg_data = self.mail.fetch(latest_mail_id, '(RFC822)')
                if status != 'OK':
                    retry_count += 1
                    continue

                # 解析邮件内容
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)
                body = self._extract_email_body(email_message)
                
                if body:
                    # 查找6位数字验证码
                    code_match = re.search(r"\b\d{6}\b", body)
                    if code_match:
                        code = code_match.group()
                        # 删除邮件
                        self.cleanup(latest_mail_id)
                        return code

            except Exception as e:
                logging.error(f"IMAP处理失败: {str(e)}")
            finally:
                if self.mail:
                    try:
                        self.mail.logout()
                    except:
                        pass
                        
            retry_count += 1
            
        raise Exception("获取验证码超时")
        
    def cleanup(self, mail_id: str) -> bool:
        """删除指定邮件"""
        try:
            if self.mail:
                self.mail.store(mail_id, '+FLAGS', '\\Deleted')
                self.mail.expunge()
                return True
        except Exception as e:
            logging.error(f"删除邮件失败: {str(e)}")
        return False
        
    def _extract_email_body(self, email_message) -> str:
        """提取邮件正文
        
        Args:
            email_message: 邮件消息对象
            
        Returns:
            str: 邮件正文
        """
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        return part.get_payload(decode=True).decode(charset, errors='ignore')
                    except Exception as e:
                        logging.error(f"解码邮件正文失败: {e}")
        else:
            content_type = email_message.get_content_type()
            if content_type == "text/plain":
                charset = email_message.get_content_charset() or 'utf-8'
                try:
                    return email_message.get_payload(decode=True).decode(charset, errors='ignore')
                except Exception as e:
                    logging.error(f"解码邮件正文失败: {e}")
        return "" 