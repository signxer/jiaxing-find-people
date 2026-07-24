"""
嘉行找人 - 主程序
系统托盘应用，后台轮询，GUI弹窗

线程模型：
- 主线程：tkinter事件循环（处理GUI弹窗）
- 后台线程：pystray系统托盘
- 后台线程：轮询线程（通过队列与主线程通信）
"""

import sys
import os
import threading
import time
import queue
import tkinter as tk
from tkinter import messagebox

import pystray
from PIL import Image, ImageDraw

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import api_client
from gui import (
    FirstSetupDialog,
    UserListWindow,
    IncomingFindAlert,
    FindResultNotification,
    SettingsDialog
)


class PeopleFinderApp:
    """主应用类"""

    def __init__(self):
        self.my_ip = api_client.get_local_ip()
        self.running = True
        self.polling_interval = 30  # 默认30秒轮询
        self.waiting_response = False  # 是否在等待找人响应

        # 消息队列：轮询线程 → 主线程
        self.msg_queue = queue.Queue()

        # 隐藏的tkinter根窗口（用于after调度）
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏主窗口

        # 检查是否首次运行
        self._check_first_run()

        # 创建系统托盘图标
        self._create_tray_icon()

        # 注册队列检查
        self._poll_queue()

    def _check_first_run(self):
        """检查是否需要首次设置"""
        username = config.get_username()
        server_url = config.get_server_url()

        if not username:
            dialog = FirstSetupDialog()
            name, server = dialog.show()
            if not name:
                sys.exit(0)
            config.set_username(name)
            if server:
                config.set_server_url(server)

            # 注册到服务器
            self._register(name)

    def _register(self, name):
        """注册用户"""
        try:
            result = api_client.register(name, self.my_ip)
            if 'error' in result:
                self._show_error(f"注册失败: {result['error']}")
                return False
            return True
        except Exception as e:
            self._show_error(f"注册失败: {e}")
            return False

    def _create_tray_icon(self):
        """创建系统托盘图标"""
        image = self._create_icon_image()

        menu = pystray.Menu(
            pystray.MenuItem("查看在线用户", self._show_users),
            pystray.MenuItem("我的收藏", self._show_favorites),
            pystray.MenuItem("设置", self._show_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._quit)
        )

        self.icon = pystray.Icon(
            "people-finder",
            image,
            "嘉行找人",
            menu
        )

    def _create_icon_image(self):
        """创建托盘图标图片"""
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], fill='#4CAF50', outline='#388E3C')
        draw.ellipse([24, 16, 40, 32], fill='white')
        draw.rectangle([28, 32, 36, 48], fill='white')
        return img

    def _poll_queue(self):
        """主线程定时检查消息队列"""
        try:
            while True:
                msg_type, data = self.msg_queue.get_nowait()
                if msg_type == 'incoming_find':
                    self._handle_incoming_find(data)
                elif msg_type == 'find_result':
                    self._show_find_result(data)
        except queue.Empty:
            pass
        # 每200ms检查一次
        self.root.after(200, self._poll_queue)

    def _start_polling(self):
        """启动后台轮询线程"""
        def poll_loop():
            while self.running:
                try:
                    self._do_poll()
                except Exception as e:
                    print(f"轮询错误: {e}")
                time.sleep(self.polling_interval)

        thread = threading.Thread(target=poll_loop, daemon=True)
        thread.start()

    def _do_poll(self):
        """执行一次轮询 - 使用sync接口合并心跳+检查"""
        try:
            result = api_client.sync()

            if not result or 'error' in result:
                return

            # 检查是否有人找我
            incoming = result.get('incoming')
            if incoming:
                self.msg_queue.put(('incoming_find', incoming))

            # 检查自己请求的结果
            my_result = result.get('my_result')
            if my_result and self.waiting_response:
                self.waiting_response = False
                self.msg_queue.put(('find_result', my_result))

        except Exception as e:
            print(f"sync请求失败: {e}")

    def _handle_incoming_find(self, incoming):
        """处理有人找我（主线程调用）"""
        request_id = incoming['request_id']
        from_name = incoming['from_name']

        alert = IncomingFindAlert(from_name, request_id, self._respond_find)
        alert.show()

    def _respond_find(self, request_id, accepted):
        """回应找人请求"""
        try:
            api_client.respond_find(request_id, accepted)
        except Exception as e:
            print(f"回应失败: {e}")

    def _show_find_result(self, result):
        """显示找人结果（主线程调用）"""
        to_name = result['to_name']
        accepted = result['status'] == 'accepted'
        notification = FindResultNotification(to_name, accepted)
        notification.show()

    def _show_users(self, icon=None, item=None):
        """显示在线用户列表"""
        def fetch_and_show():
            try:
                users = api_client.get_users()
                favorites = api_client.get_favorites()

                if isinstance(users, dict) and 'error' in users:
                    self._show_error(f"获取用户失败: {users['error']}")
                    return

                window = UserListWindow(
                    users=users,
                    favorites=favorites if isinstance(favorites, list) else [],
                    on_find=self._find_user,
                    on_favorite=self._toggle_favorite,
                    my_ip=self.my_ip
                )
                window.show()
            except Exception as e:
                self._show_error(f"获取用户列表失败: {e}")

        threading.Thread(target=fetch_and_show, daemon=True).start()

    def _show_favorites(self, icon=None, item=None):
        """显示收藏列表"""
        def fetch_and_show():
            try:
                favorites = api_client.get_favorites()

                if isinstance(favorites, dict) and 'error' in favorites:
                    self._show_error(f"获取收藏失败: {favorites['error']}")
                    return

                window = UserListWindow(
                    users=[],
                    favorites=favorites if isinstance(favorites, list) else [],
                    on_find=self._find_user,
                    on_favorite=self._toggle_favorite,
                    my_ip=self.my_ip
                )
                window.show()
            except Exception as e:
                self._show_error(f"获取收藏列表失败: {e}")

        threading.Thread(target=fetch_and_show, daemon=True).start()

    def _find_user(self, to_ip, to_name):
        """找人"""
        try:
            result = api_client.send_find(to_ip)
            if 'error' in result:
                self._show_error(f"发送失败: {result['error']}")
                return
            self.waiting_response = True
            # 等待响应时加快轮询
            self.polling_interval = 10
            # 启动超时恢复
            threading.Thread(target=self._restore_polling_after_timeout, daemon=True).start()
        except Exception as e:
            self._show_error(f"发送失败: {e}")

    def _restore_polling_after_timeout(self):
        """超时后恢复正常轮询间隔"""
        time.sleep(120)
        if self.waiting_response:
            self.waiting_response = False
            self.polling_interval = 30

    def _toggle_favorite(self, favorite_ip):
        """切换收藏"""
        try:
            result = api_client.toggle_favorite(favorite_ip)
            if 'error' in result:
                print(f"收藏操作失败: {result['error']}")
        except Exception as e:
            print(f"收藏操作失败: {e}")

    def _show_settings(self, icon=None, item=None):
        """显示设置窗口"""
        def show():
            dialog = SettingsDialog(
                current_name=config.get_username(),
                current_server=config.get_server_url(),
                current_ip=self.my_ip
            )
            result = dialog.show()
            if result:
                old_name = config.get_username()
                config.set_username(result['name'])
                config.set_server_url(result['server_url'])

                if result['name'] != old_name:
                    self._register(result['name'])

        threading.Thread(target=show, daemon=True).start()

    def _show_error(self, message):
        """显示错误信息"""
        print(f"[错误] {message}")

    def _quit(self, icon=None, item=None):
        """退出程序"""
        self.running = False
        if hasattr(self, 'icon'):
            self.icon.stop()
        self.root.quit()

    def run(self):
        """运行应用"""
        # 启动轮询线程
        self._start_polling()

        # 启动pystray（在后台线程）
        tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        tray_thread.start()

        print("嘉行找人已启动，最小化到系统托盘...")
        print(f"本机IP: {self.my_ip}")
        print(f"服务器: {config.get_server_url()}")

        # 主线程运行tkinter事件循环
        self.root.mainloop()


def main():
    app = PeopleFinderApp()
    app.run()


if __name__ == '__main__':
    main()
