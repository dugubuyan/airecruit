from core.utils import confirm_action

def handle_exit_command():
    """处理退出命令"""
    if confirm_action("确定要退出吗？"):
        print("再见！")
        return True
    return False
