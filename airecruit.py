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
