# AI Recruit Assistant 智能求职助手

[English](#english-version) | [中文](#中文版)

---

## English Version

### 📝 Project Overview
An AI-powered recruitment assistant tool that provides resume optimization, job matching, and automated application features. Supports both CLI and web interface.

### 🚀 Features
- Resume Optimization (CLI: `optimize`, Web: `/api/optimize`)
- Resume Summarization (CLI: `summarize`)
- Cover Letter Generation (CLI: `cover-letter`)
- JD-based Filter Generation (CLI: `filters`)
- Position Recommendation (CLI: `recommend`)
- Contact Extraction & Email (CLI: `contact`)
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
# 进入交互式命令行模式
python airecruit.py
# 使用/work命令开始工作流程
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
- 简历优化（命令行: `/work`, 网页: `/api/optimize`）(开发中)
- 简历摘要生成（命令行: `summarize`）
- 求职信生成（命令行: `cover-letter`）
- 职位过滤器生成（命令行: `filters`）
- 职位推荐（命令行: `recommend`）
- 联系方式提取（命令行: `contact`）
- 网页管理界面

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
python airecruit.py optimize resume.pdf
python airecruit.py cover-letter --template=tech.md
```

#### 网页模式
```bash
python airecruit.py
# 访问 http://localhost:5000
```

### ⚙ 配置说明
修改`.config.json`文件设置：
- AI模型偏好
- 邮件模板
- 工作区路径

### 🤝 贡献指南
1. Fork 本仓库
2. 新建功能分支
3. 提交包含完整描述的PR

_License: MIT_
