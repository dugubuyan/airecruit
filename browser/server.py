from flask import Flask, request, jsonify, render_template
from pathlib import Path
from utils.workspace import WorkspaceManager
from config import load_config, set_model, set_smtp_config
from capacity.send_email import send_email
import datetime

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
                    ws.add_file(str(md_path), 'auto')
                except Exception as e:
                    return jsonify({"error": f"文件转换失败: {str(e)}"}), 500
            # 文本文件直接添加
            elif file_path.suffix.lower() in ('.txt', '.md'):
                ws.add_file(str(file_path.resolve()), 'auto')
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

@app.route("/api/remove_file", methods=["POST"])
def api_remove_file():
    ws = WorkspaceManager()
    file_path = request.json.get("path")
    if not file_path:
        return jsonify({"error": "Missing file path"}), 400
    
    try:
        # 直接调用工作区管理器的移除方法（保持与命令行模式一致）
        ws.remove_files([file_path])
        
        # 返回更新后的文件列表
        return jsonify({
            "status": "removed",
            "path": file_path,
            # 返回原始文件名列表（与命令行模式显示一致）
            "new_files": [f['path'] for f in ws.config['workspace_files']]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


