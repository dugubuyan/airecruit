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
        handle_exit_command,
        handle_file_command,
        handle_help_command,
        handle_mode_command,
        handle_model_command,
        handle_work_command
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
                text = handle_file_command(session, ws)
                
            elif text.startswith('/model'):
                handle_model_command(text, session)
                text = ''
                
            elif text.startswith('/mode'):
                handle_mode_command(text, session)
                text = ''
                
            elif text == '/exit':
                if handle_exit_command():
                    break
                
            elif text == '/help':
                handle_help_command()
                text = ''
                
            elif text == '/work':
                text = handle_work_command(session, ws, current_config)
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
