# AI Recruit Assistant 智能求职助手

[English](#english-version) | [中文](#中文版)

---
## Examples


https://github.com/user-attachments/assets/bdadbdda-edde-48c7-8b9d-8da520bf3da0


## English Version

### 📝 Project Overview
An intelligent job-seeking assistant tool that provides resume optimization, position matching, and automated application features. Supports both command-line and web interfaces.

### 🚀 Features
- JD-based resume optimization with export to PDF
- Cover letter generation
- Automated email sending to HR (automatically extracts HR email from JD)
- Web-based interface operation
- Natural language conversation interface, no need to remember commands

### 🧱 Prerequisites
Ensure you have Python installed (recommended: Python 3.10+).We also recommend using a virtual environment to avoid dependency conflicts.

#### Create and activate a virtual environment
```bash
# Create a virtual environment
python3 -m venv airecruit
# Activate it (Linux/macOS)
source airecruit/bin/activate
# Or on Windows
airecruit\Scripts\activate
```

### 📦 Installation
```bash
git clone https://github.com/dugubuyan/airecruit
cd airecruit
pip install -r requirements.txt
```

### 🛠 Usage
If not using local ollama models, please set up the LLM API key environment variable first. Reference: https://docs.litellm.ai/docs/providers
#### CLI Mode
```bash
# Example commands
python airecruit.py
# Use /work command to start workflow
>/work
```

#### Web Mode
```bash
python airecruit.py --browser
# 访问 http://localhost:5001
```

### ⚙ Configuration
Edit `.config.json` to set:
- AI model preferences
- Email settings
- Workspace paths

### 🤝 Contributing
1. Fork the repository
2. Create feature branch
3. Submit PR with description

---

## 中文版

### 📝 项目概述
智能求职辅助工具，提供简历优化、职位匹配和自动化申请功能。支持命令行和网页双界面。

### 🚀 功能列表
- 根据JD来优化简历，优化后的简历可导出为pdf文件
- 生成求职信
- 发送邮件到hr（自动从JD中提取hr邮箱地址）
- 可以网页界面操作
- 自然语言对话操作，无需记任何命令

### 🧱 安装前提
请确保已安装 Python（推荐版本：Python 3.10 及以上）。建议使用虚拟环境来避免依赖冲突。

#### 创建并激活虚拟环境
```bash
# Create a virtual environment
python3 -m venv airecruit
# Activate it (Linux/macOS)
source airecruit/bin/activate
# Or on Windows
airecruit\Scripts\activate
```
### 📦 安装步骤
```bash
git clone https://github.com/dugubuyan/airecruit
cd airecruit
pip install -r requirements.txt
```

### 🛠 使用指南
如果不是ollama本地模型，请先设置大模型apikey环境变量，可参考https://docs.litellm.ai/docs/providers
#### 命令行模式
```bash
# 示例命令
python airecruit.py
# 使用/work命令开始工作流程
>/work
```

#### 网页模式
```bash
python airecruit.py --browser
# 访问 http://localhost:5001
```

### ⚙ 配置说明
修改`.config.json`文件设置：
- AI模型偏好
- 邮件地址配置
- 工作区路径

### 🤝 贡献指南
1. Fork 本仓库
2. 新建功能分支
3. 提交包含完整描述的PR

_License: MIT_
