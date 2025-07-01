from config import set_mode, get_mode

def handle_mode_command(command_text, session):
    """处理模式切换命令"""
    parts = command_text.split(maxsplit=1)
    if len(parts) < 2:
        print(f"当前模式: {get_mode()}模式")
        print("使用方法: /mode <candidate|hunter>")
        return

    try:
        set_mode(parts[1].lower())
        print(f"工作模式已设置为: {parts[1]}模式")
    except ValueError as e:
        print(f"错误: {str(e)}")
