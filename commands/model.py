from config import load_config, set_model

def handle_model_command(command_text, session):
    """处理模型相关命令"""
    parts = command_text.split(maxsplit=1)
    if len(parts) < 2:
        print("错误：命令格式为/model <ls|模型名称>")
        return

    if parts[1].lower() == 'ls':
        print("支持的模型列表：")
        current_config = load_config()
        for model in current_config.get('supported_models', []):
            print(f"- {model}")
        return

    new_model = parts[1]
    try:
        if new_model not in load_config().get('supported_models', []):
            raise ValueError(f"不支持该模型，请使用/model ls查看支持列表")
        set_model(new_model)
        print(f"模型已设置为：{new_model}")
    except ValueError as e:
        print(f"错误：{str(e)}")
