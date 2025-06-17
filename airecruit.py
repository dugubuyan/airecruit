# airecruit.py

import os
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion
from diff_match_patch import diff_match_patch
from flask import Flask, request, jsonify, render_template
from config import load_config, save_config

# Load environment variables
load_dotenv()

config = load_config()

def set_model(model):
    config["model"] = model
    save_config(config)

def get_model():
    return config.get("model", "gpt-4")

# Resume Optimizer
def optimize_resume(jd, resume):
    prompt = f"根据以下职位描述优化简历内容，使其更符合岗位需求：\n职位描述：{jd}\n当前简历：{resume}"
    return completion(model=get_model(), messages=[{"role": "user", "content": prompt}])

# Cover Letter Generator
def generate_cover_letter(jd, resume):
    prompt = f"根据以下职位描述和简历生成一封cover letter：\n职位描述：{jd}\n简历：{resume}"
    return completion(model=get_model(), messages=[{"role": "user", "content": prompt}])

# Resume Summary
def summarize_resume(resume):
    prompt = f"请总结下面的简历内容，突出特点但隐藏敏感信息：\n{resume}"
    return completion(model=get_model(), messages=[{"role": "user", "content": prompt}])

# Resume Filters to SQL
def resume_to_sql_filters(resume):
    prompt = f"请为以下简历内容生成适用于BOSS直聘/猎聘的筛选条件，并生成SQL插入语句：\n{resume}"
    return completion(model=get_model(), messages=[{"role": "user", "content": prompt}])

# Recommendation Letter Generator
def generate_recommendation(jd, resume):
    prompt = f"根据以下职位描述和简历撰写推荐信：\n职位描述：{jd}\n简历：{resume}"
    return completion(model=get_model(), messages=[{"role": "user", "content": prompt}])

# Contact Info Extractor and Email Sender
def extract_contact_and_send(jd):
    prompt = f"提取以下职位描述中的联系邮箱或方式：\n{jd}"
    return completion(model=get_model(), messages=[{"role": "user", "content": prompt}])

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
        parser.print_help()
