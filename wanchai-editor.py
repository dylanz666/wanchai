import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import configparser
import os
from datetime import datetime
import re
from tkinterdnd2 import DND_FILES, TkinterDnD


def get_version():
    try:
        from version import __version__

        return __version__
    except Exception:
        return "0.0.0"


SEMVER_VERSION = get_version()
DEFAULT_SKU_SUFFIX = "_GRC"
APP_TITLE = f"WanChai INI File Editor (v{SEMVER_VERSION})"
WINDOW_SIZE = "1200x800"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
BG_COLOR = "#f5f6fa"
PRIMARY_COLOR = "#0078d7"
PRIMARY_COLOR_DARK = "#005fa3"
ACCENT_COLOR = "#00b386"
ACCENT_COLOR_DARK = "#009966"
SELECTED_ROW_COLOR = "#90caf9"
TREE_BG_COLOR = "#fafdff"
TREE_HEADER_BG = "#e6eaf2"
TREE_HEADER_FG = "#222"
LABEL_FONT = ("Segoe UI", 11)
TITLE_FONT = ("Arial", 16, "bold")
BUTTON_FONT = ("Segoe UI", 11, "bold")
TREE_FONT = ("Segoe UI", 10)
SPLASH_TITLE_FONT = ("Segoe UI", 20, "bold")
SPLASH_SUB_FONT = ("Segoe UI", 12)
SPLASH_FG = PRIMARY_COLOR
SPLASH_BG = BG_COLOR
SPLASH_SUB_FG = "#888"
SPLASH_SIZE = (570, 270)
SPLASH_PROGRESS_LEN = 500
SPLASH_FADEIN_STEP = 30
SPLASH_FADEOUT_STEP = 30
SPLASH_STAY = 1200


class WanchaiEditor:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # 启动时先隐藏主窗口
        self.show_splash()
        self.tool_title = APP_TITLE
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.configure(bg=BG_COLOR)
        # Modern ttk theme and style
        style = ttk.Style()
        try:
            style.theme_use("clam")  # 更现代的内置主题
        except Exception:
            pass
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, font=LABEL_FONT)
        style.configure(
            "TButton",
            font=BUTTON_FONT,
            foreground="#fff",
            background=PRIMARY_COLOR,
            borderwidth=0,
            focusthickness=3,
            focuscolor=PRIMARY_COLOR,
        )
        style.map("TButton", background=[("active", PRIMARY_COLOR_DARK)])
        style.configure(
            "Accent.TButton",
            font=BUTTON_FONT,
            foreground="#fff",
            background=ACCENT_COLOR,
        )
        style.map("Accent.TButton", background=[("active", ACCENT_COLOR_DARK)])
        style.configure(
            "Treeview",
            font=TREE_FONT,
            rowheight=28,
            fieldbackground=TREE_BG_COLOR,
            background=TREE_BG_COLOR,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            font=LABEL_FONT,
            background=TREE_HEADER_BG,
            foreground=TREE_HEADER_FG,
        )
        style.map("Treeview", background=[("selected", SELECTED_ROW_COLOR)])
        style.configure(
            "TEntry",
            font=TREE_FONT,
            fieldbackground=TREE_BG_COLOR,
            background=TREE_BG_COLOR,
        )
        style.configure(
            "TCombobox",
            font=TREE_FONT,
            fieldbackground=TREE_BG_COLOR,
            background=TREE_BG_COLOR,
        )
        style.configure("TLabelframe", background=BG_COLOR, font=BUTTON_FONT)
        style.configure("TLabelframe.Label", background=BG_COLOR, font=BUTTON_FONT)
        style.configure("TNotebook", background=BG_COLOR)
        style.configure("TNotebook.Tab", font=BUTTON_FONT, padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", TREE_HEADER_BG)])
        # 文件路径
        self.ini_file = ""
        self.config = configparser.ConfigParser()
        # 创建主框架
        self.create_widgets()
        # 拖入文件支持
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.on_drop_file)

    def show_splash(self):
        splash = tk.Toplevel()
        splash.overrideredirect(True)
        splash.configure(bg=SPLASH_BG)
        w, h = SPLASH_SIZE
        ws = splash.winfo_screenwidth()
        hs = splash.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        splash.geometry(f"{w}x{h}+{x}+{y}")
        splash.attributes("-alpha", 0.0)
        label = tk.Label(
            splash, text=APP_TITLE, font=SPLASH_TITLE_FONT, fg=SPLASH_FG, bg=SPLASH_BG
        )
        label.pack(pady=(20, 0))
        sub = tk.Label(
            splash,
            text="Loading...",
            font=SPLASH_SUB_FONT,
            fg=SPLASH_SUB_FG,
            bg=SPLASH_BG,
        )
        sub.pack(pady=(120, 0))
        pb = ttk.Progressbar(splash, mode="indeterminate", length=SPLASH_PROGRESS_LEN)
        pb.pack(pady=10)
        pb.start(12)
        splash.update()
        self._splash_fade_in(splash, 0)

    def _splash_fade_in(self, splash, step):
        if step > 10:
            splash.after(SPLASH_STAY, self._fade_out_splash, splash)
            return
        splash.attributes("-alpha", step / 10)
        splash.update()
        splash.after(SPLASH_FADEIN_STEP, self._splash_fade_in, splash, step + 1)

    def _fade_out_splash(self, splash):
        self._splash_fade_out(splash, 10)

    def _splash_fade_out(self, splash, step):
        if step < 0:
            splash.destroy()
            # 主界面显示时重新左右居中并设置大小
            self.root.update_idletasks()
            w, h = WINDOW_WIDTH, WINDOW_HEIGHT
            ws = self.root.winfo_screenwidth()
            hs = self.root.winfo_screenheight()
            x = (ws // 2) - (w // 2)
            y = int(hs * 0.01)
            self.root.geometry(f"{w}x{h}+{x}+{y}")
            self.root.deiconify()  # 动画结束后显示主窗口
            return
        splash.attributes("-alpha", step / 10)
        splash.update()
        splash.after(SPLASH_FADEOUT_STEP, self._splash_fade_out, splash, step - 1)

    def on_drop_file(self, event):
        file_path = event.data.strip("{}")
        if file_path.lower().endswith(".ini"):
            self.ini_file = file_path
            self.file_path_var.set(file_path)
            self.load_ini_file()
        else:
            messagebox.showerror("Error", "Only .ini files are supported.")

    def create_widgets(self):
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # 标题
        title_label = ttk.Label(main_frame, text=self.tool_title, font=TITLE_FONT)
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # 文件信息框架
        file_frame = ttk.LabelFrame(main_frame, text="File Info", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky="we", pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="File Path:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10)
        )
        self.file_path_var = tk.StringVar(value=self.ini_file)
        file_path_entry = ttk.Entry(
            file_frame, textvariable=self.file_path_var, state="readonly"
        )
        file_path_entry.grid(row=0, column=1, sticky="we", padx=(0, 10))

        # browse button
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.grid(row=0, column=2)
        # export button
        export_btn = ttk.Button(
            file_frame, text="Export", command=self.export, style="Accent.TButton"
        )
        export_btn.grid(row=0, column=3, padx=(10, 0))
        # reload button
        reload_btn = ttk.Button(
            file_frame,
            text="Reload",
            command=self.confirm_reload,
            style="Red.TButton",
        )
        reload_btn.grid(row=0, column=4, padx=(2, 0))
        initialize_btn = ttk.Button(
            file_frame,
            text="Initialize",
            command=self.initialize_app,
            style="Red.TButton",
        )
        # initialize button
        initialize_btn.grid(row=0, column=5, padx=(2, 0))

        # SKU Operations 区块
        sku_ops_frame = ttk.LabelFrame(main_frame, text="SKU Operations", padding="10")
        sku_ops_frame.grid(row=2, column=0, columnspan=3, sticky="we", pady=(0, 10))
        sku_ops_frame.columnconfigure(1, weight=1)
        # SKU 选择框
        self.sku_var = tk.StringVar()
        ttk.Label(sku_ops_frame, text="SKU:").pack(side=tk.LEFT, padx=(0, 15))
        self.sku_combobox = ttk.Combobox(
            sku_ops_frame, textvariable=self.sku_var, state="readonly", width=30
        )
        self.sku_combobox.pack(side=tk.LEFT, padx=(5, 0))
        self.sku_combobox.bind("<<ComboboxSelected>>", lambda e: self.filter_tests())
        self.sku_combobox["values"] = []
        self.sku_var.set("")
        # SKU 批量添加后缀
        self.sku_suffix_var = tk.StringVar(value=DEFAULT_SKU_SUFFIX)
        sku_suffix_entry = ttk.Entry(
            sku_ops_frame, textvariable=self.sku_suffix_var, width=25
        )
        sku_suffix_entry.pack(side=tk.LEFT, padx=(10, 0))

        def add_suffix_to_skus():
            suffix = self.sku_suffix_var.get()
            if not suffix:
                messagebox.showwarning("Warning", "Suffix cannot be empty!")
                return
            # 更新 SKU 列表
            new_sku_list = [sku + suffix for sku in self._sku_list]
            sku_map = {old: new for old, new in zip(self._sku_list, new_sku_list)}
            # 只修改 Identifier 字段和 SKU 名称，保留其它字段
            columns = getattr(self, "_test_columns", None)
            id_idx = (
                columns.index("Identifier")
                if columns and "Identifier" in columns
                else 1
            )
            for i, (row, sku) in enumerate(self._all_rows_with_sku):
                new_sku = sku_map.get(sku, sku)
                # 只改 Identifier 字段
                row[id_idx] = new_sku
                self._all_rows_with_sku[i] = (row, new_sku)
            for i, row in enumerate(self._all_rows):
                row[id_idx] = sku_map.get(row[id_idx], row[id_idx])
            self._sku_list = new_sku_list
            self.sku_combobox["values"] = self._sku_list
            # 当前选中SKU也同步
            if self.sku_var.get() in sku_map:
                self.sku_var.set(sku_map[self.sku_var.get()])
            # 保证 _all_rows_with_sku 的 sku 始终等于 row 的 Identifier 字段
            self._all_rows_with_sku = [(row, row[id_idx]) for row in self._all_rows]
            self.filter_tests()

        def backspace_sku_suffix():
            sku = self.sku_var.get()
            if not sku or len(sku) <= 1:
                return
            new_sku = sku[:-1]
            if new_sku in self._sku_list:
                messagebox.showwarning(
                    "SKU Duplicate",
                    "Target SKU name is duplicated with another SKU, please check.",
                )
                return
            # 1. 更新 sku_combobox 和 self._sku_list
            sku_list = list(self.sku_combobox["values"])
            if sku in sku_list:
                idx = sku_list.index(sku)
                sku_list[idx] = new_sku
                self.sku_combobox["values"] = sku_list
            if sku in self._sku_list:
                idx = self._sku_list.index(sku)
                self._sku_list[idx] = new_sku
            self.sku_var.set(new_sku)
            # 2. 只重命名所有属于该 SKU 的 test item，不做插入/append
            columns = getattr(self, "_test_columns", None)
            id_idx = (
                columns.index("Identifier")
                if columns and "Identifier" in columns
                else 1
            )
            for i, (row, s) in enumerate(self._all_rows_with_sku):
                if s == sku:
                    row[id_idx] = new_sku
                    self._all_rows_with_sku[i] = (row, new_sku)
            for i, row in enumerate(self._all_rows):
                if row[id_idx] == sku:
                    row[id_idx] = new_sku
            # 保证 _all_rows_with_sku 的 sku 始终等于 row 的 Identifier 字段
            self._all_rows_with_sku = [(row, row[id_idx]) for row in self._all_rows]
            self.renumber_index_for_current_sku()

        def add_suffix_to_current_sku():
            sku = self.sku_var.get()
            suffix = self.sku_suffix_var.get()
            if not sku or not suffix:
                messagebox.showwarning("Warning", "SKU and Suffix cannot be empty!")
                return
            new_sku = sku + suffix
            if new_sku in self._sku_list:
                messagebox.showwarning(
                    "SKU Duplicate",
                    "Target SKU name is duplicated with another SKU, please check.",
                )
                return
            # 更新 sku_combobox 和 self._sku_list
            sku_list = list(self.sku_combobox["values"])
            if sku in sku_list:
                idx = sku_list.index(sku)
                sku_list[idx] = new_sku
                self.sku_combobox["values"] = sku_list
            if sku in self._sku_list:
                idx = self._sku_list.index(sku)
                self._sku_list[idx] = new_sku
            self.sku_var.set(new_sku)
            # 重命名所有属于该 SKU 的 test item，只改 Identifier 字段
            columns = getattr(self, "_test_columns", None)
            id_idx = (
                columns.index("Identifier")
                if columns and "Identifier" in columns
                else 1
            )
            for i, (row, s) in enumerate(self._all_rows_with_sku):
                if s == sku:
                    row[id_idx] = new_sku
                    self._all_rows_with_sku[i] = (row, new_sku)
            for i, row in enumerate(self._all_rows):
                if row[id_idx] == sku:
                    row[id_idx] = new_sku
            # 保证 _all_rows_with_sku 的 sku 始终等于 row 的 Identifier 字段
            self._all_rows_with_sku = [(row, row[id_idx]) for row in self._all_rows]
            self.renumber_index_for_current_sku()

        add_suffix_to_current_btn = ttk.Button(
            sku_ops_frame,
            text="Add suffix",
            command=add_suffix_to_current_sku,
            width=12,
        )
        add_suffix_to_current_btn.pack(side=tk.LEFT, padx=(10, 0))
        add_suffix_to_skus_btn = ttk.Button(
            sku_ops_frame, text="Add suffixes", command=add_suffix_to_skus, width=12
        )
        add_suffix_to_skus_btn.pack(side=tk.LEFT, padx=(2, 0))
        # 定义红色按钮样式
        style = ttk.Style()
        style.configure("Red.TButton", foreground="white", background="#d9534f")
        style.map(
            "Red.TButton",
            background=[("active", "#c9302c"), ("!active", "#d9534f")],
            foreground=[("disabled", "#f9f9f9"), ("!disabled", "white")],
        )
        backspace_btn = ttk.Button(
            sku_ops_frame,
            text="Backspace",
            command=backspace_sku_suffix,
            width=10,
            style="Red.TButton",
        )
        backspace_btn.pack(side=tk.LEFT, padx=(2, 0))

        def goto_prev_sku():
            sku_list = list(self.sku_combobox["values"])
            if not sku_list or not self.sku_var.get():
                return
            idx = (
                sku_list.index(self.sku_var.get())
                if self.sku_var.get() in sku_list
                else -1
            )
            if idx > 0:
                self.sku_var.set(sku_list[idx - 1])
                self.renumber_index_for_current_sku()
            else:
                messagebox.showinfo("Info", "This is the first SKU!")

        def goto_next_sku():
            sku_list = list(self.sku_combobox["values"])
            if not sku_list or not self.sku_var.get():
                return
            idx = (
                sku_list.index(self.sku_var.get())
                if self.sku_var.get() in sku_list
                else -1
            )
            if 0 <= idx < len(sku_list) - 1:
                self.sku_var.set(sku_list[idx + 1])
                self.renumber_index_for_current_sku()
            else:
                messagebox.showinfo("Info", "This is the last SKU!")

        prev_btn = ttk.Button(sku_ops_frame, text="Previous SKU", command=goto_prev_sku)
        prev_btn.pack(side=tk.LEFT, padx=(10, 0))

        next_btn = ttk.Button(sku_ops_frame, text="Next SKU", command=goto_next_sku)
        next_btn.pack(side=tk.LEFT, padx=(2, 0))

        # 创建Notebook用于标签页
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=(0, 10))

        # 测试项目标签页
        self.create_tests_tab()

        # Info标签页
        self.create_info_tab()

        # 按钮框架
        # button_frame = ttk.Frame(main_frame)
        # button_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))

        # save_btn = ttk.Button(button_frame, text="保存文件", command=self.save_file, style='Accent.TButton')
        # save_btn.pack(side=tk.LEFT, padx=(0, 10))

    def create_info_tab(self):
        """创建Info标签页"""
        info_frame = ttk.Frame(self.notebook)
        self.notebook.add(info_frame, text="Info")

        # Info部分编辑器
        info_label = ttk.Label(
            info_frame, text="Info Section", font=("Arial", 12, "bold")
        )
        info_label.pack(anchor=tk.W, padx=10, pady=(10, 5))

        # 创建Info字段的输入框
        info_fields_frame = ttk.Frame(info_frame)
        info_fields_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # UnitCount
        ttk.Label(info_fields_frame, text="UnitCount:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5
        )
        self.unit_count_var = tk.StringVar()
        ttk.Entry(info_fields_frame, textvariable=self.unit_count_var, width=20).grid(
            row=0, column=1, sticky=tk.W, pady=5
        )

        # Export Date
        ttk.Label(info_fields_frame, text="Export Date:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10), pady=5
        )
        self.export_date_var = tk.StringVar()
        ttk.Entry(info_fields_frame, textvariable=self.export_date_var, width=30).grid(
            row=1, column=1, sticky=tk.W, pady=5
        )

        # 更新日期按钮
        update_date_btn = ttk.Button(
            info_fields_frame, text="Update Date", command=self.update_export_date
        )
        update_date_btn.grid(row=1, column=2, padx=(10, 0), pady=5)

    def create_tests_tab(self):
        """创建测试项目标签页"""
        tests_frame = ttk.Frame(self.notebook)
        self.notebook.add(tests_frame, text="Test Items")

        # 顶部按钮区
        top_btn_frame = ttk.Frame(tests_frame)
        top_btn_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        # add_btn = ttk.Button(top_btn_frame, text="Add", command=self.add_test_item)
        # add_btn.pack(side=tk.LEFT)

        # 搜索框架
        search_frame = ttk.Frame(tests_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_tests)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=60)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))

        clear_search_btn = ttk.Button(
            search_frame, text="Clear Search", command=self.clear_search, width=12
        )
        clear_search_btn.pack(side=tk.LEFT)

        # 当前 SKU test item 数量标签按钮
        self.sku_count_var = tk.StringVar(value="0 items")
        sku_count_btn = ttk.Button(
            search_frame,
            textvariable=self.sku_count_var,
            width=8,
            style="Accent.TButton",
        )
        sku_count_btn.pack(side=tk.LEFT, padx=(10, 0))

        def update_sku_count():
            sku = self.sku_var.get()
            count = sum(
                1 for (row, s) in getattr(self, "_all_rows_with_sku", []) if s == sku
            )
            self.sku_count_var.set(f"{count} items")

        # 绑定 SKU 变化和数据变动时刷新
        self.sku_var.trace_add("write", lambda *args: update_sku_count())
        # 在批量操作、插入、删除、切换 SKU 后也应调用 update_sku_count()
        orig_filter_tests = self.filter_tests

        def filter_tests_with_count(*args, **kwargs):
            orig_filter_tests(*args, **kwargs)
            update_sku_count()

        self.filter_tests = filter_tests_with_count
        # 初始化时刷新
        update_sku_count()

        # 创建Treeview用于显示测试项目
        columns = getattr(self, "_test_columns", None)
        if columns is None:
            columns = [
                "Index",
                "Identifier",
                "TestID",
                "Description",
                "Enabled",
                "StringLimit",
                "LowLimit",
                "HighLimit",
                "LimitType",
                "Unit",
                "Parameters",
            ]
        else:
            # 若 header 没有 Identifier，插入
            if "Identifier" not in columns:
                columns = columns[:1] + ["Identifier"] + columns[1:]
        self._test_columns = columns
        tree_frame = ttk.Frame(tests_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        self.tree_frame = tree_frame  # 保存引用，便于后续操作
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=20,
            selectmode="extended",
        )

        # 设置列标题
        column_headers = {
            "Index": "Index",
            "Identifier": "Identifier",
            "TestID": "TestID",
            "Description": "Description",
            "Enabled": "Enabled",
            "StringLimit": "StringLimit",
            "LowLimit": "LowLimit",
            "HighLimit": "HighLimit",
            "LimitType": "LimitType",
            "Unit": "Unit",
            "Parameters": "Parameters",
        }

        for col in columns:
            self.tree.heading(col, text=column_headers[col])
            if col == "Index":
                self.tree.column(col, width=50, minwidth=20, stretch=False)
            elif col == "Identifier":
                self.tree.column(col, width=180, minwidth=120, stretch=False)
            elif col == "Description" or col == "StringLimit" or col == "Unit":
                self.tree.column(col, width=180, minwidth=120, stretch=False)
            elif col == "Parameters":
                self.tree.column(col, width=400, minwidth=120, stretch=False)
            else:
                self.tree.column(col, width=80, minwidth=50, stretch=False)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        h_scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # 使用grid布局，确保纵向滚动条在右侧，横向在底部
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # 双击编辑
        self.tree.bind("<Double-1>", self.edit_test_item)
        # 拖动排序功能
        self.tree.bind("<ButtonPress-1>", self._on_tree_drag_start)
        self.tree.bind("<B1-Motion>", self._on_tree_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self._on_tree_drag_release)

        # 右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.edit_selected_item)
        self.context_menu.add_command(
            label="Insert Before", command=lambda: self.insert_test_item(before=True)
        )
        self.context_menu.add_command(
            label="Insert After", command=lambda: self.insert_test_item(before=False)
        )
        self.context_menu.add_command(label="Copy", command=self.copy_selected_item)
        self.context_menu.add_command(
            label="Copy To Other SKUs", command=self.copy_to_all_skus
        )
        self.context_menu.add_command(label="Delete", command=self.delete_selected_item)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # 支持键盘 Ctrl+C 复制
        def on_tree_ctrl_c(event):
            selected = self.tree.selection()
            if not selected:
                return "break"
            header = "(Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters)"
            current_sku = self.sku_var.get() if hasattr(self, "sku_var") else ""
            # 构建 index 到 row 的映射（当前 SKU）
            index_to_row = {
                str(row[0]): row
                for (row, sku) in self._all_rows_with_sku
                if sku == current_sku
            }
            ui_order = list(self.tree.get_children())
            selected_ui_pos = [(ui_order.index(item), item) for item in selected]
            selected_ui_pos.sort()

            def format_row_export(row):
                formatted = []
                for i, v in enumerate(row):
                    if i == 3 and str(v) in ("0", "1"):
                        formatted.append(str(v))
                    else:
                        formatted.append(f"'{v}'")
                return f"({','.join(formatted)})"

            rows = []
            for idx, (ui_pos, item) in enumerate(selected_ui_pos, 1):
                values = self.tree.item(item)["values"]
                index = str(values[0])
                row = index_to_row.get(index, list(values))
                # 构造 export_row: Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters
                export_row = [row[1]] + list(
                    row[2:]
                )  # row1]是Identifier，row[2:]是其他字段
                line = f"{row[0]}={header} VALUES {format_row_export(export_row)}"
                rows.append(line)
            text = "\n".join(rows)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()

            # 自动消失的提示框
            def show_toast(msg, duration=2000):
                toast = tk.Toplevel(self.root)
                toast.overrideredirect(True)
                toast.attributes("-topmost", True)
                toast.configure(bg="#333")
                label = tk.Label(
                    toast,
                    text=msg,
                    fg="white",
                    bg="#333",
                    font=("Segoe UI", 12),
                    padx=20,
                    pady=10,
                )
                label.pack()
                self.root.update_idletasks()
                x = (
                    self.root.winfo_rootx()
                    + self.root.winfo_width() // 2
                    - toast.winfo_reqwidth() // 2
                )
                y = self.root.winfo_rooty() + 60
                toast.geometry(f"+{x}+{y}")
                toast.after(duration, toast.destroy)

            show_toast("Selected items are copied to clipboard.")
            return "break"

        self.tree.bind("<Control-c>", on_tree_ctrl_c)
        self.tree.bind("<Control-C>", on_tree_ctrl_c)

        # 支持键盘 Ctrl+V 粘贴
        def on_tree_ctrl_v(event):
            try:
                text = self.root.clipboard_get()
            except Exception:
                return "break"
            if not text:
                return "break"
            # 匹配 test item 导出格式的行（允许 Identifier 字段为任意字符串）
            pattern = r"^(\d+)=.*?VALUES \((.*)\)$"
            lines = text.strip().splitlines()
            parsed_rows = []
            for line in lines:
                m = re.match(r"^(\d+)=.*?VALUES \((.*)\)$", line)
                if not m:
                    print(f"Regex not matched: {line}")
                    continue
                values_str = m.group(2)
                values = []
                current = ""
                in_quotes = False
                i = 0
                while i < len(values_str):
                    c = values_str[i]
                    if c == "'":
                        in_quotes = not in_quotes
                        current += c
                    elif c == "," and not in_quotes:
                        v = current.strip()
                        if v.startswith("'") and v.endswith("'"):
                            v = v[1:-1]
                        values.append(v)
                        current = ""
                    else:
                        current += c
                    i += 1
                if current:
                    v = current.strip()
                    if v.startswith("'") and v.endswith("'"):
                        v = v[1:-1]
                    values.append(v)
                if len(values) != 10:
                    print(f"Wrong number of fields: {len(values)}")
                    continue
                parsed_rows.append(values)
            if not parsed_rows:
                print("No valid rows to paste")
                return "break"
            current_sku = self.sku_var.get() if hasattr(self, "sku_var") else ""
            if not current_sku:
                messagebox.showwarning(
                    "Warning", "No SKU selected. Please select SKU/SKUs first."
                )
                return "break"
            columns = getattr(self, "_test_columns", None)
            id_idx = (
                columns.index("Identifier")
                if columns and "Identifier" in columns
                else 1
            )
            # 计算插入点：选中项最后一个在当前SKU中的位置+1，否则插入SKU末尾
            selected = self.tree.selection()
            sku_indices = [
                i
                for i, (row, sku) in enumerate(self._all_rows_with_sku)
                if sku == current_sku
            ]
            insert_at = None
            if selected:
                # 找到所有选中项在tree中的顺序
                ui_order = list(self.tree.get_children())
                selected_ui_pos = [(ui_order.index(item), item) for item in selected]
                selected_ui_pos.sort()
                last_selected_item = selected_ui_pos[-1][1]
                last_selected_index = str(
                    self.tree.item(last_selected_item)["values"][0]
                )
                # 找到 _all_rows_with_sku 中当前SKU下最后一个选中项的全局索引
                insert_at = None
                for idx in reversed(sku_indices):
                    if str(self._all_rows_with_sku[idx][0][0]) == last_selected_index:
                        insert_at = idx + 1
                        break
                if insert_at is None:
                    insert_at = (
                        sku_indices[-1] + 1
                        if sku_indices
                        else len(self._all_rows_with_sku)
                    )
            else:
                insert_at = (
                    sku_indices[-1] + 1 if sku_indices else len(self._all_rows_with_sku)
                )
            # index 自动递增（以当前SKU下最大index+1为起点）
            next_index = str(len(sku_indices) + 1)
            # 但如果插入点在SKU中间，需用插入点前的index+1
            if selected and insert_at > sku_indices[0]:
                # 找到插入点前一个在当前SKU的index
                prev_idx = None
                for idx in reversed(sku_indices):
                    if idx < insert_at:
                        prev_idx = idx
                        break
                if prev_idx is not None:
                    next_index = str(int(self._all_rows_with_sku[prev_idx][0][0]) + 1)
            for row_values in parsed_rows:
                new_row = [next_index] + list(row_values)
                new_row[id_idx] = current_sku
                self._all_rows_with_sku.insert(insert_at, (new_row, current_sku))
                self._all_rows.insert(insert_at, new_row)
                insert_at += 1
                next_index = str(int(next_index) + 1)
            self.renumber_index_for_current_sku()

            def show_toast(msg, duration=2000):
                toast = tk.Toplevel(self.root)
                toast.overrideredirect(True)
                toast.attributes("-topmost", True)
                toast.configure(bg="#333")
                label = tk.Label(
                    toast,
                    text=msg,
                    fg="white",
                    bg="#333",
                    font=("Segoe UI", 12),
                    padx=20,
                    pady=10,
                )
                label.pack()
                self.root.update_idletasks()
                x = (
                    self.root.winfo_rootx()
                    + self.root.winfo_width() // 2
                    - toast.winfo_reqwidth() // 2
                )
                y = self.root.winfo_rooty() + 60
                toast.geometry(f"+{x}+{y}")
                toast.after(duration, toast.destroy)

            show_toast("Items are pasted to the list.")
            return "break"

        self.tree.bind("<Control-v>", on_tree_ctrl_v)
        self.tree.bind("<Control-V>", on_tree_ctrl_v)

        # 添加覆盖层提示
        self.overlay_label = tk.Label(
            self.tree_frame,
            text="Drag and drop an INI file here to edit\n(or click the Browse button above)",
            font=("Arial", 16, "bold"),
            fg="#888",
            bg="#f8f8f8",
            justify="center",
        )
        self.overlay_label.place(relx=0.5, rely=0.5, anchor="center")
        self.overlay_label.lower(self.tree)  # 保证tree在上层
        self.update_overlay()
        # 初始化sku相关
        self._sku_list = []
        self._all_rows_with_sku = []

        # 支持键盘 Ctrl+X 剪切
        def on_tree_ctrl_x(event):
            selected = self.tree.selection()
            if not selected:
                return "break"
            header = "(Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters)"
            current_sku = self.sku_var.get() if hasattr(self, "sku_var") else ""
            # 构建 index 到 row 的映射（当前 SKU）
            index_to_row = {
                str(row[0]): row
                for (row, sku) in self._all_rows_with_sku
                if sku == current_sku
            }
            ui_order = list(self.tree.get_children())
            selected_ui_pos = [(ui_order.index(item), item) for item in selected]
            selected_ui_pos.sort()

            def format_row_export(row):
                formatted = []
                for i, v in enumerate(row):
                    if i == 3 and str(v) in ("0", "1"):
                        formatted.append(str(v))
                    else:
                        formatted.append(f"'{v}'")
                return f"({','.join(formatted)})"

            rows = []
            selected_indices = set()
            for idx, (ui_pos, item) in enumerate(selected_ui_pos, 1):
                values = self.tree.item(item)["values"]
                index = str(values[0])
                row = index_to_row.get(index, list(values))
                export_row = [row[1]] + list(row[2:])
                line = f"{row[0]}={header} VALUES {format_row_export(export_row)}"
                rows.append(line)
                selected_indices.add(index)
            text = "\n".join(rows)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()

            # 删除选中项（从 _all_rows_with_sku 和 _all_rows）
            # 只删除当前 SKU 下的选中项
            new_all_rows_with_sku = []
            for row, sku in self._all_rows_with_sku:
                if sku == current_sku and str(row[0]) in selected_indices:
                    continue
                new_all_rows_with_sku.append((row, sku))
            self._all_rows_with_sku = new_all_rows_with_sku
            self._all_rows = [row for (row, sku) in self._all_rows_with_sku]
            self.renumber_index_for_current_sku()

            def show_toast(msg, duration=2000):
                toast = tk.Toplevel(self.root)
                toast.overrideredirect(True)
                toast.attributes("-topmost", True)
                toast.configure(bg="#333")
                label = tk.Label(
                    toast,
                    text=msg,
                    fg="white",
                    bg="#333",
                    font=("Segoe UI", 12),
                    padx=20,
                    pady=10,
                )
                label.pack()
                self.root.update_idletasks()
                x = (
                    self.root.winfo_rootx()
                    + self.root.winfo_width() // 2
                    - toast.winfo_reqwidth() // 2
                )
                y = self.root.winfo_rooty() + 60
                toast.geometry(f"+{x}+{y}")
                toast.after(duration, toast.destroy)

            show_toast("Selected items are cut to clipboard.")
            return "break"

        self.tree.bind("<Control-x>", on_tree_ctrl_x)
        self.tree.bind("<Control-X>", on_tree_ctrl_x)

    def load_ini_file(self):
        """加载INI文件"""
        try:
            if os.path.exists(self.ini_file):
                # 直接读取文件内容
                with open(self.ini_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # 解析Info部分
                self.parse_info_section(content)

                # 解析测试项目部分
                self.parse_tests_section(content)

                pass  # 不再弹窗提示，拖入时弹窗由 on_drop_file 负责
            else:
                messagebox.showerror("Error", f"File not found: {self.ini_file}")
        except Exception as e:
            import traceback

            traceback.print_exc()
            messagebox.showerror("Error", f"Error loading file: {str(e)}")

    def parse_info_section(self, content):
        """解析Info部分"""
        try:
            # 查找[Info]部分
            info_match = re.search(r"\[Info\]\s*\n(.*?)(?=\n\[|\Z)", content, re.DOTALL)
            if info_match:
                info_content = info_match.group(1)

                # 解析UnitCount
                unit_count_match = re.search(r"UnitCount\s*=\s*(.+)", info_content)
                if unit_count_match:
                    self.unit_count_var.set(unit_count_match.group(1).strip())

                # 解析Export Date
                export_date_match = re.search(r"Export Date\s*=\s*(.+)", info_content)
                if export_date_match:
                    self.export_date_var.set(export_date_match.group(1).strip())
        except Exception as e:
            print(f"Error parsing Info section: {e}")

    def parse_tests_section(self, content):
        """解析测试项目部分"""
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            self._all_rows = []
            self._all_rows_with_sku = []
            self._sku_list = []
            self._test_columns = None
            sections = re.findall(
                r"\[([^\]]+)\]\s*\n(.*?)(?=\n\[|\Z)", content, re.DOTALL
            )
            for section_name, section_content in sections:
                if section_name == "Info":
                    continue
                # 提取 header
                if self._test_columns is None:
                    header_match = re.search(
                        r"^\s*\(([^)]*)\)", section_content, re.MULTILINE
                    )
                    if header_match:
                        header_line = header_match.group(1).strip()
                        columns = [h.strip() for h in header_line.split(",")]
                        self._test_columns = ["Index"] + columns
                    else:
                        self._test_columns = [
                            "Index",
                            "Identifier",
                            "TestID",
                            "Description",
                            "Enabled",
                            "StringLimit",
                            "LowLimit",
                            "HighLimit",
                            "LimitType",
                            "Unit",
                            "Parameters",
                        ]
                self._parse_single_section(section_name, section_content)
            # 更新sku下拉框
            sku_values = self._sku_list
            self.sku_combobox["values"] = sku_values
            if self._sku_list:
                self.sku_var.set(self._sku_list[0])
            else:
                self.sku_var.set("")
            self.filter_tests()
            self.update_overlay()
        except Exception as e:
            print(f"Error parsing Test Items section: {e}")
            self.update_overlay()

    def _parse_single_section(self, section_name, section_content):
        if section_name not in self._sku_list:
            self._sku_list.append(section_name)
        lines = section_content.splitlines()
        current_idx = None
        current_value = []
        for line in lines:
            m = re.match(r"^\s*(\d+)\s*=\s*(.*)", line)
            if m:
                # 保存前一个
                if current_idx is not None:
                    self._append_row_from_value(
                        current_idx, current_value, section_name
                    )
                # 新项
                current_idx = m.group(1)
                current_value = [m.group(2)]
            else:
                # 多行内容
                if current_idx is not None:
                    current_value.append(line)
        # 最后一项
        if current_idx is not None:
            self._append_row_from_value(current_idx, current_value, section_name)

    def _append_row_from_value(self, idx, value_lines, section_name):
        test_value = "\n".join(value_lines).strip()
        parsed_data = self.parse_test_value(test_value)
        if not parsed_data:
            print(f"Failed to parse test item: index={idx}, content={test_value}")
        if parsed_data:
            columns = getattr(self, "_test_columns", None)
            if columns is None:
                columns = [
                    "Index",
                    "Identifier",
                    "TestID",
                    "Description",
                    "Enabled",
                    "StringLimit",
                    "LowLimit",
                    "HighLimit",
                    "LimitType",
                    "Unit",
                    "Parameters",
                ]
            row = [str(idx)]
            for col in columns[1:]:
                v = parsed_data.get(col, "")
                row.append(v if v is not None else "")
            self._all_rows.append(list(row))
            self._all_rows_with_sku.append((list(row), section_name))

    def parse_test_value(self, test_value):
        try:
            values = self._extract_values_from_test_value(test_value)
            if len(values) >= 10:
                return {
                    "Identifier": values[0],
                    "TestID": values[1],
                    "Description": values[2],
                    "Enabled": values[3],
                    "StringLimit": values[4],
                    "LowLimit": values[5],
                    "HighLimit": values[6],
                    "LimitType": values[7],
                    "Unit": values[8],
                    "Parameters": values[9] if len(values) > 9 else "",
                }
            else:
                print(f"Not enough fields (expected at least 10), got: {values}")
        except Exception as e:
            print(f"Error parsing test value: {e}")
        return None

    def _extract_values_from_test_value(self, test_value):
        pattern = r"VALUES\s*\((.*)\)"
        match = re.search(pattern, test_value)
        if not match:
            print(f"VALUES not matched: {test_value}")
            return []
        values_str = match.group(1)
        # 手动分割，支持空字段和引号内逗号
        values = []
        current = ""
        in_quotes = False
        i = 0
        while i < len(values_str):
            char = values_str[i]
            if char == "'":
                in_quotes = not in_quotes
                current += char
            elif char == "," and not in_quotes:
                values.append(current.strip())
                current = ""
            else:
                current += char
            i += 1
        if current:
            values.append(current.strip())
        # 去除首尾单引号，保留空字符串
        return [self._strip_quotes_keep_empty(v) for v in values]

    def _strip_quotes_keep_empty(self, s):
        s = s.strip()
        if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
            return s[1:-1]
        return s

    def filter_tests(self, *args):
        search_term = self.search_var.get().lower()
        selected_sku = self.sku_var.get() if hasattr(self, "sku_var") else ""
        filtered = []
        for row, sku in getattr(self, "_all_rows_with_sku", []):
            if (selected_sku == sku) and any(
                search_term in str(v).lower() for v in row
            ):
                filtered.append([v if v is not None else "" for v in row])
        self.tree.delete(*self.tree.get_children())
        for row in filtered:
            self.tree.insert("", "end", values=row)
        self.update_overlay()
        # 实时更新 test item 数量到 sku count
        if hasattr(self, "sku_count_var"):
            self.sku_count_var.set(f"{len(filtered)} items")

    def clear_search(self):
        """清除搜索并恢复所有行显示"""
        self.search_var.set("")
        self.filter_tests()

    def edit_selected_item(self):
        """编辑选中的项目"""
        selected = self.tree.selection()
        if selected:
            self.edit_test_item(None)

    def edit_test_item(self, event):
        """编辑测试项目"""
        selected = self.tree.selection()
        if not selected:
            return
        item_id = selected[0]
        item = self.tree.item(item_id)
        index = str(item["values"][0])
        current_sku = self.sku_var.get() if hasattr(self, "sku_var") else None
        # Only get the row for the current SKU and index
        row = next(
            (
                r
                for r, sku in self._all_rows_with_sku
                if str(r[0]) == index and sku == current_sku
            ),
            None,
        )
        if row is None:
            return
        values = row  # 这里的 values 一定是完整的 row，含 Index
        old_values = [v if v is not None else "" for v in values[1:]]  # 只要字段部分

        def open_edit_dialog_with_apply_option(on_save, values=None):
            dialog = tk.Toplevel(self.root)
            dialog.withdraw()  # 先隐藏，避免闪烁
            dialog.title("Edit Test Item")
            dialog.geometry("600x635")
            columns = getattr(self, "_test_columns", None)
            if columns is None:
                columns = [
                    "Index",
                    "Identifier",
                    "TestID",
                    "Description",
                    "Enabled",
                    "StringLimit",
                    "LowLimit",
                    "HighLimit",
                    "LimitType",
                    "Unit",
                    "Parameters",
                ]
            fields = list(columns)
            field_vars = {}
            if values is None:
                row_map = {field: "" for field in fields}
                values_list = [row_map[field] for field in fields]
            else:
                columns_ref = (
                    self._test_columns if self._test_columns is not None else fields
                )
                row_dict = {col: val for col, val in zip(columns_ref, values)}
                row_map = {field: row_dict.get(field, "") for field in fields}
                values_list = [row_map[field] for field in fields]
                # print('fields:', fields)
                # print('columns_ref:', columns_ref)
                # print('row:', values)
                # print('row_dict:', row_dict)
                # print('row_map:', row_map)
                # print('values_list:', values_list)
            for i, field in enumerate(fields):
                value = values_list[i]
                ttk.Label(dialog, text=f"{field}:").grid(
                    row=i, column=0, sticky=tk.W, padx=10, pady=5
                )
                var = tk.StringVar(value=value)
                field_vars[field] = var
                if field == "Parameters":
                    text_widget = scrolledtext.ScrolledText(dialog, height=2, width=50)
                    text_widget.grid(row=i, column=1, sticky="we", padx=10, pady=5)
                    text_widget.insert("1.0", var.get())
                    field_vars[field] = text_widget
                elif field == "Index":
                    entry = ttk.Entry(
                        dialog, textvariable=var, width=50, state="readonly"
                    )
                    entry.grid(row=i, column=1, sticky="we", padx=10, pady=5)
                else:
                    entry = ttk.Entry(dialog, textvariable=var, width=50)
                    entry.grid(row=i, column=1, sticky="we", padx=10, pady=5)

                    # 添加清除小入口
                    def make_clear_callback(v=var, e=entry):
                        def clear():
                            v.set("")

                        return clear

                    clear_btn = tk.Label(
                        dialog,
                        text="x",
                        cursor="hand2",
                        fg="#888",
                        bg="#fff",
                        font=("Arial", 7),
                    )
                    clear_btn.place(in_=entry, relx=1.0, x=-2, y=1, anchor="ne")
                    clear_btn.bind(
                        "<Button-1>", lambda e, cb=make_clear_callback(): cb()
                    )

                    # 自动显示/隐藏 ×
                    def on_var_change(*args, v=var, btn=clear_btn):
                        if v.get():
                            btn.place(in_=entry, relx=1.0, x=-2, y=1, anchor="ne")
                        else:
                            btn.place_forget()

                    var.trace_add("write", on_var_change)
                    # 初始状态
                    if not var.get():
                        clear_btn.place_forget()
            # Apply option
            apply_var = tk.StringVar(value="all_by_field")
            option_frame = ttk.LabelFrame(dialog, text="Apply Change To", padding=10)
            option_frame.grid(
                row=len(fields), column=0, columnspan=2, pady=(10, 0), sticky="we"
            )
            ttk.Radiobutton(
                option_frame,
                text="All SKUs + Exact field (only update fields whose value matches the original)",
                variable=apply_var,
                value="all_by_field",
            ).pack(anchor=tk.W)
            ttk.Radiobutton(
                option_frame,
                text="All SKUs + Any fields (replace any fields with same original value)",
                variable=apply_var,
                value="all",
            ).pack(anchor=tk.W)
            ttk.Radiobutton(
                option_frame,
                text="Current SKU only + Exact fields (only update fields whose value matches the original)",
                variable=apply_var,
                value="sku_by_field",
            ).pack(anchor=tk.W)
            ttk.Radiobutton(
                option_frame,
                text="Current SKU only + Any fields (replace any fields with same original value)",
                variable=apply_var,
                value="sku_only",
            ).pack(anchor=tk.W)
            ttk.Radiobutton(
                option_frame,
                text="Current item only",
                variable=apply_var,
                value="current",
            ).pack(anchor=tk.W)
            # Save/cancel buttons
            button_frame = ttk.Frame(dialog)
            button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=20)

            def save_changes():
                new_values = []
                for field in fields:
                    if field == "Parameters":
                        new_values.append(field_vars[field].get("1.0", tk.END).strip())
                    else:
                        new_values.append(field_vars[field].get())
                # 二次确认
                if apply_var.get() == "all":
                    if not messagebox.askyesno(
                        "Confirm Apply to All SKUs",
                        "This operation will affect ALL SKUs. Are you sure you want to continue?",
                        icon="warning",
                    ):
                        return
                if apply_var.get() == "all_by_field":
                    if not messagebox.askyesno(
                        "Confirm Apply to All SKUs by field",
                        "This operation will update only fields whose value matches the original, across ALL SKUs. Are you sure you want to continue?",
                        icon="warning",
                    ):
                        return
                if apply_var.get() == "sku_by_field":
                    if not messagebox.askyesno(
                        "Confirm Apply to Current SKU by field",
                        "This operation will update only fields whose value matches the original, in the current SKU. Are you sure you want to continue?",
                        icon="warning",
                    ):
                        return
                on_save(new_values, apply_var.get())
                dialog.destroy()

            ttk.Button(button_frame, text="Save", command=save_changes).pack(
                side=tk.LEFT, padx=5
            )
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(
                side=tk.LEFT, padx=5
            )
            dialog.columnconfigure(1, weight=1)
            # 居中并显示
            dialog.update_idletasks()
            w = dialog.winfo_width()
            h = dialog.winfo_height()
            ws = dialog.winfo_screenwidth()
            hs = dialog.winfo_screenheight()
            x = (ws // 2) - (w // 2)
            y = (hs // 2) - (h // 2) - 50  # 向上移动 50 像素
            dialog.geometry(f"{w}x635+{x}+{y}")
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.deiconify()

        def on_save(new_values, apply_to):
            # new_values 现在是 fields 顺序的完整一行（含 Index）
            columns = getattr(self, "_test_columns", None)
            if columns is None:
                columns = [
                    "Index",
                    "Identifier",
                    "TestID",
                    "Description",
                    "Enabled",
                    "StringLimit",
                    "LowLimit",
                    "HighLimit",
                    "LimitType",
                    "Unit",
                    "Parameters",
                ]
            fields = list(columns)
            current_sku = self.sku_var.get() if hasattr(self, "sku_var") else None
            row_dict = {field: val for field, val in zip(fields, new_values)}
            row_for_storage = [row_dict.get(col, "") for col in columns]
            # 更新 Treeview
            self.tree.item(item_id, values=row_for_storage)
            # 更新 _all_rows
            for i, row in enumerate(self._all_rows):
                if str(row[0]) == index:
                    self._all_rows[i] = list(row_for_storage)
                    break
            # old_values 也只针对非 Index 字段
            if apply_to == "sku_only":
                columns = (
                    self._test_columns
                    if self._test_columns is not None
                    else [
                        "Index",
                        "Identifier",
                        "TestID",
                        "Description",
                        "Enabled",
                        "StringLimit",
                        "LowLimit",
                        "HighLimit",
                        "LimitType",
                        "Unit",
                        "Parameters",
                    ]
                )
                n = len(old_values)
                current_sku = self.sku_var.get() if hasattr(self, "sku_var") else None
                for j in range(n):
                    old_val = old_values[j]
                    new_val = new_values[j + 1]
                    if old_val == new_val:
                        continue
                    for i, (row, sku) in enumerate(self._all_rows_with_sku):
                        if sku != current_sku:
                            continue
                        row_dict = {col_: val for col_, val in zip(columns, row)}
                        changed = False
                        for col in columns[1:]:  # 跳过 Index
                            if (
                                str(row_dict.get(col, "")).strip()
                                == str(old_val).strip()
                            ):
                                row_dict[col] = new_val
                                changed = True
                        if changed:
                            new_row = [row_dict.get(col_, "") for col_ in columns]
                            self._all_rows_with_sku[i] = (new_row, current_sku)
                self._all_rows = [row for (row, sku) in self._all_rows_with_sku]
                # 重新编号当前SKU下的Index字段
                sku_to_rows = {}
                for row in self._all_rows:
                    sku = row[columns.index("Identifier")]
                    sku_to_rows.setdefault(sku, []).append(row)
                for sku, rows in sku_to_rows.items():
                    for idx, row in enumerate(rows, 1):
                        row[0] = str(idx)
                self._all_rows_with_sku = [
                    (row, row[columns.index("Identifier")]) for row in self._all_rows
                ]
                # 重新统计所有SKU并同步下拉框（保持原有顺序）
                new_sku_list = []
                seen = set()
                for row in self._all_rows:
                    sku = row[columns.index("Identifier")]
                    if sku not in seen:
                        new_sku_list.append(sku)
                        seen.add(sku)
                self._sku_list = new_sku_list
                self.sku_combobox["values"] = self._sku_list
                if self.sku_var.get() not in self._sku_list:
                    if self._sku_list:
                        self.sku_var.set(self._sku_list[0])
                    else:
                        self.sku_var.set("")
                self.filter_tests()
                self.root.update_idletasks()
            elif apply_to == "all":
                columns = (
                    self._test_columns
                    if self._test_columns is not None
                    else [
                        "Index",
                        "Identifier",
                        "TestID",
                        "Description",
                        "Enabled",
                        "StringLimit",
                        "LowLimit",
                        "HighLimit",
                        "LimitType",
                        "Unit",
                        "Parameters",
                    ]
                )
                n = len(old_values)
                for j in range(n):
                    old_val = old_values[j]
                    new_val = new_values[j + 1]
                    if old_val == new_val:
                        continue
                    for i, (row, sku) in enumerate(self._all_rows_with_sku):
                        row_dict = {col_: val for col_, val in zip(columns, row)}
                        changed = False
                        for col in columns[1:]:  # 跳过 Index
                            # 只做全等整体替换
                            if (
                                str(row_dict.get(col, "")).strip()
                                == str(old_val).strip()
                            ):
                                row_dict[col] = new_val
                                changed = True
                        if changed:
                            new_row = [row_dict.get(col_, "") for col_ in columns]
                            new_sku = new_row[columns.index("Identifier")]
                            self._all_rows_with_sku[i] = (new_row, new_sku)
                self._all_rows = [row for (row, sku) in self._all_rows_with_sku]
                # 重新编号所有SKU下的Index字段，避免重复
                sku_to_rows = {}
                for row in self._all_rows:
                    sku = row[columns.index("Identifier")]
                    sku_to_rows.setdefault(sku, []).append(row)
                for sku, rows in sku_to_rows.items():
                    for idx, row in enumerate(rows, 1):
                        row[0] = str(idx)
                self._all_rows_with_sku = [
                    (row, row[columns.index("Identifier")]) for row in self._all_rows
                ]
                # 重新统计所有SKU并同步下拉框（保持原有顺序）
                new_sku_list = []
                seen = set()
                for row in self._all_rows:
                    sku = row[columns.index("Identifier")]
                    if sku not in seen:
                        new_sku_list.append(sku)
                        seen.add(sku)
                self._sku_list = new_sku_list
                self.sku_combobox["values"] = self._sku_list
                if self.sku_var.get() not in self._sku_list:
                    if self._sku_list:
                        self.sku_var.set(self._sku_list[0])
                    else:
                        self.sku_var.set("")
                self.filter_tests()
                self.root.update_idletasks()
            elif apply_to == "all_by_field":
                columns = (
                    self._test_columns
                    if self._test_columns is not None
                    else [
                        "Index",
                        "Identifier",
                        "TestID",
                        "Description",
                        "Enabled",
                        "StringLimit",
                        "LowLimit",
                        "HighLimit",
                        "LimitType",
                        "Unit",
                        "Parameters",
                    ]
                )
                fields = list(columns)
                # old_row_dict must be built from columns and values (full row, including Index)
                old_row_dict = {col: val for col, val in zip(columns, values)}
                new_row_dict = {col: val for col, val in zip(columns, new_values)}
                for i, (row, sku) in enumerate(self._all_rows_with_sku):
                    row_dict = {col: val for col, val in zip(columns, row)}
                    for col in columns:
                        old_val = old_row_dict.get(col, "")
                        new_val = new_row_dict.get(col, "")
                        row_val = row_dict.get(col, "")
                        # Only update if the field was changed in the Edit dialog
                        if (
                            old_val != new_val
                            and str(row_val).strip() == str(old_val).strip()
                        ):
                            row_dict[col] = new_val
                    new_row = [row_dict.get(col, "") for col in columns]
                    self._all_rows_with_sku[i] = (new_row, row_dict["Identifier"])
                self._all_rows = [row for (row, sku) in self._all_rows_with_sku]
                # 重新编号所有SKU下的Index字段，避免重复
                sku_to_rows = {}
                for row in self._all_rows:
                    sku = row[columns.index("Identifier")]
                    sku_to_rows.setdefault(sku, []).append(row)
                for sku, rows in sku_to_rows.items():
                    for idx, row in enumerate(rows, 1):
                        row[0] = str(idx)
                self._all_rows_with_sku = [
                    (row, row[columns.index("Identifier")]) for row in self._all_rows
                ]
                # 重新统计所有SKU并同步下拉框（保持原有顺序）
                new_sku_list = []
                seen = set()
                for row in self._all_rows:
                    sku = row[columns.index("Identifier")]
                    if sku not in seen:
                        new_sku_list.append(sku)
                        seen.add(sku)
                self._sku_list = new_sku_list
                self.sku_combobox["values"] = self._sku_list
                if self.sku_var.get() not in self._sku_list:
                    if self._sku_list:
                        self.sku_var.set(self._sku_list[0])
                    else:
                        self.sku_var.set("")
                self.filter_tests()
                self.root.update_idletasks()
            elif apply_to == "sku_by_field":
                columns = (
                    self._test_columns
                    if self._test_columns is not None
                    else [
                        "Index",
                        "Identifier",
                        "TestID",
                        "Description",
                        "Enabled",
                        "StringLimit",
                        "LowLimit",
                        "HighLimit",
                        "LimitType",
                        "Unit",
                        "Parameters",
                    ]
                )
                n = len(old_values)
                current_sku = self.sku_var.get() if hasattr(self, "sku_var") else None
                for i, (row, sku) in enumerate(self._all_rows_with_sku):
                    if sku != current_sku:
                        continue
                    row_dict = {col_: val for col_, val in zip(columns, row)}
                    changed = False
                    for j in range(n):
                        col = columns[j + 1]  # 跳过 Index
                        old_val = old_values[j]
                        new_val = new_values[j + 1]
                        if old_val == new_val:
                            continue
                        if str(row_dict.get(col, "")).strip() == str(old_val).strip():
                            row_dict[col] = new_val
                            changed = True
                    if changed:
                        new_row = [row_dict.get(col_, "") for col_ in columns]
                        self._all_rows_with_sku[i] = (new_row, current_sku)
                self._all_rows = [row for (row, sku) in self._all_rows_with_sku]
                # 重新编号当前SKU下的Index字段
                sku_to_rows = {}
                for row in self._all_rows:
                    sku = row[columns.index("Identifier")]
                    sku_to_rows.setdefault(sku, []).append(row)
                for sku, rows in sku_to_rows.items():
                    for idx, row in enumerate(rows, 1):
                        row[0] = str(idx)
                self._all_rows_with_sku = [
                    (row, row[columns.index("Identifier")]) for row in self._all_rows
                ]
                # 重新统计所有SKU并同步下拉框（保持原有顺序）
                new_sku_list = []
                seen = set()
                for row in self._all_rows:
                    sku = row[columns.index("Identifier")]
                    if sku not in seen:
                        new_sku_list.append(sku)
                        seen.add(sku)
                self._sku_list = new_sku_list
                self.sku_combobox["values"] = self._sku_list
                if self.sku_var.get() not in self._sku_list:
                    if self._sku_list:
                        self.sku_var.set(self._sku_list[0])
                    else:
                        self.sku_var.set("")
                self.filter_tests()
                self.root.update_idletasks()
            elif apply_to == "current":
                columns = (
                    self._test_columns
                    if self._test_columns is not None
                    else [
                        "Index",
                        "Identifier",
                        "TestID",
                        "Description",
                        "Enabled",
                        "StringLimit",
                        "LowLimit",
                        "HighLimit",
                        "LimitType",
                        "Unit",
                        "Parameters",
                    ]
                )
                # Build row_dict and row_for_storage
                row_dict = {field: val for field, val in zip(fields, new_values)}
                row_for_storage = [row_dict.get(col, "") for col in columns]
                # Update _all_rows (only the current row)
                for i, row in enumerate(self._all_rows):
                    if (
                        str(row[0]) == index
                        and row[columns.index("Identifier")] == current_sku
                    ):
                        self._all_rows[i] = list(row_for_storage)
                        break
                # Update _all_rows_with_sku (only the current row)
                for i, (row, sku) in enumerate(self._all_rows_with_sku):
                    if str(row[0]) == index and sku == current_sku:
                        self._all_rows_with_sku[i] = (list(row_for_storage), sku)
                        break
                # Update Treeview
                self.tree.item(item_id, values=row_for_storage)
                self.filter_tests()
                self.root.update_idletasks()
                return
            # 兜底：无论如何都刷新主界面
            self.filter_tests()
            self.root.update_idletasks()

        open_edit_dialog_with_apply_option(on_save, values=values[:])

    def add_test_item(self):
        """添加新测试项目到末尾"""

        def on_save(new_values):
            # 获取当前所有 index 的最大值
            if self._all_rows:
                max_index = max(int(row[0]) for row in self._all_rows)
                new_index = str(max_index + 1)
            else:
                new_index = "1"
            row = [str(new_index)] + [
                str(v) if v is not None else "" for v in new_values
            ]
            self._all_rows.append(row)
            self._all_rows_with_sku.append((row, self.sku_var.get()))  # 添加sku
            self.renumber_index()
            self.tree.delete(*self.tree.get_children())
            for r in self._all_rows:
                self.tree.insert("", "end", values=r)
            self.search_var.set("")  # 清空搜索，显示全部
            self.update_overlay()

        self.open_edit_dialog(on_save, values=[""] * 9)

    def insert_test_item(self, before=True):
        """在选中项前/后插入新测试项目"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a row before inserting!")
            return
        ref_item = selected[0]
        ref_values = self.tree.item(ref_item)["values"]
        ref_index_value = str(ref_values[0])  # Index 字段
        ref_index = None
        for i, row in enumerate(self._all_rows):
            if str(row[0]) == ref_index_value:
                ref_index = i
                break
        if ref_index is None:
            messagebox.showerror(
                "Error",
                "Failed to locate the selected item in the main data. The data may have been filtered or modified.",
            )
            return

        def on_save(new_values):
            current_sku = self.sku_var.get() if hasattr(self, "sku_var") else None
            # 重新获取当前选中项的 Index 字段
            selected = self.tree.selection()
            if not selected:
                messagebox.showerror("Error", "No row selected for insert.")
                return
            ref_item = selected[0]
            ref_values = self.tree.item(ref_item)["values"]
            ref_index_value = str(ref_values[0])
            # 在 _all_rows_with_sku 里查找最新的全局索引
            sku_indices = [
                i
                for i, (row, sku) in enumerate(self._all_rows_with_sku)
                if sku == current_sku
            ]
            ref_global_index = None
            for i in sku_indices:
                if str(self._all_rows_with_sku[i][0][0]) == ref_index_value:
                    ref_global_index = i
                    break
            if ref_global_index is None:
                messagebox.showerror(
                    "Error", "Failed to locate the selected item in the current SKU."
                )
                return
            sku_pos = sku_indices.index(ref_global_index)
            # 计算插入点
            if before:
                insert_at = sku_indices[sku_pos]
            else:
                # after: 如果选中项是SKU区间最后一个，插到末尾，否则插在选中项后
                if sku_pos == len(sku_indices) - 1:
                    insert_at = sku_indices[-1] + 1
                else:
                    insert_at = sku_indices[sku_pos + 1]
            if self._all_rows:
                max_index = max(int(row[0]) for row in self._all_rows)
                new_index = str(max_index + 1)
            else:
                new_index = "1"
            row = [str(new_index)] + [
                str(v) if v is not None else "" for v in new_values
            ]
            self._all_rows.insert(insert_at, row)
            self._all_rows_with_sku.insert(insert_at, (row, self.sku_var.get()))
            # 重新编号当前SKU下的index，并同步 self._all_rows
            sku_indices = [
                i
                for i, (row, sku) in enumerate(self._all_rows_with_sku)
                if sku == current_sku
            ]
            for new_idx, i in enumerate(sku_indices, 1):
                row, sku = self._all_rows_with_sku[i]
                self._all_rows_with_sku[i] = ([str(new_idx)] + list(row[1:]), sku)
            for i, row in enumerate(self._all_rows):
                for r, sku in self._all_rows_with_sku:
                    if sku == current_sku and str(r[0]) == str(row[0]):
                        self._all_rows[i] = r
                        break
            self.tree.delete(*self.tree.get_children())
            for r in self._all_rows:
                self.tree.insert("", "end", values=r)
            self.search_var.set("")
            self.update_overlay()

        self.open_edit_dialog(
            on_save,
            values=[""] * 9,
            title=(
                "Insert Test Item (Before)" if before else "Insert Test Item (After)"
            ),
        )

    def delete_selected_item(self):
        """删除选中的项目，支持多选并提示即将删除的index"""
        selected = self.tree.selection()
        if selected:
            indices = [self.tree.item(item, "values")[0] for item in selected]
            indices_str = ", ".join(indices)
            msg = f"Are you sure you want to delete the selected test item(s)?\nIndex: {indices_str}"
            if messagebox.askyesno("Confirm Delete", msg):
                selected_indices = set(indices)
                self._all_rows = [
                    row for row in self._all_rows if row[0] not in selected_indices
                ]
                self._all_rows_with_sku = [
                    item
                    for item in self._all_rows_with_sku
                    if item[0][0] not in selected_indices
                ]  # 更新sku列表
                # 重新编号当前SKU下的index
                current_sku = self.sku_var.get() if hasattr(self, "sku_var") else None
                # 找到当前SKU下的所有行
                sku_rows = [
                    (i, row, sku)
                    for i, (row, sku) in enumerate(self._all_rows_with_sku)
                    if sku == current_sku
                ]
                # 重新编号
                for new_idx, (i, row, sku) in enumerate(sku_rows, 1):
                    self._all_rows_with_sku[i] = ([str(new_idx)] + list(row[1:]), sku)
                # 同步 self._all_rows
                # 只更新当前SKU下的行
                for i, row in enumerate(self._all_rows):
                    for r, sku in self._all_rows_with_sku:
                        if sku == current_sku and str(r[0]) == str(row[0]):
                            self._all_rows[i] = r
                            break
                self.filter_tests()

    def renumber_index(self):
        """重新编号Index列，并同步所有数据结构和UI"""
        for idx, row in enumerate(self._all_rows, 1):
            new_row = [str(idx)] + list(row[1:])
            self._all_rows[idx - 1] = new_row
        # 同步 _all_rows_with_sku 的 index 字段
        for i, (row, sku) in enumerate(self._all_rows_with_sku):
            row[0] = self._all_rows[i][0]
        # 刷新 Treeview
        self.tree.delete(*self.tree.get_children())
        for row in self._all_rows:
            self.tree.insert("", "end", values=row)

    def open_edit_dialog(self, on_save, values=None, title="Edit Test Item"):
        """通用编辑/添加对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("600x500")
        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        ws = dialog.winfo_screenwidth()
        hs = dialog.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        dialog.transient(self.root)
        dialog.grab_set()
        fields = [
            "TestID",
            "Description",
            "Enabled",
            "StringLimit",
            "LowLimit",
            "HighLimit",
            "LimitType",
            "Unit",
            "Parameters",
        ]
        field_vars = {}
        if values is None:
            values = [""] * 9
        for i, field in enumerate(fields):
            ttk.Label(dialog, text=f"{field}:").grid(
                row=i, column=0, sticky=tk.W, padx=10, pady=5
            )
            var = tk.StringVar(value=values[i] if i < len(values) else "")
            field_vars[field] = var
            if field == "Parameters":
                text_widget = scrolledtext.ScrolledText(dialog, height=4, width=50)
                text_widget.grid(row=i, column=1, sticky="we", padx=10, pady=5)
                text_widget.insert("1.0", var.get())
                field_vars[field] = text_widget
            else:
                ttk.Entry(dialog, textvariable=var, width=50).grid(
                    row=i, column=1, sticky="we", padx=10, pady=5
                )
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)

        def save_changes():
            new_values = []
            for field in fields:
                if field == "Parameters":
                    new_values.append(field_vars[field].get("1.0", tk.END).strip())
                else:
                    new_values.append(field_vars[field].get())
            on_save(new_values)
            dialog.destroy()

        ttk.Button(button_frame, text="Save", command=save_changes).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )
        dialog.columnconfigure(1, weight=1)

    def show_context_menu(self, event):
        """显示右键菜单"""
        # 只有未选中任何行时才自动选中鼠标下的行
        if not self.tree.selection():
            row_id = self.tree.identify_row(event.y)
            if row_id:
                self.tree.selection_set(row_id)
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def update_export_date(self):
        """更新导出日期为当前时间"""
        now = datetime.now()
        current_time = f"{now.month}/{now.day}/{now.year} {now.strftime('%I:%M:%S %p')}"
        self.export_date_var.set(current_time)

    def browse_file(self):
        """浏览文件"""
        filename = filedialog.askopenfilename(
            title="Select INI File",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
        )
        if filename:
            self.ini_file = filename
            self.file_path_var.set(filename)
            self.load_ini_file()

    # def save_file(self):
    #     """保存文件"""
    #     try:
    #         # 读取原文件内容
    #         with open(self.ini_file, 'r', encoding='utf-8') as f:
    #             content = f.read()

    #         # 更新Info部分
    #         content = self.update_info_section(content)

    #         # 保存到文件
    #         with open(self.ini_file, 'w', encoding='utf-8') as f:
    #             f.write(content)

    #         messagebox.showinfo("成功", f"文件已保存: {self.ini_file}")
    #     except Exception as e:
    #         messagebox.showerror("错误", f"保存文件时出错: {str(e)}")

    def update_info_section(self, content):
        """导出时直接用UI变量重建[Info]区内容，保证导出和UI一致"""
        try:
            # 构造新的Info区内容
            info_lines = [
                f"UnitCount={self.unit_count_var.get()}",
                f"Export Date={self.export_date_var.get()}",
            ]
            new_info = "[Info]\n" + "\n".join(info_lines)
            # 用正则替换原有[Info]区
            content = re.sub(
                r"\[Info\]\s*\n(.*?)(?=\n\[|\Z)", new_info, content, flags=re.DOTALL
            )
            return content
        except Exception as e:
            print(f"Error updating Info section: {e}")
            return content

    def export(self):
        """导出"""
        if not os.path.exists(self.ini_file):
            messagebox.showerror("Error", f"File not found")
            return
        try:
            # 从原文件名中提取基础名称，清除中括号内文本，保留[和]
            base_name = re.sub(r'\[[^\]]*\]', '[]', os.path.basename(self.ini_file))
            backup_filename = base_name

            filename = filedialog.asksaveasfilename(
                title="Save File",
                defaultextension=".ini",
                initialfile=backup_filename,
                filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
            )

            if filename:
                # 读取原文件内容
                with open(self.ini_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # 更新Info部分
                content = self.update_info_section(content)

                # 只导出当前 self._sku_list 中的 SKU
                sku_to_rows = {}
                for row, sku in self._all_rows_with_sku:
                    if sku in self._sku_list:
                        sku_to_rows.setdefault(sku, []).append(row)

                # 1. 提取每个 section 的 header_line
                section_headers = {}
                for m in re.finditer(
                    r"\[([^\]]+)\]\s*\n(.*?)(?=\n\[|\Z)", content, flags=re.DOTALL
                ):
                    section_name = m.group(1)
                    section_content = m.group(2)
                    if section_name == "Info":
                        continue
                    header_match = re.search(
                        r"^\s*\(([^)]*)\)", section_content, re.MULTILINE
                    )
                    if header_match:
                        header_line = header_match.group(0).strip()
                    else:
                        header_line = "(Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters)"
                    section_headers[section_name] = header_line

                def format_row(row):
                    formatted = []
                    for i, v in enumerate(row):
                        if i == 3 and str(v) in ("0", "1"):
                            formatted.append(str(v))  # Enabled 字段不加引号
                        else:
                            formatted.append(f"'{v}'")
                    return f"({','.join(formatted)})"

                sections = []
                # 只导出 self._sku_list 中的 SKU
                for idx, sku in enumerate(self._sku_list):
                    rows = sku_to_rows.get(sku, [])
                    header_line = section_headers.get(
                        sku,
                        "Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters",
                    )
                    header_line_stripped = header_line.strip()
                    if header_line_stripped.startswith(
                        "("
                    ) and header_line_stripped.endswith(")"):
                        header_line_final = header_line_stripped[1:-1]
                    else:
                        header_line_final = header_line_stripped
                    if header_line_final:
                        header_fields = [
                            h.strip() for h in header_line_final.split(",")
                        ]
                    else:
                        header_fields = [
                            "Identifier",
                            "TestID",
                            "Description",
                            "Enabled",
                            "StringLimit",
                            "LowLimit",
                            "HighLimit",
                            "LimitType",
                            "Unit",
                            "Parameters",
                        ]
                    lines = [f"Count={len(rows)}"]
                    for i, row in enumerate(rows, 1):
                        # 按 header_fields 顺序组装 new_row
                        test_columns = (
                            self._test_columns
                            if isinstance(self._test_columns, list)
                            else [
                                "Index",
                                "Identifier",
                                "TestID",
                                "Description",
                                "Enabled",
                                "StringLimit",
                                "LowLimit",
                                "HighLimit",
                                "LimitType",
                                "Unit",
                                "Parameters",
                            ]
                        )
                        row_dict = {col: val for col, val in zip(test_columns, row)}
                        new_row = [row_dict.get(col, "") for col in header_fields]
                        lines.append(
                            f"{i}=({header_line_final}) VALUES {format_row(new_row)}"
                        )
                    if sections:
                        sections.append("")
                    sections.append(f"[{sku}]\n" + "\n".join(lines))

                # Info 区放最前面
                info_match = re.search(
                    r"\[Info\]\s*\n(.*?)(?=\n\[|\Z)", content, re.DOTALL
                )
                if info_match:
                    info_section = f"[Info]\n{info_match.group(1).strip()}\n"
                    sections = [info_section] + sections

                content = "\n".join(sections)

                # 保存备份
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)

                messagebox.showinfo("Success", f"The file is saved: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting: {str(e)}")

    def confirm_reload(self):
        if not os.path.exists(self.ini_file):
            messagebox.showerror("Error", f"File not found")
            return
        """在重新加载前提示用户会覆盖当前修改，需确认"""
        msg = "Reload will overwrite all unsaved changes. This action cannot be undone.\nAre you sure you want to proceed?"
        if messagebox.askyesno("Confirm Reload", msg, icon="warning"):
            self.load_ini_file()
        # 否则什么都不做

    def update_overlay(self):
        """根据表格是否有数据，显示或隐藏覆盖层提示"""
        if not self.tree.get_children():
            # 判断是否有 SKU 被选中
            sku_selected = (
                bool(self.sku_var.get()) if hasattr(self, "sku_var") else False
            )
            search_active = (
                bool(self.search_var.get()) if hasattr(self, "search_var") else False
            )
            if sku_selected and search_active:
                self.overlay_label.config(
                    text="No test item matches the current filter."
                )
            else:
                self.overlay_label.config(
                    text="Drag and drop an INI file here to edit\n(or click the Browse button above)"
                )
            self.overlay_label.lift()
            self.overlay_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.overlay_label.place_forget()

    def initialize_app(self):
        """恢复程序到最初始状态（清空所有数据和界面）"""
        msg = "This will clear all loaded data and reset the application to its initial state.\nAre you sure you want to proceed?"
        if not messagebox.askyesno("Confirm Initialize", msg, icon="warning"):
            return
        self.ini_file = ""
        self.file_path_var.set("")
        self.unit_count_var.set("")
        self.export_date_var.set("")
        self._all_rows = []
        self._all_rows_with_sku = []
        self._sku_list = []
        self.sku_combobox["values"] = []
        self.sku_var.set("")
        self.tree.delete(*self.tree.get_children())
        if hasattr(self, "search_var"):
            self.search_var.set("")
        if hasattr(self, "sku_suffix_var"):
            self.sku_suffix_var.set(DEFAULT_SKU_SUFFIX)
        self.update_overlay()

    def copy_selected_item(self):
        """复制选中行到剪贴板（导出格式），并在所有选中行的最后一条之后一并插入副本（顺序与原选中项一致）"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Copy", "Please select at least one row to copy.")
            return
        header = "(Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters)"
        current_sku = self.sku_var.get() if hasattr(self, "sku_var") else ""
        # 构建 index 到 row 的映射（当前 SKU）
        index_to_row = {
            str(row[0]): row
            for (row, sku) in self._all_rows_with_sku
            if sku == current_sku
        }
        ui_order = list(self.tree.get_children())
        selected_ui_pos = [(ui_order.index(item), item) for item in selected]
        selected_ui_pos.sort()

        def format_row_export(row):
            formatted = []
            for i, v in enumerate(row):
                if i == 3 and str(v) in ("0", "1"):
                    formatted.append(str(v))
                else:
                    formatted.append(f"'{v}'")
            return f"({','.join(formatted)})"

        rows = []
        for idx, (ui_pos, item) in enumerate(selected_ui_pos, 1):
            values = self.tree.item(item)["values"]
            index = str(values[0])
            row = index_to_row.get(index, list(values))
            export_row = [current_sku] + list(row[2:])  # row[2:] 跳过 Index, Identifier
            export_row.insert(0, row[1])  # Identifier
            line = f"{row[0]}={header} VALUES {format_row_export(export_row)}"
            rows.append(line)
        text = "\n".join(rows)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        # 插入副本
        sku_rows = [
            (i, row, sku)
            for i, (row, sku) in enumerate(self._all_rows_with_sku)
            if sku == current_sku
        ]
        ui_items = list(self.tree.get_children())
        selected_ui_pos = [(ui_items.index(item), item) for item in selected]
        selected_ui_pos.sort()
        if not selected_ui_pos:
            return
        max_ui_pos = max(pos for pos, _ in selected_ui_pos)
        insert_at = max_ui_pos + 1
        if insert_at > len(sku_rows):
            insert_at = len(sku_rows)
        global_insert_at = (
            sku_rows[insert_at - 1][0] + 1
            if insert_at > 0 and insert_at <= len(sku_rows)
            else (sku_rows[-1][0] + 1 if sku_rows else len(self._all_rows_with_sku))
        )
        new_rows = []
        for _, item in selected_ui_pos:
            values = self.tree.item(item)["values"]
            index = str(values[0])
            row = index_to_row.get(index, list(values))
            new_row = ["TMP_INDEX"] + list(row[1:])
            new_rows.append(new_row)
        for offset, new_row in enumerate(new_rows):
            self._all_rows_with_sku.insert(
                global_insert_at + offset, (new_row, current_sku)
            )
            self._all_rows.insert(global_insert_at + offset, new_row)
        self.renumber_index_for_current_sku()
        self.filter_tests()

    def copy_to_all_skus(self):
        """将选中行分别插入到所有其他 SKU 的相同 index 位置（如超出则插入末尾），并自动编号"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(
                "Copy To Other SKUs", "Please select at least one row to copy."
            )
            return
        current_sku = self.sku_var.get() if hasattr(self, "sku_var") else ""
        all_skus = list(self.sku_combobox["values"])
        other_skus = [sku for sku in all_skus if sku != current_sku]
        if not other_skus:
            messagebox.showinfo("Copy To Other SKUs", "No other SKUs to copy to.")
            return
        # 构建 index 到 row 的映射（当前 SKU）
        index_to_row = {
            str(row[0]): row
            for (row, sku) in self._all_rows_with_sku
            if sku == current_sku
        }
        selected_rows = []
        for item in selected:
            values = self.tree.item(item)["values"]
            index = str(values[0])
            row = index_to_row.get(index, list(values))
            selected_rows.append((int(index), row))
        selected_rows.sort()
        for sku in other_skus:
            sku_indices = [
                i for i, (row, s) in enumerate(self._all_rows_with_sku) if s == sku
            ]
            sku_rows = [self._all_rows_with_sku[i][0] for i in sku_indices]
            for sel_idx, row in selected_rows:
                insert_pos = sel_idx - 1
                if insert_pos > len(sku_rows):
                    insert_pos = len(sku_rows)
                global_insert_at = (
                    sku_indices[insert_pos]
                    if insert_pos < len(sku_indices)
                    else (
                        sku_indices[-1] + 1
                        if sku_indices
                        else len(self._all_rows_with_sku)
                    )
                )
                new_row = ["TMP_INDEX"] + list(row[1:])
                columns = getattr(self, "_test_columns", None)
                if columns and "Identifier" in columns:
                    idx = columns.index("Identifier")
                    new_row[idx] = sku
                else:
                    new_row[1] = sku
                self._all_rows_with_sku.insert(global_insert_at, (list(new_row), sku))
                self._all_rows.insert(global_insert_at, list(new_row))
                sku_indices = [
                    i for i, (row, s) in enumerate(self._all_rows_with_sku) if s == sku
                ]
                sku_rows = [self._all_rows_with_sku[i][0] for i in sku_indices]
        for sku in other_skus:
            idx = 1
            for i, (row, s) in enumerate(self._all_rows_with_sku):
                if s == sku:
                    row[0] = str(idx)
                    idx += 1
        self._all_rows = [row for (row, sku) in self._all_rows_with_sku]
        self.filter_tests()
        messagebox.showinfo("Copy To Other SKUs", "Copy To Other SKUs completed!")

    def renumber_index_for_current_sku(self):
        current_sku = self.sku_var.get() if hasattr(self, "sku_var") else ""
        idx = 1
        for i, (row, sku) in enumerate(self._all_rows_with_sku):
            if sku == current_sku:
                row[0] = str(idx)
                idx += 1
        self._all_rows = [row for (row, sku) in self._all_rows_with_sku]
        self.filter_tests()

    def _on_tree_drag_start(self, event):
        # 记录拖动起始项
        item = self.tree.identify_row(event.y)
        if not item:
            self._dragging_item = None
            return
        self._dragging_item = item
        self._dragging_index = self.tree.index(item)
        self._last_target_item = None

    def _on_tree_drag_motion(self, event):
        # 仅选中目标行，不再高亮目标行
        if not hasattr(self, "_dragging_item") or not self._dragging_item:
            return
        target_item = self.tree.identify_row(event.y)
        if target_item:
            self.tree.selection_set(target_item)

    def _on_tree_drag_release(self, event):
        if not hasattr(self, "_dragging_item") or not self._dragging_item:
            if hasattr(self, "_dragging_item") and self._dragging_item:
                self.tree.item(self._dragging_item, tags=())
            return
        target_item = self.tree.identify_row(event.y)
        if not target_item or target_item == self._dragging_item:
            self._dragging_item = None
            if hasattr(self, "_dragging_item") and self._dragging_item:
                self.tree.item(self._dragging_item, tags=())
            return
        # 只允许当前SKU下拖动
        current_sku = self.sku_var.get() if hasattr(self, "sku_var") else ""
        # 获取当前UI顺序的所有行
        ui_items = list(self.tree.get_children())
        from_idx = ui_items.index(self._dragging_item)
        to_idx = ui_items.index(target_item)
        # 取出当前SKU下的所有行在 _all_rows_with_sku 的索引
        sku_indices = [
            i
            for i, (row, sku) in enumerate(self._all_rows_with_sku)
            if sku == current_sku
        ]
        # 只允许拖动当前SKU下的行
        if from_idx >= len(sku_indices) or to_idx >= len(sku_indices):
            self._dragging_item = None
            if hasattr(self, "_dragging_item") and self._dragging_item:
                self.tree.item(self._dragging_item, tags=())
            return
        real_from = sku_indices[from_idx]
        real_to = sku_indices[to_idx]
        # 移动数据
        row = self._all_rows_with_sku.pop(real_from)
        self._all_rows_with_sku.insert(real_to, row)
        # 同步 _all_rows
        self._all_rows = [r for (r, s) in self._all_rows_with_sku]
        self.renumber_index_for_current_sku()
        # 修正：同步 _all_rows_with_sku 的 index 字段
        for i, (row, sku) in enumerate(self._all_rows_with_sku):
            row[0] = self._all_rows[i][0]
        self.filter_tests()
        self._dragging_item = None
        if hasattr(self, "_dragging_item") and self._dragging_item:
            self.tree.item(self._dragging_item, tags=())


def main():
    root = TkinterDnD.Tk()
    # 设置样式
    style = ttk.Style()
    style.theme_use("clam")
    # 创建应用
    WanchaiEditor(root)
    # 主窗口靠上一点
    root.update_idletasks()
    w = root.winfo_width()
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws // 2) - (w // 2)
    y = int(hs * 0.01)  # 距离顶部1%
    root.geometry(f"+{x}+{y}")
    # 运行应用
    root.mainloop()


if __name__ == "__main__":
    main()
