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
from config import load_config, save_config, set_model, get_model, set_mode, get_mode,set_smtp_config
from llm import get_system_prompt
from utils.file_utils import (
    convert_pdf_to_md,
    convert_docx_to_md,
)
from capacity import (
    pdf_export,
    send_email
)
import warnings

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="Pydantic serializer warnings:"
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
    from commands import (
        handle_file_command,
        handle_model_command,
        handle_work_command,
        handle_mode_command,
        handle_exit_command,
        handle_help_command
    )
    ws = WorkspaceManager()
    workspace_files = ws.list_files()
    print("欢迎进入AI招聘助手工作模式（输入/help查看帮助）")
    current_config = load_config()
    text = ''
    while True:
        print(f"{RED}{'-'*50}")
        print(f"当前模式: {get_mode()}模式")
        print(f"当前模型: {current_config.get('model', '未设置')}")
        print(f"工作邮箱: {current_config.get('email', '未设置')}")
        print(f"今日日期: {datetime.datetime.now().strftime('%Y-%m-%d')}")
        # print(f"{'-'*50}{RESET}")
        try:
            # 显示工作区文件和红色分隔线
            print(f"{RED}{'-'*50}")
            if workspace_files:
                print(f"{RED}工作区文件：" + ", ".join([f for f in workspace_files]) + f"{RESET}")
            text = session.prompt('> ') if not text else text
            if not text.strip():
                print("请问您需要我做什么？")
                continue
            
            if text == '/file':
                while True:
                    # 进入文件管理子菜单
                    print(f"\n{RED}文件管理操作（当前工作区文件：{len(workspace_files)}个）{RESET}")
                    print("1. 扫描并添加文件 - 从workdir目录添加文件到工作区")
                    print("2. 列出工作区文件 - 显示已添加的文件及其类型")
                    print("3. 移除工作区文件 - 从工作区删除指定文件")
                    print(f"{RED}0. 返回主菜单{RESET}")
                    print(f"{RED}提示：支持的文件类型：PDF/DOCX/MD/TXT{RESET}")
                    try:
                        # 文件子菜单提示符
                        print(f"{RED}{'-'*50}{RESET}")
                        if workspace_files:
                            print(f"{RED}工作区文件：" + ", ".join([f for f in workspace_files]) + f"{RESET}")
                        choice = session.prompt('file> ')
                        if not choice:
                            print("请问您需要我做什么？")
                            continue
                        if choice.startswith('/'):
                            text = choice  # 将命令传递回主循环
                            break
                        if choice == '0':
                            text = ''
                            break
                        
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
                                    # with open(file_path, 'r', encoding='utf-8') as f:
                                    #     content = f.read()
                                    
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
                                workspace_files = ws.list_files()  # 刷新文件列表
                                continue  # 添加成功后返回主菜单
                                
                        elif choice == '2':
                            pass  # 前面已经显示过文件列表
                            
                        elif choice == '3':
                            # 获取原始文件路径列表
                            all_files = [f['path'] for f in ws.config['workspace_files']]
                            if not all_files:
                                print("工作区中没有文件可移除")
                                continue
                                
                            print("\n当前工作区文件：")
                            for i, path in enumerate(all_files, 1):
                                print(f"{i}. {Path(path).name}")
                                
                            to_remove = session.prompt("请输入要移除的文件编号（多个用空格分隔）: ")
                            if not to_remove.strip():
                                print("操作已取消")
                                continue
                                
                            try:
                                indexes = [int(i) for i in to_remove.split()]
                                # 验证编号有效性
                                if any(i < 1 or i > len(all_files) for i in indexes):
                                    raise ValueError("编号超出范围")
                                    
                                selected_paths = [all_files[i-1] for i in indexes]
                                removed_files = [Path(p).name for p in selected_paths]
                                
                                # 通过WorkspaceManager更新工作区文件
                                ws.remove_files(selected_paths)
                                # 刷新工作区文件列表
                                workspace_files = ws.list_files()
                                print(f"\n✅ 已移除文件：{', '.join(removed_files)}")
                            except (ValueError, IndexError):
                                print("错误：请输入有效的文件编号")
                                
                        else:
                            print("错误：无效选项，请输入 0-3 的数字")
                        continue
                    except (KeyboardInterrupt, EOFError):
                        break
                
            elif text.startswith('/model'):
                handle_model_command(text, session)
                text = ''
                
            elif text.startswith('/mode'):
                handle_mode_command(text, session)
                text = ''
                
            elif text == '/exit':
                if handle_exit_command():
                    break
                text = ''
                
            elif text == '/help':
                handle_help_command()
                text = ''
                
            elif text == '/work':
                handle_work_command(session, ws, current_config)
                text = ''
            else:
                # 非命令输入自动进入工作模式
                text = '/work'
                continue
                
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
    return jsonify({"optimized": 'success'})
    # try:
    #     # 从工作区获取最新简历和JD
    #     resumes = ws.get_resumes()
    #     jds = ws.get_jds()
        
    #     if not resumes or not jds:
    #         return jsonify({"error": "需要至少一份简历和职位描述"}), 400
            
    #     # 使用第一个找到的简历和JD
    #     resume_path = resumes[0]
    #     jd_path = jds[0]

    #     with open(resume_path, 'r', encoding='utf-8') as f:
    #         resume_content = f.read()
    #     with open(jd_path, 'r', encoding='utf-8') as f:
    #         jd_content = f.read()
        
    #     result = optimize_resume.optimize_resume(jd_content, resume_content)
    #     return jsonify({"optimized": result})
        
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

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
