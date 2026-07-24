"""API客户端 - 封装所有HTTP请求"""

import requests
import socket
import json
from config import get_server_url, get_my_ip

TIMEOUT = 10  # 请求超时(秒)

def get_local_ip():
    """获取本机局域网IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def _url():
    return get_server_url()

def _ip():
    """获取当前使用的IP"""
    ip = get_my_ip()
    if not ip:
        ip = get_local_ip()
    return ip

def register(name, ip=None):
    """注册用户"""
    if ip is None:
        ip = _ip()
    resp = requests.post(_url(), json={
        'action': 'register',
        'name': name,
        'ip': ip
    }, timeout=TIMEOUT)
    return resp.json()

def heartbeat():
    """发送心跳"""
    resp = requests.post(_url(), json={
        'action': 'heartbeat',
        'ip': _ip()
    }, timeout=TIMEOUT)
    return resp.json()

def get_users():
    """获取所有用户列表"""
    resp = requests.get(_url(), params={'action': 'users'}, timeout=TIMEOUT)
    return resp.json()

def send_find(to_ip):
    """发送找人请求"""
    resp = requests.post(_url(), json={
        'action': 'find',
        'from_ip': _ip(),
        'to_ip': to_ip
    }, timeout=TIMEOUT)
    return resp.json()

def check_incoming():
    """检查是否有人找我"""
    resp = requests.get(_url(), params={
        'action': 'check',
        'ip': _ip()
    }, timeout=TIMEOUT)
    return resp.json()

def respond_find(request_id, accepted):
    """回应找人请求"""
    resp = requests.post(_url(), json={
        'action': 'respond',
        'request_id': request_id,
        'accepted': accepted
    }, timeout=TIMEOUT)
    return resp.json()

def check_result():
    """检查自己发出请求的结果"""
    resp = requests.get(_url(), params={
        'action': 'result',
        'ip': _ip()
    }, timeout=TIMEOUT)
    return resp.json()

def sync():
    """同步接口 - 合并心跳+检查+结果，一次请求搞定"""
    resp = requests.post(_url(), json={
        'action': 'sync',
        'ip': _ip()
    }, timeout=TIMEOUT)
    return resp.json()

def toggle_favorite(favorite_ip):
    """切换收藏状态"""
    resp = requests.post(_url(), json={
        'action': 'favorite',
        'user_ip': _ip(),
        'favorite_ip': favorite_ip
    }, timeout=TIMEOUT)
    return resp.json()

def get_favorites():
    """获取收藏列表"""
    resp = requests.get(_url(), params={
        'action': 'favorites',
        'ip': _ip()
    }, timeout=TIMEOUT)
    return resp.json()
