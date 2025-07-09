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
from utils.workspace import WorkspaceManager
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from config import load_config, save_config, set_model, get_model, set_smtp_config
from llm import get_system_prompt

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
    from utils.workspace import WorkspaceManager
    from commands import (
        handle_exit_command,
        handle_file_command,
        handle_help_command,
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
            break



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
        from browser.server import app
        import webbrowser
        webbrowser.open('http://localhost:5001')
        app.run(host='0.0.0.0', port=5001, debug=True)
    else:
        chat_mode()
