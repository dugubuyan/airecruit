from flask import Flask, request, jsonify, render_template
from pathlib import Path
from utils.workspace import WorkspaceManager
from config import load_config, set_model, set_smtp_config,get_model
from capacity.send_email import send_email
import datetime
import re
import json
from llm import get_system_prompt
from litellm import completion

app = Flask(__name__, template_folder='../templates')

@app.route("/")
def index():
    config = load_config()
    ws = WorkspaceManager()
    return render_template("index.html", 
                         config=config,
                         available_files=ws.get_raw_files(),
                         workspace_files=ws.list_files(),
                         today_date=datetime.date.today().strftime('%Y-%m-%d'))

@app.route("/api/add_file", methods=["POST"])
def api_add_file():
    ws = WorkspaceManager()
    if 'files' not in request.files:
        return jsonify({"error": "No files uploaded"}), 400
    
    try:
        # 确保工作目录存在
        work_dir = Path("workdir")
        work_dir.mkdir(exist_ok=True)
        
        file_type = request.form.get('file_type', 'auto')  # 获取用户选择的类型
        
        for file in request.files.getlist('files'):
            # 处理文件逻辑与命令行模式一致
            file_path = work_dir.resolve() / file.filename
            file.save(str(file_path))
            
            # PDF/DOCX文件转换逻辑
            if file_path.suffix.lower() in ('.pdf', '.docx'):
                md_path = file_path.with_suffix('.md')
                try:
                    if file_path.suffix.lower() == '.pdf':
                        from utils.file_utils import convert_pdf_to_md
                        convert_pdf_to_md(str(file_path), str(md_path))
                    else:
                        from utils.file_utils import convert_docx_to_md
                        convert_docx_to_md(str(file_path), str(md_path))
                    ws.add_file(str(md_path), file_type)
                except Exception as e:
                    return jsonify({"error": f"文件转换失败: {str(e)}"}), 500
            # 文本文件直接添加
            elif file_path.suffix.lower() in ('.txt', '.md'):
                ws.add_file(str(file_path.resolve()), file_type)
            else:
                return jsonify({"error": f"不支持的文件类型: {file_path.suffix}"}), 400
        return jsonify({"status": "added", "count": len(request.files.getlist('files'))})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/update_config", methods=["POST"], strict_slashes=False)
def api_update_config():
    key = request.json.get("key")
    value = request.json.get("value")
    
    if not key or value is None:
        return jsonify({"error": "Missing key or value"}), 400
        
    try:
        if key == "model":
            set_model(value)
        elif key == "email":
            # 从请求体中获取完整的SMTP配置
            set_smtp_config(
                sender_email=request.json.get("value").get("sender_email"),
                sender_password=request.json.get("value").get("sender_password"),
                smtp_server=request.json.get("value").get("smtp_server"),
                smtp_port=int(request.json.get("value").get("smtp_port", 587))
            )
        return jsonify({"status": "updated", key: value})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/files", methods=["GET"])
def api_files():
    ws = WorkspaceManager()
    # 保持与命令行模式一致的返回格式（仅文件路径列表）
    return jsonify([f['path'] for f in ws.config['workspace_files']])

@app.route("/api/chat", methods=["POST"])
def api_chat():
    ws = WorkspaceManager()
    data = request.json
    message = data.get('message')
    
    resumes = ws.get_resumes()
    jds = ws.get_jds()
    system_msg = get_system_prompt(resumes, jds)
    
    # 获取完整对话历史（包含之前的多轮对话）
    chat_history = data.get('history', [])
    
    # 构建消息数组：系统提示 + 历史对话 + 最新消息
    messages = [{"role": "system", "content": system_msg}]
    for entry in chat_history:
        messages.append({"role": entry['role'], "content": entry['content']})
    messages.append({"role": "user", "content": message})
    
    try:
        # 调用AI接口
        response = completion(
            model=get_model(),
            messages=messages,
            temperature=0.3
        )
        ai_reply = response.choices[0].message.content
        
        # 解析并执行操作指令
        operation = None
        operation_match = re.search(r'```json\n(.*?)\n```', ai_reply, re.DOTALL)
        if operation_match:
            operation_content = operation_match.group(1).strip()
            operation = json.loads(operation_content)
            ai_reply = ai_reply.replace(operation_match.group(0), '').strip()

            # 执行实际操作（与命令行模式一致）
            try:
                if operation['action'] == 'export2pdf':
                    from capacity.pdf_export import export_to_pdf
                    # 从工作区获取最新内容
                    pdf_path = export_to_pdf(operation.get('md_content', ''))  
                    ai_reply += f"\n\nPDF已生成：{pdf_path}"
                elif operation['action'] == 'send_email':
                    from capacity.send_email import send_email
                    # 直接使用operation中的字段而非params
                    send_email(
                        recipient=operation['recipient'],
                        subject=operation.get('subject', '求职申请材料'),
                        body=operation['body'],
                        has_attachment=operation.get('has_attachment', False)
                    )
                    ai_reply += f"\n\n邮件已发送至：{operation['recipient']}"
            except Exception as e:
                ai_reply += f"\n\n操作执行失败：{str(e)}"
            
        return jsonify({"reply": ai_reply})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/remove_file", methods=["POST"])
def api_remove_file():
    ws = WorkspaceManager()
    index = request.json.get("index")
    if index is None or index < 0 or index >= len(ws.config['workspace_files']):
        return jsonify({"error": "无效的文件索引"}), 400
    
    try:
        file_path = ws.config['workspace_files'][index]['path']
        # 直接调用工作区管理器的移除方法（保持与命令行模式一致）
        ws.remove_files([file_path])
        
        # 保持与命令行模式一致的文件移除逻辑（仅从工作区移除，不删除实际文件）
        return jsonify({
            "status": "removed",
            "path": file_path,
            "new_files": [Path(f['path']).name for f in ws.config['workspace_files']]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


