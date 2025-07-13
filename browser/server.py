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
        Path(ws.workdir).mkdir(parents=True, exist_ok=True)
        
        for file in request.files.getlist('files'):
            # 保存文件到工作目录（绝对路径）
            file_path = str(Path(ws.workdir).resolve() / file.filename)
            file.save(file_path)
            ws.add_file(file_path, "auto")
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
    return jsonify(ws.list_files())

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


