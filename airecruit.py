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
from config import load_config, save_config, set_model, get_model

from commands import (
    optimize_resume,
    generate_cover_letter,
    summarize_resume,
    resume_to_sql_filters,
    generate_recommendation,
    extract_contact_and_send,
    WORK_COMMANDS
)

# Load environment variables
load_dotenv()

config = load_config()

def chat_mode():
    """交互式聊天模式"""
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.styles import Style
    command_completer = WordCompleter([
        '/file', '/model', '/work', '/exit', '/help'
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
    workspace_files = config.get('workspace_files', [])
    
    print("欢迎进入AI招聘助手工作模式（输入/help查看帮助）")
    current_config = load_config()
    print(f"{RED}{'-'*50}")
    print(f"当前模型: {get_model()}")
    print(f"工作邮箱: {current_config.get('email', '未设置')}")
    print(f"今日日期: {datetime.datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'-'*50}{RESET}")
    while True:
        try:
            # 显示工作区文件和红色分隔线
            if workspace_files:
                print(f"{RED}工作区文件：" + ", ".join([Path(f).name for f in workspace_files]) + f"{RESET}")
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
                            print(f"{RED}工作区文件：" + ", ".join([Path(f).name for f in workspace_files]) + f"{RESET}")
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
                                    from utils.workspace import WorkspaceManager
                                    ws = WorkspaceManager()
                                    ws.add_file(
                                        path=str(file_path.resolve()),
                                        file_type=file_type,
                                        content=content
                                    )
                                    added.append(file_path.name)
                                    # 刷新工作区文件列表（带类型标记）
                                    workspace_files = ws.list_files()
                                else:
                                    print(f"跳过不支持的文件类型：{file_path.suffix}")
                            
                            if added:
                                workspace_files = list(set(workspace_files))  # 去重
                                config['workspace_files'] = workspace_files
                                save_config(config)
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
                                config['workspace_files'] = workspace_files
                                save_config(config)
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
                
            elif text == '/exit':
                break
                
            elif text == '/help':
                print("可用命令：\n"
                      f"{RED}可用命令列表：{RESET}\n"
                      "/file       - 文件管理（添加/查看/删除工作区文件）\n"
                      "/model ls   - 查看所有支持的AI模型列表\n" 
                      "/model <名称> - 切换AI模型（需要先查看支持列表）\n"
                      "/work      - 进入智能工作模式（简历优化/生成求职信等）\n"
                      f"{RED}系统状态：{RESET}\n"
                      f"当前模型：{get_model()}\n"
                      f"工作区文件：{len(workspace_files)}个\n"
                      f"{RED}输入 /exit 退出程序{RESET}")
                      
            elif text == '/work':
                print(f"{RED}{'-'*50}")
                print(f"当前模型: {get_model()}")
                print(f"工作邮箱: {current_config.get('email', '未设置')}")
                print(f"今日日期: {datetime.datetime.now().strftime('%Y-%m-%d')}")
                from utils.workspace import WorkspaceManager
                ws = WorkspaceManager()
                commands = [
                    ("1. 简历优化", "optimize", "需要职位描述(JD)和简历内容", optimize_resume),
                    ("2. 简历摘要", "summarize", "需要简历内容", summarize_resume),
                    ("3. 生成求职信", "cover-letter", "需要职位描述(JD)和简历内容", generate_cover_letter),
                    ("4. 生成筛选条件", "filters", "需要简历内容生成SQL条件", resume_to_sql_filters),
                    ("5. 职位推荐", "recommend", "需要职位描述(JD)和简历内容", generate_recommendation),
                    ("6. 提取联系信息", "contact", "需要职位描述(JD)", extract_contact_and_send),
                    ("7. 发送邮件", "send-email", "需要收件人地址、主题和正文", send_email)
                ]

                # 构造动态系统提示
                # 获取最新工作区状态
                resumes = ws.get_resumes()
                jds = ws.get_jds()
                system_msg = f'''你是一位招聘助手，当前工作区状态：
📁 简历文件：{len(resumes)}份 ({'✅' if len(resumes)>=1 else '❌'})
📄 JD文件：{len(jds)}份 ({'✅' if len(jds)>=1 else '❌'})

## System Prompt for AI Recruitment Assistant

You are a recruitment assistant.

Your role is to process user instructions regarding job applications, candidate resumes, and job descriptions (JDs). You can either answer user questions or trigger specific local functions.

### Output Format

* **Always respond using Markdown format**.
* **When invoking local functionality**, use the custom code block with language identifier `command`, e.g.:

```command
<command content here>
```

---

### Available Local Functions

#### 1. 提取联系方式（Extract contact info from text）

Input: Free-form text

#### 2. 写推荐信并发邮件（Generate and email cover letter）

Inputs:

* 简历信息（Resume, local file or text）
* JD信息（Job description, local file or text）
* HR邮箱地址（email address）

#### 3. JD生成数据库过滤项并查询（Generate and execute SQL based on JD）

Inputs:

* JD信息（local file or text）
* （可选）数据库连接信息（如果未设置，则提示设置）

#### 4. 优化简历以匹配JD（Optimize resume based on JD）

Inputs:

* JD信息（local file or text）
* 简历信息（local file or text）

#### 5. 简历脱敏摘要并发布（Summarize and anonymize resume for publishing）

Input:

* 简历信息（local file or text）

---

### Interaction Requirements

1. Before invoking a function, **confirm the required input parameters** with the user.
2. If resume or JD file is missing, **prompt the user to provide the text directly**.
3. Keep responses **concise**, **precise**, and **easy to follow**.
4. **Only output the command block and required parameters** for local functions—**no extra explanation**.


当前工作区文件：
{chr(10).join(ws.list_files()) or "暂无文件"}'''
                
                while True:
                    try:
                        # 工作命令子菜单提示符
                        # 获取最新工作区文件
                        from utils.workspace import WorkspaceManager
                        ws = WorkspaceManager()
                        workspace_files = ws.list_files()
                        
                        print(f"{RED}{'-'*50}{RESET}")
                        if workspace_files:
                            print(f"{RED}当前工作区文件：")
                            for f in workspace_files:
                                print(f"  {f}")
                        print(f"{RED}{'-'*50}{RESET}")
                        cmd_input = session.prompt('work> ').strip()
                        if cmd_input.startswith('/'):
                            text = cmd_input  # 将命令传递回主循环
                            break
                        if cmd_input == '0':
                            break
                            
                        # 处理数字选择
                        if cmd_input.isdigit():
                            index = int(cmd_input) - 1
                            if 0 <= index < len(commands):
                                _, cmd_name, params_needed, cmd_func = commands[index]
                                print(f"\n执行 {cmd_name} 命令（{params_needed}）")
                                
                                # 收集所需参数
                                params = []
                                for param in params_needed.split("和"):
                                    param = param.replace("需要", "").strip()
                                    param_input = session.prompt(f"请输入 {param}: ")
                                    params.append(param_input.strip())
                                
                                # 执行命令并显示结果
                                result = cmd_func(*params)
                                print(f"\n执行结果：\n{result}\n")
                            else:
                                print("错误：请输入有效的编号")
                            continue
                            
                        # 处理自然语言输入
                        system_msg = (
                            "你是一个招聘助手，可以执行以下功能：\n" +
                            "\n".join([f"{i+1}. {desc[3:]}（需要参数：{params}）" 
                                    for i, (desc, _, params, _) in enumerate(commands)]) +
                            "\n请根据用户需求引导完成参数输入"
                        )
                        
                        # 保持对话上下文
                        messages = [{"role": "system", "content": system_msg}]
                        while True:
                            messages.append({"role": "user", "content": cmd_input})
                            response = completion(
                                model=get_model(),
                                messages=messages
                            )
                            ai_reply = response.choices[0].message.content
                            print(f"助理：{ai_reply}")
                            
                            # 解析Markdown命令块
                            import re
                            command_match = re.search(r'```command\n(.*?)\n```', ai_reply, re.DOTALL)
                            if command_match:
                                command_line = command_match.group(1).strip()
                                cmd_name, *args = command_line.split()
                                
                                # 找到对应的命令函数
                                cmd_func = next((c[3] for c in commands if c[1] == cmd_name), None)
                                if not cmd_func:
                                    print(f"错误：未知命令 {cmd_name}")
                                    break
                                    
                                # 执行命令（参数从工作区自动获取）
                                try:
                                    result = cmd_func()
                                    print(f"\n执行结果：\n{result}\n")
                                except Exception as e:
                                    print(f"执行出错：{str(e)}")
                                break
                                
                            # 继续收集参数
                            next_input = session.prompt('> ').strip()
                            if next_input.lower() == '取消':
                                print("命令已取消")
                                break
                            cmd_input = next_input
                            
                    except (KeyboardInterrupt, EOFError):
                        break
                    except Exception as e:
                        print(f"执行出错：{str(e)}")
            else:
                print("请输入以'/'开头的有效命令或直接回车执行工作区分析")
                print("请输入以'/'开头的有效命令")
                print("输入/help查看所有命令")
                
        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"出错：{str(e)}")


# 文件格式转换功能
def convert_pdf_to_md(pdf_path, output_path):
    """转换PDF文件到Markdown格式"""
    from pdfminer.high_level import extract_text
    text = extract_text(pdf_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

def convert_docx_to_md(docx_path, output_path):
    """转换DOCX文件到Markdown格式"""
    from docx import Document
    doc = Document(docx_path)
    text = '\n'.join([para.text for para in doc.paragraphs])
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

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
        
        result = optimize_resume(jd_content, resume_content)
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
        app.run(debug=True)
        webbrowser.open('http://localhost:5000')
    else:
        chat_mode()
