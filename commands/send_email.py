import smtplib
from email.mime.text import MIMEText
from email.header import Header
from config import load_config

def send_email(recipient, subject, body, template=None):
    """
    发送邮件到指定的地址。

    :param recipient: 收件人邮箱地址
    :param subject: 邮件主题
    :param body: 邮件正文
    :param template: 邮件模版，如果为None则使用默认模版
    """
    config = load_config()
    sender = config.get('email')  # 发件人邮箱
    password = config.get('email_password')  # 发件人邮箱密码
    smtp_server = config.get('smtp_server')  # SMTP服务器地址
    smtp_port = config.get('smtp_port', 465)  # SMTP端口，默认为465

    if not sender or not password or not smtp_server:
        raise ValueError("请先配置发件人邮箱、密码和SMTP服务器信息")

    # 邮件模版
    if template is None:
        template = config.get('default_email_template', """
        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
            <p>尊敬的 {recipient}，</p>
            <p>{body}</p>
            <p>此致，</p>
            <p>AI招聘助手</p>
        </div>
        """)

    # 格式化邮件内容
    html_body = template.format(recipient=recipient, body=body)

    # 构造邮件
    message = MIMEText(html_body, 'html', 'utf-8')
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = Header(subject, 'utf-8')

    try:
        # 连接SMTP服务器并发送邮件
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender, password)
        server.sendmail(sender, [recipient], message.as_string())
        server.quit()
        return "邮件发送成功"
    except Exception as e:
        raise Exception(f"邮件发送失败: {str(e)}")
````

接下来，这是 `airecruit.py` 的 *SEARCH/REPLACE* 块：

airecruit.py
````python
<<<<<<< SEARCH
    generate_recommendation,
    extract_contact_and_send,
    WORK_COMMANDS
)
