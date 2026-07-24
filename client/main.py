"""
嘉行找人 - 主程序
PyQt5 + PyQt-Fluent-Widgets + QSystemTrayIcon
"""

import sys
import os
import threading
import time

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import api_client
from gui import (
    FirstSetupDialog, SettingsDialog,
    UserListWindow, IncomingFindAlert, FindResultDialog
)


class PollSignals(QObject):
    """轮询线程信号"""
    incoming_find = pyqtSignal(dict)
    find_result = pyqtSignal(dict)
    server_status = pyqtSignal(bool)


class PeopleFinderApp(QObject):
    """主应用"""

    def __init__(self):
        super().__init__()
        self.my_ip = api_client.get_local_ip()
        self.server_ok = False
        self.waiting_response = False
        self.polling_interval = 30

        # 信号
        self.signals = PollSignals()
        self.signals.incoming_find.connect(self._on_incoming_find)
        self.signals.find_result.connect(self._on_find_result)

        # 初始化托盘
        self._init_tray()

        # 启动轮询
        self._start_polling()

    def _get_icon_path(self):
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, 'icon.ico')

    def _init_tray(self):
        """初始化系统托盘"""
        icon_path = self._get_icon_path()
        if os.path.exists(icon_path):
            self.tray_icon = QIcon(icon_path)
        else:
            # fallback
            pixmap = QPixmap(64, 64)
            pixmap.fill()
            self.tray_icon = QIcon(pixmap)

        self.tray = QSystemTrayIcon(self.tray_icon)
        self.tray.setToolTip("嘉行找人")

        # 右键菜单
        menu = QMenu()

        users_action = QAction("👥 查看在线用户", menu)
        users_action.triggered.connect(self._show_users)
        menu.addAction(users_action)

        fav_action = QAction("⭐ 我的收藏", menu)
        fav_action.triggered.connect(self._show_favorites)
        menu.addAction(fav_action)

        menu.addSeparator()

        settings_action = QAction("⚙️ 设置", menu)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("❌ 退出", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_users()

    def _start_polling(self):
        """启动轮询线程"""
        def poll_loop():
            while True:
                try:
                    self._do_poll()
                except Exception as e:
                    print(f"轮询错误: {e}")
                time.sleep(self.polling_interval)

        thread = threading.Thread(target=poll_loop, daemon=True)
        thread.start()

    def _do_poll(self):
        try:
            result = api_client.sync()
            if not result or 'error' in result:
                if self.server_ok:
                    self.server_ok = False
                return

            if not self.server_ok:
                self.server_ok = True

            incoming = result.get('incoming')
            if incoming:
                self.signals.incoming_find.emit(incoming)

            my_result = result.get('my_result')
            if my_result and self.waiting_response:
                self.waiting_response = False
                self.signals.find_result.emit(my_result)

        except Exception as e:
            if self.server_ok:
                self.server_ok = False
                print(f"服务器连接失败: {e}")

    def _on_incoming_find(self, data):
        """有人找我 - 主线程处理"""
        alert = IncomingFindAlert(
            data['from_name'],
            data['request_id'],
            self._respond_find
        )
        alert.showFullScreen()

    def _respond_find(self, request_id, accepted):
        try:
            api_client.respond_find(request_id, accepted)
        except Exception as e:
            print(f"回应失败: {e}")

    def _on_find_result(self, data):
        """找人结果 - 主线程处理"""
        dialog = FindResultDialog(data['to_name'], data['status'] == 'accepted')
        dialog.show()

    def _show_users(self):
        """显示在线用户"""
        def fetch():
            try:
                users = api_client.get_users()
                favorites = api_client.get_favorites()
                if isinstance(users, dict) and 'error' in users:
                    print(f"获取用户失败: {users['error']}")
                    return
                self._user_win = UserListWindow(
                    users=users,
                    favorites=favorites if isinstance(favorites, list) else [],
                    on_find=self._find_user,
                    on_favorite=self._toggle_favorite,
                    my_ip=self.my_ip
                )
                self._user_win.show()
            except Exception as e:
                print(f"获取用户列表失败: {e}")

        threading.Thread(target=fetch, daemon=True).start()

    def _show_favorites(self):
        """显示收藏列表"""
        def fetch():
            try:
                favorites = api_client.get_favorites()
                if isinstance(favorites, dict) and 'error' in favorites:
                    print(f"获取收藏失败: {favorites['error']}")
                    return
                self._fav_win = UserListWindow(
                    users=[],
                    favorites=favorites if isinstance(favorites, list) else [],
                    on_find=self._find_user,
                    on_favorite=self._toggle_favorite,
                    my_ip=self.my_ip
                )
                self._fav_win.show()
            except Exception as e:
                print(f"获取收藏列表失败: {e}")

        threading.Thread(target=fetch, daemon=True).start()

    def _find_user(self, to_ip, to_name):
        try:
            result = api_client.send_find(to_ip)
            if 'error' in result:
                print(f"发送失败: {result['error']}")
                return
            self.waiting_response = True
            self.polling_interval = 10
            QTimer.singleShot(120000, self._restore_polling)
        except Exception as e:
            print(f"发送失败: {e}")

    def _restore_polling(self):
        if self.waiting_response:
            self.waiting_response = False
            self.polling_interval = 30

    def _toggle_favorite(self, favorite_ip):
        try:
            result = api_client.toggle_favorite(favorite_ip)
            if 'error' in result:
                print(f"收藏操作失败: {result['error']}")
        except Exception as e:
            print(f"收藏操作失败: {e}")

    def _show_settings(self):
        dialog = SettingsDialog(
            current_name=config.get_username(),
            current_server=config.get_server_url(),
            current_ip=self.my_ip
        )
        dialog.show()
        # 等窗口关闭后检查是否保存了
        self._settings_dialog = dialog
        # 用QTimer轮询结果（简单方案）
        def check_result():
            if dialog.result:
                old_name = config.get_username()
                config.set_username(dialog.result['name'])
                config.set_server_url(dialog.result['server_url'])
                self._try_register(dialog.result['name'])
            elif dialog.isVisible():
                QTimer.singleShot(500, check_result)
        QTimer.singleShot(500, check_result)

    def _try_register(self, name):
        try:
            result = api_client.register(name, self.my_ip)
            if 'error' in result:
                print(f"[提示] 注册失败: {result['error']}")
                self.server_ok = False
            else:
                self.server_ok = True
                print(f"[OK] 注册成功: {name} ({self.my_ip})")
        except Exception as e:
            print(f"[提示] 服务器连接失败: {e}")
            self.server_ok = False

    def check_first_run(self):
        """首次运行检查（在app.exec()之前调用）"""
        username = config.get_username()
        server_url = config.get_server_url()

        if username and server_url:
            self._try_register(username)
            return

        dialog = FirstSetupDialog()
        dialog.show()
        # 需要等对话框关闭
        self._setup_dialog = dialog

    def on_setup_closed(self):
        """首次设置关闭后"""
        dialog = self._setup_dialog
        if dialog.result_name:
            config.set_username(dialog.result_name)
            if dialog.result_server:
                config.set_server_url(dialog.result_server)
            self._try_register(dialog.result_name)

    def _quit(self):
        self.tray.hide()
        QApplication.instance().quit()


def main():
    # 高DPI支持
    QApplication.setAttribute(16, True)  # AA_EnableHighDpiScaling

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出
    app.setApplicationName("嘉行找人")

    # 设置全局主题样式
    app.setStyleSheet("""
        QWidget {
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
        }
        QLabel#formLabel {
            font-size: 13px;
            color: #666;
            margin-top: 4px;
        }
        QLabel#ipLabel {
            font-size: 12px;
            color: #999;
        }
        QLabel#emptyLabel {
            font-size: 14px;
            color: #aaa;
            padding: 40px;
        }
    """)

    finder = PeopleFinderApp()

    # 首次运行检查
    finder.check_first_run()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
