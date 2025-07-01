def handle_help_command():
    """显示帮助信息"""
    print("可用命令列表：\n"
          "/file       - 文件管理（添加/查看/删除工作区文件）\n"
          "/model ls   - 查看所有支持的AI模型列表\n" 
          "/model <名称> - 切换AI模型（需要先查看支持列表）\n"
          "/work      - 进入智能工作模式（简历优化/生成求职信等）\n"
          "/mode <candidate|hunter> - 切换候选人/猎头模式\n"
          "输入 /exit 退出程序")
