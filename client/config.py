"""配置管理 - 保存在 %APPDATA%/people-finder/config.json"""

import os
import json

APP_NAME = "jiaxing-find-people"

def get_config_dir():
    """获取配置目录"""
    if os.name == 'nt':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    else:
        base = os.path.expanduser('~/.config')
    config_dir = os.path.join(base, APP_NAME)
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_config_path():
    return os.path.join(get_config_dir(), 'config.json')

def load_config():
    """加载配置"""
    path = get_config_path()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    """保存配置"""
    path = get_config_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_server_url():
    """获取服务器地址"""
    config = load_config()
    return config.get('server_url', 'http://localhost/findpeople')

def set_server_url(url):
    """设置服务器地址"""
    config = load_config()
    config['server_url'] = url
    save_config(config)

def get_username():
    """获取已保存的用户名"""
    config = load_config()
    return config.get('username', '')

def set_username(name):
    """保存用户名"""
    config = load_config()
    config['username'] = name
    save_config(config)

def get_my_ip():
    """获取本机IP"""
    config = load_config()
    return config.get('my_ip', '')
