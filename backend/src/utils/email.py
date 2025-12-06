"""
Email Utility - Gmail SMTP를 사용한 이메일 전송
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from src.config import settings


class EmailService:
    """이메일 전송 서비스"""
    
    def __init__(self):
        self.smtp_host = settings.email_host
        self.smtp_port = settings.email_port
        self.email_user = settings.email_user
        self.email_password = settings.email_password
        self.from_email = settings.email_from or settings.email_user
        
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        이메일 전송
        
        Args:
            to_email: 수신자 이메일
            subject: 제목
            html_content: HTML 본문
            text_content: 텍스트 본문 (optional)
            
        Returns:
            bool: 성공 여부
        """
        if not self.email_user or not self.email_password:
            print("⚠️ 이메일 설정이 없습니다. .env 파일을 확인하세요.")
            return False
            
        try:
            # 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"제주여행 챗봇 <{self.from_email}>"
            msg['To'] = to_email
            
            # 텍스트 및 HTML 파트 추가
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
                
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # SMTP 연결 및 전송
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # TLS 암호화
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
                
            print(f"✅ 이메일 전송 성공: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ 이메일 전송 실패: {str(e)}")
            return False
    
    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str) -> bool:
        """
        비밀번호 재설정 이메일 전송
        
        Args:
            to_email: 수신자 이메일
            reset_token: 재설정 토큰
            user_name: 사용자 이름
            
        Returns:
            bool: 성공 여부
        """
        # 프론트엔드 URL
        frontend_url = settings.frontend_url
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"
        
        subject = "[제주여행 챗봇] 비밀번호 재설정"
        
        # HTML 이메일 템플릿
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #fff5f0 0%, #f0f9ff 100%);
                    border-radius: 16px;
                    padding: 40px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .emoji {{
                    font-size: 48px;
                    margin-bottom: 10px;
                }}
                h1 {{
                    color: #f97316;
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    margin: 20px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 14px 28px;
                    background: linear-gradient(135deg, #f97316 0%, #3b82f6 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .button:hover {{
                    opacity: 0.9;
                }}
                .warning {{
                    background: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="emoji">🍊</div>
                    <h1>비밀번호 재설정</h1>
                </div>
                
                <div class="content">
                    <p>안녕하세요, <strong>{user_name}</strong>님!</p>
                    
                    <p>비밀번호 재설정 요청을 받았습니다.</p>
                    
                    <p>아래 버튼을 클릭하여 새로운 비밀번호를 설정해주세요:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">
                            🔐 비밀번호 재설정하기
                        </a>
                    </div>
                    
                    <div class="warning">
                        ⚠️ <strong>주의:</strong> 이 링크는 <strong>30분 동안</strong>만 유효합니다.
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        버튼이 작동하지 않으면 아래 링크를 복사하여 브라우저에 붙여넣으세요:<br>
                        <a href="{reset_url}" style="color: #3b82f6;">{reset_url}</a>
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    
                    <p style="color: #666; font-size: 14px;">
                        💡 비밀번호 재설정을 요청하지 않으셨다면 이 이메일을 무시하셔도 됩니다.
                    </p>
                </div>
                
                <div class="footer">
                    <p>감귤처럼 상큼한 제주 여행 ✨</p>
                    <p style="font-size: 12px; color: #999;">
                        이 이메일은 발신 전용입니다. 회신하지 마세요.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 텍스트 버전 (HTML을 지원하지 않는 이메일 클라이언트용)
        text_content = f"""
안녕하세요, {user_name}님!

비밀번호 재설정 요청을 받았습니다.

아래 링크를 클릭하여 새로운 비밀번호를 설정해주세요:
{reset_url}

⚠️ 주의: 이 링크는 30분 동안만 유효합니다.

비밀번호 재설정을 요청하지 않으셨다면 이 이메일을 무시하셔도 됩니다.

감귤처럼 상큼한 제주 여행 ✨
        """
        
        return self.send_email(to_email, subject, html_content, text_content)


# 싱글톤 인스턴스
email_service = EmailService()

