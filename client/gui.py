"""GUI模块 - 所有弹窗和界面"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading


class FirstSetupDialog:
    """首次运行 - 输入名字和服务器地址（使用Toplevel避免多Tk冲突）"""

    def __init__(self, parent):
        self.parent = parent
        self.result = None
        self.server_url = None

    def show(self):
        self.win = tk.Toplevel(self.parent)
        self.win.title("嘉行找人 - 首次设置")
        self.win.geometry("400x250")
        self.win.resizable(False, False)
        self.win.attributes('-topmost', True)
        self.win.grab_set()  # 模态

        # 居中
        self.win.update_idletasks()
        x = (self.win.winfo_screenwidth() - 400) // 2
        y = (self.win.winfo_screenheight() - 250) // 2
        self.win.geometry(f"400x250+{x}+{y}")

        frame = ttk.Frame(self.win, padding=20)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="欢迎使用嘉行找人！", font=('微软雅黑', 14, 'bold')).pack(pady=(0, 15))

        # 服务器地址
        ttk.Label(frame, text="服务器地址:").pack(anchor='w')
        self.server_entry = ttk.Entry(frame, width=45)
        self.server_entry.pack(fill='x', pady=(0, 10))
        self.server_entry.insert(0, "http://localhost/findpeople")

        # 用户名
        ttk.Label(frame, text="你的名字:").pack(anchor='w')
        self.name_entry = ttk.Entry(frame, width=45)
        self.name_entry.pack(fill='x', pady=(0, 15))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="确定", command=self._on_ok).pack(side='right', padx=(5, 0))
        ttk.Button(btn_frame, text="跳过", command=self._on_skip).pack(side='right')

        self.win.protocol("WM_DELETE_WINDOW", self._on_skip)
        self.win.wait_window()
        return self.result, self.server_url

    def _on_ok(self):
        name = self.name_entry.get().strip()
        server = self.server_entry.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入你的名字", parent=self.win)
            return
        if not server:
            messagebox.showwarning("提示", "请输入服务器地址", parent=self.win)
            return
        self.result = name
        self.server_url = server
        self.win.destroy()

    def _on_skip(self):
        self.win.destroy()


class UserListWindow:
    """用户列表窗口 - 在线用户、收藏、找人"""

    def __init__(self, users, favorites, on_find, on_favorite, my_ip):
        self.users = users
        self.favorites = favorites
        self.on_find = on_find
        self.on_favorite = on_favorite
        self.my_ip = my_ip
        self.favorite_ips = {f['ip'] for f in favorites}

    def show(self):
        self.root = tk.Tk()
        self.root.title("在线用户")
        self.root.geometry("500x400")
        self.root.attributes('-topmost', True)

        # 居中
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 500) // 2
        y = (self.root.winfo_screenheight() - 400) // 2
        self.root.geometry(f"500x400+{x}+{y}")

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill='both', expand=True)

        # 标签页
        notebook = ttk.Notebook(frame)
        notebook.pack(fill='both', expand=True)

        # 在线用户页
        online_frame = ttk.Frame(notebook, padding=5)
        notebook.add(online_frame, text="在线用户")
        self._build_user_list(online_frame, [u for u in self.users if u['online'] and u['ip'] != self.my_ip])

        # 收藏页
        fav_frame = ttk.Frame(notebook, padding=5)
        notebook.add(fav_frame, text="我的收藏")
        self._build_user_list(fav_frame, [u for u in self.favorites if u['ip'] != self.my_ip], show_fav_btn=False)

        # 全部用户页
        all_frame = ttk.Frame(notebook, padding=5)
        notebook.add(all_frame, text="全部用户")
        self._build_user_list(all_frame, [u for u in self.users if u['ip'] != self.my_ip])

        # 关闭按钮
        ttk.Button(frame, text="关闭", command=self.root.destroy).pack(pady=(10, 0))

        self.root.mainloop()

    def _build_user_list(self, parent, users, show_fav_btn=True):
        """构建用户列表"""
        if not users:
            ttk.Label(parent, text="暂无用户", foreground='gray').pack(pady=20)
            return

        # 滚动容器
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for user in users:
            row = ttk.Frame(scroll_frame)
            row.pack(fill='x', pady=2)

            # 在线状态指示
            status = "🟢" if user['online'] else "⚫"
            ttk.Label(row, text=f"{status} {user['name']}", width=20, anchor='w').pack(side='left', padx=(0, 10))
            ttk.Label(row, text=user['ip'], foreground='gray', width=15).pack(side='left')

            # 收藏按钮
            if show_fav_btn:
                is_fav = user['ip'] in self.favorite_ips
                fav_text = "★ 已收藏" if is_fav else "☆ 收藏"
                btn = ttk.Button(row, text=fav_text, width=8,
                                 command=lambda ip=user['ip']: self._toggle_fav(ip))
                btn.pack(side='right', padx=2)

            # 找人按钮(仅在线用户)
            if user['online']:
                ttk.Button(row, text="找 TA", width=6,
                           command=lambda ip=user['ip'], name=user['name']: self._find_user(ip, name)).pack(side='right', padx=2)

    def _toggle_fav(self, ip):
        self.on_favorite(ip)
        if ip in self.favorite_ips:
            self.favorite_ips.discard(ip)
        else:
            self.favorite_ips.add(ip)

    def _find_user(self, ip, name):
        if messagebox.askyesno("确认", f"确定要找 {name} 吗？", parent=self.root):
            self.on_find(ip, name)
            messagebox.showinfo("已发送", f"已向 {name} 发送找人请求，等待回应...", parent=self.root)


class IncomingFindAlert:
    """被找全屏弹窗 - 醒目提醒"""

    def __init__(self, from_name, request_id, on_respond):
        self.from_name = from_name
        self.request_id = request_id
        self.on_respond = on_respond
        self.responded = None

    def show(self):
        self.root = tk.Toplevel()
        self.root.title("有人找你！")
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#1a1a2e')

        # 主框架
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.place(relx=0.5, rely=0.5, anchor='center')

        # 图标
        tk.Label(main_frame, text="🔔", font=('Arial', 80), bg='#1a1a2e', fg='#e94560').pack()

        # 提示文字
        tk.Label(main_frame, text=f"{self.from_name} 在找你！",
                 font=('微软雅黑', 36, 'bold'), bg='#1a1a2e', fg='#ffffff').pack(pady=20)

        tk.Label(main_frame, text="请注意查看",
                 font=('微软雅黑', 18), bg='#1a1a2e', fg='#aaaaaa').pack(pady=(0, 40))

        # 按钮框架
        btn_frame = tk.Frame(main_frame, bg='#1a1a2e')
        btn_frame.pack()

        ok_btn = tk.Button(btn_frame, text="✓ 我知道了", font=('微软雅黑', 16, 'bold'),
                           bg='#0f3460', fg='#ffffff', activebackground='#16213e',
                           width=15, height=2, relief='flat', cursor='hand2',
                           command=lambda: self._respond(True))
        ok_btn.pack(side='left', padx=20)

        ignore_btn = tk.Button(btn_frame, text="✗ 忽略", font=('微软雅黑', 16),
                               bg='#333333', fg='#aaaaaa', activebackground='#444444',
                               width=15, height=2, relief='flat', cursor='hand2',
                               command=lambda: self._respond(False))
        ignore_btn.pack(side='left', padx=20)

        self.root.bind('<Escape>', lambda e: self._respond(False))
        self.root.protocol("WM_DELETE_WINDOW", lambda: self._respond(False))
        self.root.grab_set()
        self.root.wait_window()
        return self.responded

    def _respond(self, accepted):
        self.responded = accepted
        self.on_respond(self.request_id, accepted)
        self.root.destroy()


class FindResultNotification:
    """找人结果通知"""

    def __init__(self, to_name, accepted):
        self.to_name = to_name
        self.accepted = accepted

    def show(self):
        self.root = tk.Toplevel()
        self.root.title("找人结果")
        self.root.geometry("350x180")
        self.root.attributes('-topmost', True)
        self.root.resizable(False, False)

        # 居中
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 350) // 2
        y = (self.root.winfo_screenheight() - 180) // 2
        self.root.geometry(f"350x180+{x}+{y}")

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill='both', expand=True)

        if self.accepted:
            ttk.Label(frame, text="✅", font=('Arial', 36)).pack()
            ttk.Label(frame, text=f"{self.to_name} 已收到你的请求",
                      font=('微软雅黑', 12)).pack(pady=10)
        else:
            ttk.Label(frame, text="❌", font=('Arial', 36)).pack()
            ttk.Label(frame, text=f"{self.to_name} 未回应",
                      font=('微软雅黑', 12)).pack(pady=10)

        ttk.Button(frame, text="确定", command=self.root.destroy).pack(pady=(10, 0))
        self.root.grab_set()
        self.root.wait_window()


class SettingsDialog:
    """设置窗口 - 修改名字和服务器"""

    def __init__(self, current_name, current_server, current_ip):
        self.current_name = current_name
        self.current_server = current_server
        self.current_ip = current_ip
        self.result = None

    def show(self):
        self.root = tk.Toplevel()
        self.root.title("设置")
        self.root.geometry("400x280")
        self.root.attributes('-topmost', True)
        self.root.resizable(False, False)

        # 居中
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 400) // 2
        y = (self.root.winfo_screenheight() - 280) // 2
        self.root.geometry(f"400x280+{x}+{y}")

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="设置", font=('微软雅黑', 14, 'bold')).pack(pady=(0, 15))

        # 服务器地址
        ttk.Label(frame, text="服务器地址:").pack(anchor='w')
        self.server_entry = ttk.Entry(frame, width=45)
        self.server_entry.pack(fill='x', pady=(0, 10))
        self.server_entry.insert(0, self.current_server)

        # 用户名
        ttk.Label(frame, text="你的名字:").pack(anchor='w')
        self.name_entry = ttk.Entry(frame, width=45)
        self.name_entry.pack(fill='x', pady=(0, 5))
        self.name_entry.insert(0, self.current_name)

        # IP显示
        ttk.Label(frame, text=f"本机IP: {self.current_ip}", foreground='gray').pack(anchor='w', pady=(0, 15))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="保存", command=self._on_save).pack(side='right', padx=(5, 0))
        ttk.Button(btn_frame, text="取消", command=self.root.destroy).pack(side='right')

        self.root.grab_set()
        self.root.wait_window()
        return self.result

    def _on_save(self):
        name = self.name_entry.get().strip()
        server = self.server_entry.get().strip()
        if not name or not server:
            messagebox.showwarning("提示", "名字和服务器地址不能为空", parent=self.root)
            return
        self.result = {'name': name, 'server_url': server}
        self.root.destroy()
