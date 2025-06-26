from email.mime.text import MIMEText
from email.header import Header
from config import get_smtp_config
from redmail import EmailSender
import html
from pathlib import Path
def send_email(recipient, subject, body, has_attachment, template=None):
    """
    发送邮件到指定的地址。

    :param recipient: 收件人邮箱地址
    :param subject: 邮件主题
    :param body: 邮件正文
    :param template: 邮件模版，如果为None则使用默认模版
    """
    print("send_email::",recipient, subject, body)
    config = get_smtp_config()

    sender = config['sender_email'] # 发件人邮箱
    password = config['sender_password']  # 发件人邮箱密码
    smtp_server = config['smtp_server']  # SMTP服务器地址
    smtp_port = config['smtp_port']  # SMTP端口

    if not sender or not password or not smtp_server:
        raise ValueError("请先配置发件人邮箱、密码和SMTP服务器信息")
    
    # 1. 转义特殊字符（<, >, & 等）
    escaped_text = html.escape(body)
    
    # 2. 替换换行符为 HTML 换行标签
    body = escaped_text.replace('\n', '<br>')

    # 3. 处理附件
    attachments = get_attachment() if has_attachment == 'true' else {}
    print("attachments:",attachments)
    # 邮件模版
    if template is None:
        template = config.get('default_email_template', """
        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
            <p>{body}</p>
        </div>
        """)

    # 格式化邮件内容
    html_body = template.format(body=body)

    try:
        email = EmailSender(host=smtp_server, port=smtp_port, username="longhui@chainfeeds.xyz", password="omenmvywtbffjbev")
        email.send(
            subject,sender,receivers=[recipient],html=html_body,attachments=attachments
            )
        return f"成功发送邮件到{recipient}"
    except Exception as e:
        raise Exception(f"邮件发送失败: {str(e)}")

def get_attachment():
    attachment = {"resume.pdf": Path("workdir/resume_optimized.pdf").resolve()} #TODO： hard code 
    return attachment
def test_work():
    attachment = {"resume.pdf": Path("workdir/resume_optimized.pdf").resolve()} 
    print(attachment)
# def send():
#     body = "尊敬的HR：\n\n您好！\n\n我是在招聘网站上看到贵公司招聘高级研发工程师(P5)的职位，我对该职位非常感兴趣，并相信我的技能和经验能够胜任该职位。\n\n我叫朱元璋，拥有7年的Java开发经验。我熟悉SpringBoot、MyBatis、Dubbo、Redis、RocketMQ等常用开源框架与组件，了解常用的设计模式，对微服务、分布式系统相关概念及技术有一定了解。在项目经验方面，我曾参与浦发银行持续发布平台、苏州银行关联方交易管理项目等多个项目，积累了丰富的项目经验。\n\n我具备扎实的Java基础，熟悉Linux操作系统，具备良好的调试、线上诊断和性能调优能力。同时，我具有责任心，抗压且乐观，有团队合作精神，善于总结和分享。\n\n我对贵公司的供应链行业非常感兴趣，并且具备高并发或海量数据实战项目经验。我相信我的加入能够为贵公司带来价值。\n\n感谢您抽出时间阅读我的求职信。我期待有机会与您进一步沟通。\n\n简历文件见附件。\n\n此致\n\n敬礼！\n\n朱元璋"

#     attachments={"resume.pdf": Path("/Users/alex/work/startup/ai-hunter/project/airecruit/workdir/resume_optimized.pdf")}
#     send_email("335767028@qq.com","求职信-高级研发工程师(P5)",body,attachments)

