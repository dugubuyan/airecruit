# AI Recruit Assistant 智能求职助手

[English](#english-version) | [中文](#中文版)

---
## Examples


https://github.com/user-attachments/assets/bdadbdda-edde-48c7-8b9d-8da520bf3da0


## English Version

### 📝 Project Overview
An AI-powered recruitment assistant tool that provides resume optimization, job matching, and automated application features. Supports both CLI and web interface.

### 🚀 Features
- Resume Optimization
- Resume Summarization
- Cover Letter Generation & Send Email
- JD-based Filter Generation 
- Position Recommendation
- Contact Extraction & Send Email 
- Web-based Management Interface

### 📦 Installation
```bash
git clone https://github.com/your-username/airecruit.git
cd airecruit
pip install -r requirements.txt
```

### 🛠 Usage
#### CLI Mode
```bash
# Example commands
# chat mode
python airecruit.py
# use /work to begin
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
- Email templates
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

### 📦 安装步骤
```bash
git clone [项目仓库地址]
cd airecruit
pip install -r requirements.txt
```

### 🛠 使用指南
#### 命令行模式
```bash
# 示例命令
python airecruit.py
# 使用/work命令开始工作流程
>/work
```

#### 网页模式
```bash
python airecruit.py
# 访问 http://localhost:5000
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
