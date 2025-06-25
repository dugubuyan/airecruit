import json
from pathlib import Path

CONFIG_FILE = '.config.json'

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
    
    # 默认配置
    default_config = {
        'default_model': 'ollama/mistral:7b-instruct',
        'last_model': None,
        'model': 'ollama/mistral:7b-instruct',
        'sender_email': '',
        'sender_password': '',
        'smtp_server': '',
        'smtp_port': 465,
        'workspace_files': [],
        'supported_models': [
            'ollama/mistral:7b-instruct',
            'openai/gpt-4',
            'anthropic/claude-2', 
            'cohere/command-nightly',
            'gemini/gemini-2.0-flash'
        ],
        'mode': 'candidate'
    }
    
    # 合并默认配置（保留现有配置字段）
    for key in default_config:
        if key not in config:
            config[key] = default_config[key]
    
    # 确保model字段是字符串类型
    if isinstance(config.get('model'), dict):
        config['model'] = config['model'].get('name', default_config['default_model'])
    elif not isinstance(config.get('model'), str):
        config['model'] = default_config['default_model']
        
    return config

def get_model():
    config = load_config()
    return config.get("model", "ollama/mistral:7b-instruct")

def set_model(model):
    # 放宽模型名称格式验证，允许无版本号
    if '/' not in model:
        raise ValueError("模型名称格式应为 provider/model[:version]")
    
    config = load_config()
    if model not in config.get('supported_models', []):
        raise ValueError(f"不支持该模型，请使用/model ls查看支持列表")
    config["model"] = model
    save_config(config)

def get_mode():
    """获取当前模式"""
    return "候选人" if 'candidate' == load_config().get('mode', 'candidate') else '猎头'

def set_mode(mode):
    """设置工作模式"""
    valid_modes = ['candidate', 'hunter']
    if mode not in valid_modes:
        raise ValueError(f"无效模式，可选: {', '.join(valid_modes)}")
    config = load_config()
    config['mode'] = mode
    save_config(config)

def get_smtp_config():
    """获取SMTP服务器配置"""
    config = load_config()
    return {
        'sender_email': config.get('sender_email', ''),
        'sender_password': config.get('sender_password', ''),
        'smtp_server': config.get('smtp_server', ''),
        'smtp_port': config.get('smtp_port', 465)
    }

def set_smtp_config(sender_email: str, sender_password: str, smtp_server: str, smtp_port: int = 465):
    """设置SMTP服务器配置"""
    if not all([sender_email, sender_password, smtp_server]):
        raise ValueError("邮箱、密码和SMTP服务器地址不能为空")
    
    if smtp_port not in [465, 587, 25]:
        raise ValueError("无效的SMTP端口，常用端口：465(SSL), 587(TLS), 25(非加密)")
    
    config = load_config()
    config.update({
        'sender_email': sender_email,
        'sender_password': sender_password,
        'smtp_server': smtp_server,
        'smtp_port': smtp_port
    })
    save_config(config)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
