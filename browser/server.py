from flask import Flask, request, jsonify, render_template
from utils.workspace import WorkspaceManager
from config import load_config
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
    file_path = request.json.get("path")
    if not file_path:
        return jsonify({"error": "Missing file path"}), 400
    ws.add_file(file_path, "auto")
    return jsonify({"status": "added", "path": file_path})

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
            # 保持与命令行模式一致的SMTP配置处理
            current_smtp = load_config().get("smtp_config", {})
            set_smtp_config(
                sender_email=value,
                sender_password=current_smtp.get("sender_password", ""),
                smtp_server=current_smtp.get("smtp_server", ""),
                smtp_port=current_smtp.get("smtp_port", 587)
            )
        return jsonify({"status": "updated", key: value})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/files", methods=["GET"])
def api_files():
    ws = WorkspaceManager()
    return jsonify(ws.list_files())

@app.route("/api/optimize", methods=["POST"])
def api_optimize():
    try:
        ws = WorkspaceManager()
        resumes = ws.get_resumes()
        jds = ws.get_jds()
        
        if not resumes or not jds:
            return jsonify({"error": "需要至少一份简历和职位描述"}), 400
            
        with open(resumes[0], 'r', encoding='utf-8') as f:
            resume_content = f.read()
        with open(jds[0], 'r', encoding='utf-8') as f:
            jd_content = f.read()
        
        result = optimize_resume(jd_content, resume_content)
        return jsonify({"optimized": result})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate_recommendation", methods=["POST"])
def api_generate_recommendation():
    try:
        ws = WorkspaceManager()
        resumes = ws.get_resumes()
        data = request.json
        
        if not resumes:
            return jsonify({"error": "需要至少一份简历"}), 400
            
        with open(resumes[0], 'r', encoding='utf-8') as f:
            resume_content = f.read()
        
        recommendation = generate_recommendation(
            content=data.get('content', ''),
            resume=resume_content
        )
        
        # 发送邮件
        if data.get('send_email'):
            send_email(
                recipient=data['email'],
                subject=f"推荐信 - {datetime.date.today().strftime('%Y-%m-%d')}",
                body=recommendation,
                has_attachment=True
            )
        
        return jsonify({"recommendation": recommendation})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
