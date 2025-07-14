# 贡献指南

欢迎参与项目贡献！以下是提交 Issue 和 Pull Request 的指南：

## 提交 Issue
1. 在提交新 Issue 前，请先搜索是否已有相关议题
2. 清晰描述问题或建议（使用中文）
3. 如果是错误报告，请包括：
   - 复现步骤
   - 预期行为与实际行为
   - 环境信息（Python版本、操作系统等）

## 提交 Pull Request
1. Fork 仓库并创建新分支（分支名需描述修改内容）
2. 提交清晰的 commit 信息（使用中文）
3. 保持代码风格与项目一致
4. 更新相关文档（如有需要）
5. 确保所有测试通过
6. 在 PR 描述中关联相关 Issue（如有）

## 开发环境设置
```bash
git clone https://github.com/your-username/airecruit.git
cd airecruit
pip install -r requirements.txt
```

## 代码风格
- 遵循 PEP8 规范
- 使用 Google 风格 docstring
- 类型注解推荐用于公共接口
