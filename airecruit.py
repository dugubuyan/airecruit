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
    
    print("欢迎进入AI招聘助手聊天模式（输入/help查看帮助）")
    print(f"{RED}{'-'*50}{RESET}")
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
                print("\n文件管理操作：")
                print("1. 添加文件到工作区")
                print("2. 列出工作区文件")
                print("3. 移除工作区文件")
                print("0. 返回主菜单")
                
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
                            
                    except (KeyboardInterrupt, EOFError):
                        break
                
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
                      "/file             文件管理菜单\n"
                      "/model ls         查看支持模型列表\n"
                      "/model <名称>     设置LLM模型\n"
                      "/work            进入工作命令菜单\n"
                      "/exit             退出程序\n"
                      "/help            显示帮助信息")
                      
            elif text == '/work':
                from utils.workspace import WorkspaceManager
                ws = WorkspaceManager()
                commands = [
                    ("1. 简历优化", "optimize", "需要职位描述(JD)和简历内容", optimize_resume),
                    ("2. 简历摘要", "summarize", "需要简历内容", summarize_resume),
                    ("3. 生成求职信", "cover-letter", "需要职位描述(JD)和简历内容", generate_cover_letter),
                    ("4. 生成筛选条件", "filters", "需要简历内容生成SQL条件", resume_to_sql_filters),
                    ("5. 职位推荐", "recommend", "需要职位描述(JD)和简历内容", generate_recommendation),
                    ("6. 提取联系信息", "contact", "需要职位描述(JD)", extract_contact_and_send)
                ]
                
                # 构造动态系统提示
                system_msg = f'''您正在使用AI招聘助手，当前工作区包含：
{len(ws.get_resumes())}份简历和{len(ws.get_jds())}份职位描述（JD）

请按以下步骤操作：
1. 告诉我您想完成的任务（例如："优化简历"）
2. 我会检查所需文件是否齐全
3. 如果文件不足，将引导您添加并分类文件
4. 确认后自动执行相应操作

支持的功能：
- 简历优化（需要1JD+1简历）
- 简历摘要（需要1简历）
- 生成求职信（需要1JD+1简历）
- 生成筛选条件（需要1简历） 
- 职位推荐（需要1JD+1简历）
- 提取联系信息（需要1JD）

当前工作区文件：
{chr(10).join(ws.list_files()) or "暂无文件"}'''
                
                while True:
                    try:
                        # 工作命令子菜单提示符
                        print(f"{RED}{'-'*50}{RESET}")
                        if workspace_files:
                            print(f"{RED}工作区文件：" + ", ".join([Path(f).name for f in workspace_files]) + f"{RESET}")
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
                            
                            # 检查是否完成参数收集
                            if "参数已齐全" in ai_reply:
                                # 提取参数并执行命令
                                cmd_index = int(ai_reply.split("执行命令")[1].split(":")[0].strip()) - 1
                                params = eval(ai_reply.split("参数：")[1].split("\n")[0].strip())
                                result = commands[cmd_index][3](*params)
                                print(f"\n执行结果：\n{result}\n")
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
