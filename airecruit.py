# airecruit.py

import os
import argparse
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion
from diff_match_patch import diff_match_patch
import shlex
from flask import Flask, request, jsonify, render_template
from utils.workspace import WorkspaceManager
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from config import load_config, save_config, set_model, get_model, set_mode, get_mode
from llm import get_system_prompt
from utils.file_utils import (
    convert_pdf_to_md,
    convert_docx_to_md,
)
from commands import (
    pdf_export,
    generate_cover_letter,
    summarize_resume,
    resume_to_sql_filters,
    generate_recommendation,
    extract_contact_and_send,
    send_email,
    WORK_COMMANDS,
    optimize_resume
)


# Load environment variables
load_dotenv()

def chat_mode():
    """交互式聊天模式"""
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.styles import Style
    command_completer = WordCompleter([
        '/file', '/model', '/work', '/mode', '/exit', '/help'
    ], ignore_case=True)
    
    # 定义颜色常量
    RED = '\033[31m'
    BLUE = '\033[34m'
    RESET = '\033[0m'
    
    session = PromptSession(
        history=FileHistory('.airecruit_history'),
        completer=command_completer,
        style=Style.from_dict({
            'prompt': '#ff0000 bold',
        })
    )
    from utils.workspace import WorkspaceManager
    ws = WorkspaceManager()
    workspace_files = ws.list_files()
    print("欢迎进入AI招聘助手工作模式（输入/help查看帮助）")
    current_config = load_config()
    print(f"{RED}{'-'*50}")
    print(f"当前模式: {get_mode()}模式")
    print(f"当前模型: {current_config.get('model', '未设置')}")
    print(f"工作邮箱: {current_config.get('email', '未设置')}")
    print(f"今日日期: {datetime.datetime.now().strftime('%Y-%m-%d')}")
    # print(f"{'-'*50}{RESET}")
    while True:
        try:
            # 显示工作区文件和红色分隔线
            print(f"{RED}{'-'*50}")
            if workspace_files:
                print(f"{RED}工作区文件：" + ", ".join([f for f in workspace_files]) + f"{RESET}")
            text = session.prompt('> ')
            if not text.strip():
                print("请问您需要我做什么？")
                continue
            
            if text == '/file':
                # 进入文件管理子菜单
                print(f"\n{RED}文件管理操作（当前工作区文件：{len(workspace_files)}个）{RESET}")
                print("1. 扫描并添加文件 - 从workdir目录添加文件到工作区")
                print("2. 列出工作区文件 - 显示已添加的文件及其类型")
                print("3. 移除工作区文件 - 从工作区删除指定文件")
                print(f"{RED}0. 返回主菜单{RESET}")
                print(f"{RED}提示：支持的文件类型：PDF/DOCX/MD/TXT{RESET}")
                
                while True:
                    try:
                        # 文件子菜单提示符
                        print(f"{RED}{'-'*50}{RESET}")
                        if workspace_files:
                            print(f"{RED}工作区文件：" + ", ".join([f for f in workspace_files]) + f"{RESET}")
                        choice = session.prompt('file> ')
                        
                        if choice.startswith('/'):
                            text = choice  # 将命令传递回主循环
                            break
                        if choice == '0':
                            break
                            
                        # 显示当前工作区文件
                        print("\n当前工作区文件：")
                        for i, f in enumerate(workspace_files, 1):
                            print(f"{i}. {f}")
                        print()
                        
                        if choice == '1':
                            # 扫描workdir目录中的文件
                            work_dir = Path("workdir")
                            work_dir.mkdir(exist_ok=True)  # 确保目录存在
                            
                            # 获取目录中支持的文件类型
                            file_list = list(work_dir.glob("*.pdf")) + list(work_dir.glob("*.docx")) + \
                                      list(work_dir.glob("*.md")) + list(work_dir.glob("*.txt"))
                                      
                            if not file_list:
                                print("workdir目录中没有可用的文件（支持pdf/docx/md/txt格式）")
                                continue
                                
                            print("\nworkdir目录中的可用文件：")
                            for i, f in enumerate(file_list, 1):
                                print(f"{i}. {f.name}")
                                
                            file_nums = session.prompt("请输入要添加的文件编号（多个用空格分隔）: ")
                            if not file_nums.strip():
                                print("操作已取消")
                                continue
                                
                            added = []
                            try:
                                indexes = [int(n)-1 for n in file_nums.split()]
                                selected_files = [file_list[i] for i in indexes]
                            except (ValueError, IndexError):
                                print("错误：请输入有效的文件编号")
                                continue
                                
                            added = []
                            for file_path in selected_files:
                                if not file_path.exists():
                                    print(f"文件不存在：{f}")
                                    continue
                                
                                # 转换并添加文件
                                if file_path.suffix.lower() in ('.pdf', '.docx'):
                                    md_path = file_path.with_suffix('.md')
                                    try:
                                        if file_path.suffix.lower() == '.pdf':
                                            convert_pdf_to_md(str(file_path), str(md_path))
                                        else:
                                            convert_docx_to_md(str(file_path), str(md_path))
                                        workspace_files.append(str(md_path.resolve()))
                                        added.append(str(md_path))
                                    except Exception as e:
                                        print(f"转换文件 {f} 失败：{str(e)}")
                                elif file_path.suffix.lower() in ('.txt', '.md'):
                                    # 读取文件内容
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    
                                    # 让用户分类文件类型
                                    file_type = session.prompt(
                                        f"请为文件 {file_path.name} 选择类型：\n"
                                        "1. 简历\n2. 职位描述(JD)\n请输入编号: "
                                    ).strip()
                                    
                                    file_type = 'resume' if file_type == '1' else 'jd'
                                    
                                    # 添加到工作区
                                    ws.add_file(
                                        path=str(file_path.resolve()),
                                        file_type=file_type,
                                    )
                                    added.append(file_path.name)
                                    # 刷新工作区文件列表（带类型标记）
                                    workspace_files = ws.list_files()
                                else:
                                    print(f"跳过不支持的文件类型：{file_path.suffix}")
                            
                            if added:
                                print(f"已添加文件：{', '.join(added)}")
                                
                        elif choice == '2':
                            pass  # 前面已经显示过文件列表
                            
                        elif choice == '3':
                            to_remove = session.prompt("请输入要移除的文件编号（多个用空格分隔）: ")
                            try:
                                indexes = [int(i)-1 for i in to_remove.split()]
                                removed = []
                                new_files = []
                                for i, f in enumerate(workspace_files):
                                    if i in indexes:
                                        removed.append(f)
                                    else:
                                        new_files.append(f)
                                workspace_files = new_files
                                # 通过WorkspaceManager更新工作区文件
                                ws.remove_files([workspace_files[i] for i in indexes])
                                ws.save_workspace()
                                print(f"已移除文件：{', '.join(removed)}")
                            except (ValueError, IndexError):
                                print("错误：请输入有效的文件编号")
                                
                        else:
                            print("错误：无效选项，请输入 0-3 的数字")
                        continue
                    except (KeyboardInterrupt, EOFError):
                        break
                
            elif text.startswith('/model'):
                parts = text.split(maxsplit=1)
                if len(parts) < 2:
                    print("错误：命令格式为/model <ls|模型名称>")
                    continue
                
                if parts[1].lower() == 'ls':
                    print("支持的模型列表：")
                    current_config = load_config()
                    for model in current_config.get('supported_models', []):
                        print(f"- {model}")
                    continue
                
                new_model = parts[1]
                try:
                    if new_model not in load_config().get('supported_models', []):
                        raise ValueError(f"不支持该模型，请使用/model ls查看支持列表")
                    set_model(new_model)
                    print(f"模型已设置为：{new_model}")
                except ValueError as e:
                    print(f"错误：{str(e)}")
                
            elif text.startswith('/mode'):
                parts = text.split(maxsplit=1)
                if len(parts) < 2:
                    print(f"当前模式: {get_mode()}模式模式")
                    print("使用方法: /mode <candidate|hunter>")
                    continue
                try:
                    set_mode(parts[1].lower())
                    print(f"工作模式已设置为: {parts[1]}模式")
                    # 刷新配置显示
                    current_config = load_config()
                except ValueError as e:
                    print(f"错误: {str(e)}")
                    
            elif text == '/exit':
                break
                
            elif text == '/help':
                print(f"可用命令列表：\n"
                      "/file       - 文件管理（添加/查看/删除工作区文件）\n"
                      "/model ls   - 查看所有支持的AI模型列表\n" 
                      "/model <名称> - 切换AI模型（需要先查看支持列表）\n"
                      "/work      - 进入智能工作模式（简历优化/生成求职信等）\n"
                      "/mode <candidate|hunter> - 切换候选人/猎头模式\n"
                      f"系统状态：\n"
                      f"当前模型：{get_model()}\n"
                      f"工作区文件：{len(workspace_files)}个\n"
                      f"输入 /exit 退出程序")
                      
            elif text == '/work':
                print(f"{RED}{'-'*50}")
                print(f"当前模式: {get_mode()}模式")
                print(f"当前模型: {get_model()}")
                print(f"工作邮箱: {current_config.get('email', '未设置')}")
                print(f"今日日期: {datetime.datetime.now().strftime('%Y-%m-%d')}")
                commands = [
                    ("export2pdf", "需要md格式的内容", pdf_export.export_to_pdf),
                    ("send-email", "需要收件人地址（自动从JD提取或手动输入）", send_email.send_email)
                ]
                # 构造动态系统提示
                # 获取最新工作区状态
                resumes = ws.get_resumes()
                jds = ws.get_jds()
                
                system_msg = get_system_prompt(current_config.get('mode', 'candidate'))(resumes, jds)
                while True:
                    try:
                        # 工作命令子菜单提示符
                        # 获取最新工作区文件
                        from utils.workspace import WorkspaceManager
                        ws = WorkspaceManager()
                        workspace_files = ws.list_files()
                        print(f"{RED}{'-'*50}{RESET}")
                        if workspace_files:
                            print(f"{RED}工作区文件：" + " ".join([f for f in workspace_files]) + f"{RESET}")
                            
                        cmd_input = session.prompt('work> ').strip()
                        if not cmd_input:
                            print("请问您需要我做什么？")
                        if cmd_input.startswith('/'):
                            text = cmd_input  # 将命令传递回主循环
                            break
                            
                        # 处理自然语言输入
                        messages = [{"role": "system", "content": system_msg}]
                        while True:
                            try:
                                messages.append({"role": "user", "content": cmd_input})
                                response = completion(
                                    model=get_model(),
                                    messages=messages,
                                    temperature=0.3
                                )
                                print("mesages++++++++++222222222:",messages)
                                # 统一处理不同LLM响应格式为字典
                                choice = response.choices[0]
                                message = choice.message
                                
                                # 转换Pydantic模型为字典
                                if hasattr(message, 'dict'):
                                    message_dict = message.dict()
                                else:
                                    message_dict = dict(message)
                                
                                ai_reply = message_dict.get('content', '')
                                # 同时处理finish_reason字段
                                finish_reason = getattr(choice, 'finish_reason', None)
                                print(f"\n助理：\n{ai_reply}\n")
                                messages.append({"role": "assistant", "content": ai_reply})
                                # 解析操作块
                                import re
                                operation_match = re.search(r'```json\n(.*?)\n```', ai_reply, re.DOTALL)
                                if operation_match:
                                    operation_content = operation_match.group(1).strip()
                                    # 解析JSON参数
                                    operation_json = json.loads(operation_content)
                                    operation_type = operation_json['action']
                                    params = {k: v for k, v in operation_json.items() if k != 'action'}
                                        
                                    # 查找匹配的命令
                                    cmd_func = next((c[2] for c in commands if c[0].find(operation_type) != -1), None)
                                    if cmd_func:
                                        # 执行前检查必要参数
                                        missing_params = []
                                        if '收件人' in params and '❌' in params['收件人']:
                                            missing_params.append('收件人邮箱')
                                        if '附件路径' in params and '❌' in params['附件路径']:
                                            missing_params.append('附件路径')
                                            
                                        if missing_params:
                                            print(f"缺少必要参数：{', '.join(missing_params)}")
                                            cmd_input = session.prompt("请补充缺失参数（格式：参数名=值）：")
                                        else:
                                            try:
                                                result = cmd_func(**params)
                                                print(f"\n✅ 操作成功：\n{result}\n")
                                                break
                                            except Exception as e:
                                                print(f"\n❌ 操作失败：{str(e)}\n")
                                                break
                                    else:
                                        print(f"未知操作类型：{operation_type}")
                                        break
                                    
                                # 继续对话
                                next_input = session.prompt("请输入后续内容或参数（输入'取消'退出）： ")
                                if next_input.lower() in ('取消', 'exit', 'quit'):
                                    print("操作已取消")
                                    break
                                cmd_input = next_input
                                    
                            except Exception as e:
                                print(f"发生错误：{str(e)}")
                                break
                            
                    except (KeyboardInterrupt, EOFError):
                        break
                    except Exception as e:
                        print(f"执行出错：{str(e)}")
            else:
                # 非命令输入自动进入工作模式
                commands = [
                    ("1. 简历优化", "optimize", "需要职位描述(JD)和简历内容", optimize_resume),
                    ("2. 简历摘要", "summarize", "需要简历内容", summarize_resume),
                    ("3. 生成求职信", "cover-letter", "需要职位描述(JD)和简历内容", generate_cover_letter),
                    ("4. 生成筛选条件", "filters", "需要简历内容生成SQL条件", resume_to_sql_filters),
                    ("5. 职位推荐", "recommend", "需要职位描述(JD)和简历内容", generate_recommendation),
                    ("6. 提取联系信息", "contact", "需要职位描述(JD)", extract_contact_and_send),
                    ("7. 发送邮件", "send-email", "需要收件人地址（自动从JD提取或手动输入）", send_email.send_email)
                ]
                
                # 获取最新工作区状态
                resumes = ws.get_resumes()
                jds = ws.get_jds()
                
                # 构造系统提示
                system_msg = f'''## AI 招聘助手系统提示
你是一位智能招聘助手，当前工作区状态：
📁 简历文件：{len(resumes)}份 ({'✅' if len(resumes)>=1 else '❌'})
📄 JD文件：{len(jds)}份 ({'✅' if len(jds)>=1 else '❌'})

### 工作模式说明

1. 所有操作基于本地文件和用户输入
2. 你需要用Markdown格式返回响应
3. 当需要执行本地操作时，按以下格式返回：

```operation
操作类型: [操作名称]
参数:
  参数1: 值
  参数2: 值
```

### 支持的操作类型、执行要求等内容与/work模式一致'''
                
                # 直接进入工作模式处理循环
                cmd_input = text.strip()
                try:
                    # 复用/work模式的处理逻辑
                    messages = [{"role": "system", "content": system_msg}]
                    while True:
                        messages.append({"role": "user", "content": cmd_input})
                        response = completion(
                            model=get_model(),
                            messages=messages,
                            temperature=0.3
                        )

                        # 统一处理LLM响应格式为字典
                        choice = response.choices[0]
                        message = choice.message
                        
                        # 转换Pydantic模型为字典
                        if hasattr(message, 'dict'):
                            message_dict = message.dict()
                        else:
                            message_dict = dict(message)
                        
                        ai_reply = message_dict.get('content', '')
                        # 同时处理finish_reason字段
                        finish_reason = getattr(choice, 'finish_reason', None)
                        print(f"\n助理：\n{ai_reply}\n")

                        # 解析和执行操作（复用/work模式的代码）
                        import re
                        operation_match = re.search(r'```json\n(.*?)\n```', ai_reply, re.DOTALL)
                        if operation_match:
                            operation_content = operation_match.group(1).strip()
                            # 解析JSON参数
                            operation_json = json.loads(operation_content)
                            operation_type = operation_json['action']
                            params = {k: v for k, v in operation_json.items() if k != 'action'}
                            
                            # 查找匹配的命令
                            cmd_func = next((c[3] for c in commands if c[0].find(operation_type) != -1), None)
                            if cmd_func:
                                # 执行前检查必要参数
                                missing_params = []
                                if '收件人' in params and '❌' in params['收件人']:
                                    missing_params.append('收件人邮箱')
                                if '附件路径' in params and '❌' in params['附件路径']:
                                    missing_params.append('附件路径')
                                
                                if missing_params:
                                    print(f"缺少必要参数：{', '.join(missing_params)}")
                                    cmd_input = session.prompt("请补充缺失参数（格式：参数名=值）：")
                                else:
                                    try:
                                        result = cmd_func(**params)
                                        print(f"\n✅ 操作成功：\n{result}\n")
                                        break
                                    except Exception as e:
                                        print(f"\n❌ 操作失败：{str(e)}\n")
                                        break
                            else:
                                print(f"未知操作类型：{operation_type}")
                                break

                        # 继续对话
                        next_input = session.prompt("请输入后续内容或参数（输入'取消'退出）： ")
                        if next_input.lower() in ('取消', 'exit', 'quit'):
                            print("操作已取消")
                            break
                        cmd_input = next_input
                except Exception as e:
                    print(f"发生错误：{str(e)}")
                
        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"出错：{e}")


# Local web server with Flask
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/api/add_file", methods=["POST"])
def api_add_file():
    from utils.workspace import WorkspaceManager
    ws = WorkspaceManager()
    file_path = request.json.get("path")
    if not file_path:
        return jsonify({"error": "Missing file path"}), 400
    ws.add_file(file_path, "auto", "")
    return jsonify({"status": "added", "path": file_path})

@app.route("/api/files", methods=["GET"])
def api_files():
    from utils.workspace import WorkspaceManager
    ws = WorkspaceManager()
    return jsonify(ws.list_files())

@app.route("/api/optimize", methods=["POST"])
def api_optimize():
    from utils.workspace import WorkspaceManager
    ws = WorkspaceManager()
    
    try:
        # 从工作区获取最新简历和JD
        resumes = ws.get_resumes()
        jds = ws.get_jds()
        
        if not resumes or not jds:
            return jsonify({"error": "需要至少一份简历和职位描述"}), 400
            
        # 使用第一个找到的简历和JD
        resume_path = resumes[0]
        jd_path = jds[0]

        with open(resume_path, 'r', encoding='utf-8') as f:
            resume_content = f.read()
        with open(jd_path, 'r', encoding='utf-8') as f:
            jd_content = f.read()
        
        result = optimize_resume.optimize_resume(jd_content, resume_content)
        return jsonify({"optimized": result})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# CLI
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Recruit Assistant")
    parser.add_argument("--browser", action="store_true", help="Start web server and open browser")
    parser.add_argument("--verbose", action="store_true", help="Show LLM request details")
    parser.add_argument("-m", "--model", type=str, help="Set LLM model")
    args = parser.parse_args()
    if args.model:
        set_model(args.model)
        print(f"模型已设置为：{args.model}")
    elif args.browser:
        import webbrowser
        app.run(host='0.0.0.0', port=5001, debug=True)
        webbrowser.open('http://localhost:5001')
    else:
        chat_mode()
