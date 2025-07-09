from flask import Flask, request, jsonify, render_template
from utils.workspace import WorkspaceManager
from config import load_config
from capacity.optimize_resume import optimize_resume
from capacity.generate_recommendation import generate_recommendation
from capacity.send_email import send_email
import datetime

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/add_file", methods=["POST"])
def api_add_file():
    ws = WorkspaceManager()
    file_path = request.json.get("path")
    if not file_path:
        return jsonify({"error": "Missing file path"}), 400
    ws.add_file(file_path, "auto")
    return jsonify({"status": "added", "path": file_path})

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
