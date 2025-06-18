# airecruit.py

import os
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion
from diff_match_patch import diff_match_patch
import shlex
from flask import Flask, request, jsonify, render_template
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from pathlib import Path
from config import load_config, save_config, set_model, get_model

from commands import (
    optimize_resume,
    generate_cover_letter,
    summarize_resume,
    resume_to_sql_filters,
    generate_recommendation,
    extract_contact_and_send
)

# Load environment variables
load_dotenv()

config = load_config()

def chat_mode():
    """交互式聊天模式"""
    session = PromptSession(history=FileHistory('.airecruit_history'))
    workspace_files = config.get('workspace_files', [])
    
    print("欢迎进入AI招聘助手聊天模式（输入/help查看帮助）")
    while True:
        try:
            text = session.prompt('> ')
            
            if text.startswith('/add'):
                parts = text.split()
                if len(parts) < 2:
                    print("错误：请指定要添加的文件，格式为/add <文件路径>...")
                    continue
                files = parts[1:]
                added = []
                for f in files:
                    if Path(f).exists():
                        workspace_files.append(str(Path(f).resolve()))
                        added.append(f)
                workspace_files = list(set(workspace_files))  # 去重
                config['workspace_files'] = workspace_files
                save_config(config)
                print(f"已添加文件到工作区：{', '.join(added)}")
                
            elif text.startswith('/model'):
                parts = text.split(maxsplit=1)
                if len(parts) < 2:
                    print("错误：请指定模型名称，格式为/command <模型名称>")
                    continue
                new_model = parts[1]
                try:
                    set_model(new_model)
                    print(f"模型已设置为：{new_model}")
                except ValueError as e:
                    print(f"无效的模型格式：{str(e)}")
                
            elif text == '/exit':
                break
                
            elif text == '/help':
                print("可用命令：\n"
                      "/add <文件>... 添加文件到工作区\n"
                      "/model <模型名称> 设置LLM模型\n"
                      "/exit 退出\n"
                      "/help 显示帮助")
                      
            else:
                # 构造包含工作区文件的上下文
                context = []
                for f in workspace_files:
                    try:
                        with open(f) as file:
                            context.append(f"文件 {f} 内容：\n{file.read()}")
                    except Exception as e:
                        print(f"读取文件 {f} 出错：{str(e)}")
                
                response = completion(
                    model=get_model(),
                    messages=[
                        {"role": "system", "content": "你是一个招聘助手，当前工作区文件：\n" + '\n'.join(context)},
                        {"role": "user", "content": text}
                    ]
                )
                print(response.choices[0].message.content)
                
        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"出错：{str(e)}")


# Resume format conversion (PDF to Markdown)
def convert_pdf_to_md(pdf_path, output_path):
    from pdfminer.high_level import extract_text
    text = extract_text(pdf_path)
    with open(output_path, 'w') as f:
        f.write(text)

# Local web server with Flask
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/api/optimize", methods=["POST"])
def api_optimize():
    jd = request.json["jd"]
    resume = request.json["resume"]
    result = optimize_resume(jd, resume)
    return jsonify({"optimized": result})

# CLI
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Recruit Assistant")
    parser.add_argument("--server", action="store_true", help="Start local web server")
    parser.add_argument("-m", "--model", type=str, help="Set LLM model")
    args = parser.parse_args()

    if args.model:
        set_model(args.model)
        print(f"模型已设置为：{args.model}")
    elif args.server:
        app.run(debug=True)
    else:
        chat_mode()
