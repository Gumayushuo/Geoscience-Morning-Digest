# scripts/send_email.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 配置
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
TO_EMAIL = os.getenv("TO_EMAIL", EMAIL_USER)  # 默认发给自己，也可以在 Secrets 里指定其他收件人

SMTP_SERVER = os.getenv("SMTP_SERVER")  # 例如 "mail.xxx.edu.cn"
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))  # 默认 465 (SSL)


# 读取 daily.md 内容
with open("output/daily.md", "r", encoding="utf-8") as f:
    content = f.read()

# 构建邮件
msg = MIMEMultipart()
msg['From'] = EMAIL_USER
msg['To'] = TO_EMAIL
msg['Subject'] = "📄 今日论文晨报"

# 邮件正文，Markdown 内容可以直接放入 text/plain
msg.attach(MIMEText(content, 'plain', 'utf-8'))

# 发送邮件
try:
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, TO_EMAIL, msg.as_string())
    print("Email sent successfully.")
except Exception as e:
    print(f"Failed to send email: {e}")
