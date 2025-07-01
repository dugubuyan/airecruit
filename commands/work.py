import json
import re
from llm import get_system_prompt
from capacity import pdf_export, send_email
from utils.workspace import WorkspaceManager
from prompt_toolkit import PromptSession
from litellm import completion
from config import get_model

def handle_work_command(session, ws, current_config):
    """处理工作模式命令"""
    commands = [
        ("export2pdf", "需要md格式的内容", pdf_export.export_to_pdf),
        ("send_email", "需要收件人地址（自动从JD提取或手动输入）", send_email.send_email)
    ]
    
    resumes = ws.get_resumes()
    jds = ws.get_jds()
    system_msg = get_system_prompt(current_config.get('mode', 'candidate'))(resumes, jds)
    
    while True:
        try:
            cmd_input = session.prompt('work> ').strip()
            if not cmd_input:
                print("请问您需要我做什么？")
                continue
            if cmd_input.startswith('/'):
                return cmd_input

            messages = [{"role": "system", "content": system_msg}]
            while True:
                messages.append({"role": "user", "content": cmd_input})
                response = completion(
                    model=get_model(),
                    messages=messages,
                    temperature=0.3
                )
                choice = response.choices[0]
                message = choice.message
                ai_reply = message['content']
                print(f"\n助理：\n{ai_reply}\n")
                messages.append({"role": "assistant", "content": ai_reply})

                operation_match = re.search(r'```json\n(.*?)\n```', ai_reply, re.DOTALL)
                if operation_match:
                    operation_content = operation_match.group(1).strip()
                    operation_json = json.loads(operation_content)
                    operation_type = operation_json['action']
                    print(f"操作类型：{operation_type}")
                    params = {k: v for k, v in operation_json.items() if k != 'action'}
                        
                    cmd_func = next((c[2] for c in commands if c[0].find(operation_type) != -1), None)
                    if cmd_func:
                        try:
                            result = cmd_func(**params)
                            print(f"\n✅ 操作成功\n{result}\n")
                            break
                        except Exception as e:
                            print(f"\n❌ 操作失败：{str(e)}\n")
                            break
                    else:
                        print(f"未知操作类型：{operation_type}")
                        break

                next_input = session.prompt("请输入后续内容或参数（输入'取消'退出）： ")
                if next_input.lower() in ('取消', 'exit', 'quit'):
                    print("操作已取消")
                    break
                cmd_input = next_input

        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"执行出错：{str(e)}")
