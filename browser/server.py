from flask import Flask, request, jsonify, render_template
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
        for file in request.files.getlist('files'):
            # 保存文件到工作目录
            file_path = str(Path(ws.workdir) / file.filename)
            file.save(file_path)
            ws.add_file(file_path, "auto")
        return jsonify({"status": "added", "count": len(request.files.getlist('files'))})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/update_config", methods=["POST"])
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
                sender_email=value.get("sender_email"),
                sender_password=value.get("sender_password"),
                smtp_server=value.get("smtp_server"),
                smtp_port=int(value.get("smtp_port", 587))
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
    ws.remove_files([file_path])
    return jsonify({"status": "removed", "path": file_path})


