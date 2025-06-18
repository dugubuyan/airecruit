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
    from prompt_toolkit.completion import WordCompleter
    command_completer = WordCompleter([
        '/file', '/model', '/work', '/exit', '/help'
    ], ignore_case=True)
    
    session = PromptSession(
        history=FileHistory('.airecruit_history'),
        completer=command_completer
    )
    workspace_files = config.get('workspace_files', [])
    
    print("欢迎进入AI招聘助手聊天模式（输入/help查看帮助）")
    while True:
        try:
            text = session.prompt('> ')
            
            elif text.startswith('/file'):
                parts = text.split(maxsplit=2)
                if len(parts) < 2:
                    print("文件操作命令格式：/file <add|ls|drop> [参数]")
                    continue
                
                subcmd = parts[1].lower()
                
                if subcmd == 'add':
                    if len(parts) < 3:
                        print("错误：请指定要添加的文件，格式为/file add <文件路径>...")
                        continue
                    files = parts[2].split()
                added = []
                for f in files:
                    file_path = Path(f)
                    if not file_path.exists():
                        print(f"文件不存在：{f}")
                        continue
                    
                    # 转换并添加文件
                    if file_path.suffix.lower() in ('.pdf', '.docx'):
                        # 生成对应的md文件路径
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
                        workspace_files.append(str(file_path.resolve()))
                        added.append(str(file_path))
                    else:
                        print(f"跳过不支持的文件类型：{file_path.suffix}")
                workspace_files = list(set(workspace_files))  # 去重
                config['workspace_files'] = workspace_files
                save_config(config)
                print(f"已添加文件到工作区：{', '.join(added)}")
                
            elif text.startswith('/model'):
                parts = text.split(maxsplit=1)
                if len(parts) < 2:
                    print("错误：命令格式为/model <ls|模型名称>")
                    continue
                
                if parts[1].lower() == 'ls':
                    print("支持的模型列表：")
                    for model in config.get('supported_models', []):
                        print(f"- {model}")
                    continue
                
                new_model = parts[1]
                try:
                    if new_model not in config.get('supported_models', []):
                        raise ValueError(f"不支持该模型，请使用/model ls查看支持列表")
                    set_model(new_model)
                    print(f"模型已设置为：{new_model}")
                except ValueError as e:
                    print(f"错误：{str(e)}")
                
            elif text == '/exit':
                break
                
            elif text == '/help':
                print("可用命令：\n"
                      "/add <文件路径>...   添加文件到工作区（支持pdf/docx/txt/md）\n" 
                      "/ls                显示工作区文件\n"
                      "/model <模型名称>   设置LLM模型（格式：provider/model:version）\n"
                      "/exit              退出程序\n"
                      "/help             显示帮助信息")
                      
            elif text.startswith('/work'):
                parts = text.split(maxsplit=2)
                if len(parts) < 2:
                    print("工作命令格式：/work <command> [参数]")
                    print("可用命令：" + ", ".join(WORK_COMMANDS))
                    continue
                
                command = parts[1].lower()
                args = parts[2] if len(parts) > 2 else ""
                
                try:
                    if command == 'optimize':
                        # 示例参数解析逻辑
                        params = args.split(';')
                        if len(params) < 2:
                            raise ValueError("需要JD和简历参数，格式：optimize <JD> ; <resume>")
                        result = optimize_resume(params[0], params[1])
                        print("优化结果：\n" + result)
                    # 其他命令处理逻辑...
                    else:
                        print(f"未知工作命令：{command}")
                except Exception as e:
                    print(f"执行命令出错：{str(e)}")
            
            elif text.startswith('/file'):
                # 已处理的file命令分支
                pass
            elif text.startswith('/'):
                print(f"未知命令：{text.split()[0]}")
                print("请输入有效命令，可用命令列表：")
                print("/file, /model, /work, /exit, /help")
                
            else:
                # 构造包含工作区文件的上下文
                context = []
                for f in workspace_files:
                    try:
                        file_path = Path(f)
                        # 只处理文本文件和PDF文件
                        if file_path.suffix.lower() in ('.txt', '.md'):
                            with open(f, 'r', encoding='utf-8') as file:
                                context.append(f"文件 {f} 内容：\n{file.read()}")
                        elif file_path.suffix.lower() == '.pdf':
                            # 使用临时文件保存转换后的文本
                            temp_md = file_path.with_suffix('.temp.md')
                            convert_pdf_to_md(f, temp_md)
                            with open(temp_md, 'r', encoding='utf-8') as file:
                                context.append(f"PDF文件 {f} 转换内容：\n{file.read()}")
                            temp_md.unlink()  # 删除临时文件
                        else:
                            print(f"跳过不支持的文件类型：{f}")
                    except Exception as e:
                        print(f"处理文件 {f} 出错：{str(e)}")
                
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
