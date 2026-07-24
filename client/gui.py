"""GUI模块 - PyQt5 + PyQt-Fluent-Widgets"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QApplication, QSpacerItem, QSizePolicy, QStackedWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from qfluentwidgets import (
    FluentWindow, FluentTitleBar,
    PrimaryPushButton, PushButton, HyperlinkButton, ToolButton,
    LineEdit,
    Dialog, MessageBox,
    InfoBar, InfoBarPosition,
    CardWidget, SimpleCardWidget,
    FluentIcon as FIF,
    setTheme, Theme,
    isDarkTheme
)


# ============================================================
# 首次设置对话框
# ============================================================
class FirstSetupDialog(FluentWindow):
    """首次运行 - 输入名字和服务器地址"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_name = None
        self.result_server = None

        self.setWindowTitle("嘉行找人 - 首次设置")
        self.setFixedSize(420, 300)
        self.titleBar.minBtn.hide()
        self.titleBar.maxBtn.hide()

        self._init_ui()
        self._center()

    def _center(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _init_ui(self):
        container = QWidget()
        container.setObjectName("setupContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 20, 30, 25)
        layout.setSpacing(12)

        # 标题
        title = QLabel("👋 欢迎使用嘉行找人")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(10)

        # 服务器地址
        lbl_server = QLabel("服务器地址")
        lbl_server.setObjectName("formLabel")
        layout.addWidget(lbl_server)

        self.server_input = LineEdit()
        self.server_input.setPlaceholderText("http://ip:端口/findpeople")
        self.server_input.setText("http://localhost/findpeople")
        layout.addWidget(self.server_input)

        # 用户名
        lbl_name = QLabel("你的名字")
        lbl_name.setObjectName("formLabel")
        layout.addWidget(lbl_name)

        self.name_input = LineEdit()
        self.name_input.setPlaceholderText("输入你的名字")
        layout.addWidget(self.name_input)

        layout.addSpacing(10)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.skip_btn = HyperlinkButton(self)
        self.skip_btn.setText("跳过")
        self.skip_btn.clicked.connect(self._on_skip)
        btn_layout.addWidget(self.skip_btn)

        self.ok_btn = PrimaryPushButton("确定")
        self.ok_btn.setFixedWidth(100)
        self.ok_btn.clicked.connect(self._on_ok)
        btn_layout.addWidget(self.ok_btn)

        layout.addLayout(btn_layout)

        self.setWidget(container)

    def _on_ok(self):
        name = self.name_input.text().strip()
        server = self.server_input.text().strip()
        if not name:
            InfoBar.warning("提示", "请输入你的名字", parent=self)
            return
        if not server:
            InfoBar.warning("提示", "请输入服务器地址", parent=self)
            return
        self.result_name = name
        self.result_server = server
        self.close()

    def _on_skip(self):
        self.close()


# ============================================================
# 设置对话框
# ============================================================
class SettingsDialog(FluentWindow):
    """设置窗口 - 修改名字和服务器"""

    def __init__(self, current_name, current_server, current_ip, parent=None):
        super().__init__(parent)
        self.current_name = current_name
        self.current_server = current_server
        self.current_ip = current_ip
        self.result = None

        self.setWindowTitle("设置")
        self.setFixedSize(420, 320)
        self.titleBar.minBtn.hide()
        self.titleBar.maxBtn.hide()

        self._init_ui()
        self._center()

    def _center(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _init_ui(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 20, 30, 25)
        layout.setSpacing(12)

        title = QLabel("⚙️ 设置")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(10)

        # 服务器
        layout.addWidget(QLabel("服务器地址"))
        self.server_input = LineEdit()
        self.server_input.setText(self.current_server)
        layout.addWidget(self.server_input)

        # 用户名
        layout.addWidget(QLabel("你的名字"))
        self.name_input = LineEdit()
        self.name_input.setText(self.current_name)
        layout.addWidget(self.name_input)

        # IP显示
        ip_label = QLabel(f"本机IP: {self.current_ip}")
        ip_label.setObjectName("ipLabel")
        layout.addWidget(ip_label)

        layout.addSpacing(10)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = PushButton("取消")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)

        save_btn = PrimaryPushButton("保存")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setWidget(container)

    def _on_save(self):
        name = self.name_input.text().strip()
        server = self.server_input.text().strip()
        if not name or not server:
            InfoBar.warning("提示", "名字和服务器地址不能为空", parent=self)
            return
        self.result = {'name': name, 'server_url': server}
        self.close()


# ============================================================
# 用户列表窗口
# ============================================================
class UserListWindow(FluentWindow):
    """用户列表 - 在线用户 / 收藏 / 全部"""

    def __init__(self, users, favorites, on_find, on_favorite, my_ip, parent=None):
        super().__init__(parent)
        self.users = users
        self.favorites = favorites
        self.on_find = on_find
        self.on_favorite = on_favorite
        self.my_ip = my_ip
        self.favorite_ips = {f['ip'] for f in favorites}

        self.setWindowTitle("嘉行找人")
        self.resize(520, 450)
        self.titleBar.maxBtn.hide()

        self._init_ui()
        self._center()

    def _center(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _init_ui(self):
        from qfluentwidgets import TabBar

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 10, 15, 15)
        layout.setSpacing(10)

        # Tab栏
        self.tab_bar = TabBar(self)
        self.tab_bar.addTab("online", "🟢 在线用户")
        self.tab_bar.addTab("fav", "⭐ 我的收藏")
        self.tab_bar.addTab("all", "📋 全部用户")
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tab_bar)

        # 页面栈
        self.stack = QStackedWidget()

        # 在线用户页
        online_users = [u for u in self.users if u['online'] and u['ip'] != self.my_ip]
        self.stack.addWidget(self._build_user_page(online_users))

        # 收藏页
        self.stack.addWidget(self._build_user_page(
            [u for u in self.favorites if u['ip'] != self.my_ip], show_fav_btn=False
        ))

        # 全部用户页
        self.stack.addWidget(self._build_user_page(
            [u for u in self.users if u['ip'] != self.my_ip]
        ))

        layout.addWidget(self.stack)
        self.setWidget(container)

    def _on_tab_changed(self, index):
        self.stack.setCurrentIndex(index)

    def _build_user_page(self, users, show_fav_btn=True):
        """构建一个用户列表页面"""
        from PyQt5.QtWidgets import QScrollArea

        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 5, 0, 0)
        page_layout.setSpacing(6)

        if not users:
            empty = QLabel("暂无用户")
            empty.setAlignment(Qt.AlignCenter)
            empty.setObjectName("emptyLabel")
            page_layout.addWidget(empty)
            page_layout.addStretch()
            return page

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 8, 0)
        scroll_layout.setSpacing(6)

        for user in users:
            card = self._build_user_card(user, show_fav_btn)
            scroll_layout.addWidget(card)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        page_layout.addWidget(scroll)
        return page

    def _build_user_card(self, user, show_fav_btn=True):
        """构建单个用户卡片"""
        card = SimpleCardWidget()
        card.setFixedHeight(52)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # 在线状态
        status_dot = QLabel("●")
        status_dot.setFixedWidth(16)
        status_dot.setAlignment(Qt.AlignCenter)
        if user['online']:
            status_dot.setStyleSheet("color: #4CAF50; font-size: 12px;")
        else:
            status_dot.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(status_dot)

        # 名字
        name_label = QLabel(user['name'])
        name_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        layout.addWidget(name_label)

        # IP
        ip_label = QLabel(user['ip'])
        ip_label.setObjectName("ipLabel")
        layout.addWidget(ip_label)

        layout.addStretch()

        # 收藏按钮
        if show_fav_btn:
            is_fav = user['ip'] in self.favorite_ips
            fav_btn = ToolButton(FIF.HEART if is_fav else FIF.HEART)
            fav_btn.setToolTip("取消收藏" if is_fav else "收藏")
            if is_fav:
                fav_btn.setStyleSheet("QToolButton { color: #e91e63; }")
            fav_btn.clicked.connect(lambda checked, ip=user['ip']: self._toggle_fav(ip, fav_btn))
            layout.addWidget(fav_btn)

        # 找人按钮
        if user['online']:
            find_btn = PrimaryPushButton("找 TA")
            find_btn.setFixedWidth(70)
            find_btn.setFixedHeight(32)
            find_btn.clicked.connect(lambda checked, ip=user['ip'], name=user['name']: self._find_user(ip, name))
            layout.addWidget(find_btn)

        return card

    def _toggle_fav(self, ip, btn):
        self.on_favorite(ip)
        if ip in self.favorite_ips:
            self.favorite_ips.discard(ip)
            btn.setToolTip("收藏")
            btn.setStyleSheet("")
        else:
            self.favorite_ips.add(ip)
            btn.setToolTip("取消收藏")
            btn.setStyleSheet("QToolButton { color: #e91e63; }")

    def _find_user(self, ip, name):
        w = Dialog("确认找人", f"确定要找 {name} 吗？", self)
        w.yesSignal.connect(lambda: self._do_find(ip, name))
        w.exec()

    def _do_find(self, ip, name):
        self.on_find(ip, name)
        InfoBar.success("已发送", f"已向 {name} 发送找人请求，等待回应...",
                        position=InfoBarPosition.TOP, parent=self)


# ============================================================
# 被找全屏弹窗
# ============================================================
class IncomingFindAlert(QWidget):
    """被找全屏弹窗 - 醒目提醒"""

    def __init__(self, from_name, request_id, on_respond):
        super().__init__()
        self.from_name = from_name
        self.request_id = request_id
        self.on_respond = on_respond
        self.responded = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: #1a1a2e;")

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # 铃铛
        bell = QLabel("🔔")
        bell.setFont(QFont("Arial", 72))
        bell.setAlignment(Qt.AlignCenter)
        layout.addWidget(bell)

        # 提示文字
        msg = QLabel(f"{self.from_name} 在找你！")
        msg.setFont(QFont("Microsoft YaHei", 32, QFont.Bold))
        msg.setStyleSheet("color: white;")
        msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg)

        sub = QLabel("请注意查看")
        sub.setFont(QFont("Microsoft YaHei", 16))
        sub.setStyleSheet("color: #aaaaaa;")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacing(30)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(30)
        btn_layout.setAlignment(Qt.AlignCenter)

        ok_btn = PrimaryPushButton("✓ 我知道了")
        ok_btn.setFixedSize(180, 50)
        ok_btn.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #16213e;
            }
        """)
        ok_btn.clicked.connect(lambda: self._respond(True))
        btn_layout.addWidget(ok_btn)

        ignore_btn = PushButton("✗ 忽略")
        ignore_btn.setFixedSize(180, 50)
        ignore_btn.setFont(QFont("Microsoft YaHei", 14))
        ignore_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: #aaa;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        ignore_btn.clicked.connect(lambda: self._respond(False))
        btn_layout.addWidget(ignore_btn)

        layout.addLayout(btn_layout)

    def showEvent(self, event):
        """显示时全屏"""
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._respond(False)

    def _respond(self, accepted):
        self.responded = accepted
        self.on_respond(self.request_id, accepted)
        self.close()


# ============================================================
# 找人结果通知
# ============================================================
class FindResultDialog(FluentWindow):
    """找人结果弹窗"""

    def __init__(self, to_name, accepted, parent=None):
        super().__init__(parent)
        self.setWindowTitle("找人结果")
        self.setFixedSize(350, 200)
        self.titleBar.minBtn.hide()
        self.titleBar.maxBtn.hide()

        self._init_ui(to_name, accepted)
        self._center()

    def _center(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _init_ui(self, name, accepted):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 20, 30, 25)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("✅" if accepted else "❌")
        icon.setFont(QFont("Arial", 36))
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        msg = QLabel(f"{name} 已收到你的请求" if accepted else f"{name} 未回应")
        msg.setFont(QFont("Microsoft YaHei", 12))
        msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg)

        layout.addSpacing(10)

        ok_btn = PrimaryPushButton("确定")
        ok_btn.setFixedWidth(100)
        ok_btn.clicked.connect(self.close)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setWidget(container)
