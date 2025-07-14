import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, font
from ..config import config_loader as config
from ..log import utils
from ..process import data
from ..load_data import load_paper
from ..process.paper_processor import process_papers
from ..load_data.load_api_keys import load_api_keys_from_files, print_loaded_keys
from ..tools.txt_to_bib_converter import TxtToBibConverter
import threading
import sys
import os
import re
from PIL import Image, ImageTk
import colorsys

# Correct the path to import the language module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from language import language

# 作者: 李弘基(hli546@connect.hkust-gz.edu.cn)，栗梓明(zli578@connect.hkust-gz.edu.cn)
# 创建日期: 2025
# 版本: 1.1

# 自定义主题和样式类
class AppTheme:
    def __init__(self, is_dark_mode=False):
        # 主题颜色（只保留亮色主题）
        self.is_dark_mode = False
        
        # 亮色主题
        self.light = {
            'bg': '#f5f5f7',              # 背景色
            'fg': '#333333',              # 前景色/文本色
            'accent': '#0066cc',          # 强调色
            'accent_light': '#4a9ced',    # 浅强调色
            'success': '#28a745',         # 成功色
            'warning': '#ffc107',         # 警告色
            'error': '#dc3545',           # 错误色
            'frame_bg': '#ffffff',        # 框架背景
            'input_bg': '#ffffff',        # 输入框背景
            'button_bg': '#0066cc',       # 按钮背景
            'button_fg': '#ffffff',       # 按钮文本
            'button_active': '#004c99',   # 按钮激活
            'border': '#dddddd',          # 边框色
            'selection': '#e6f2ff',       # 选中背景
            'disabled': '#cccccc',        # 禁用色
            'log_bg': '#f8f9fa',          # 日志背景
            'tab_active': '#ffffff',      # 活动选项卡
            'tab_inactive': '#f0f0f0',    # 非活动选项卡
            'scrollbar': '#cccccc',       # 滚动条
        }
        
        # 当前主题（始终为亮色主题）
        self.current = self.light
    
    def get_color(self, name):
        """获取当前主题的指定颜色"""
        return self.light.get(name, self.light['bg'])
    
    def get_gradient_colors(self, start_color, end_color, steps):
        """生成渐变色列表"""
        # 将十六进制颜色转换为RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # 将RGB转换为HSV
        def rgb_to_hsv(rgb):
            r, g, b = [x/255.0 for x in rgb]
            return colorsys.rgb_to_hsv(r, g, b)
        
        # 将HSV转换为RGB
        def hsv_to_rgb(hsv):
            r, g, b = colorsys.hsv_to_rgb(*hsv)
            return tuple(int(x*255) for x in (r, g, b))
        
        # 将RGB转换为十六进制
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)
        
        # 转换起始和结束颜色
        start_rgb = hex_to_rgb(start_color)
        end_rgb = hex_to_rgb(end_color)
        
        start_hsv = rgb_to_hsv(start_rgb)
        end_hsv = rgb_to_hsv(end_rgb)
        
        # 生成渐变色
        gradient = []
        for i in range(steps):
            # 计算当前步骤的HSV值
            h = start_hsv[0] + (end_hsv[0] - start_hsv[0]) * i / (steps-1)
            s = start_hsv[1] + (end_hsv[1] - start_hsv[1]) * i / (steps-1)
            v = start_hsv[2] + (end_hsv[2] - start_hsv[2]) * i / (steps-1)
            
            # 转换回RGB和十六进制
            rgb = hsv_to_rgb((h, s, v))
            hex_color = rgb_to_hex(rgb)
            gradient.append(hex_color)
        
        return gradient

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.processing_thread = None
        self.is_running = False  # 标记程序是否正在运行
        
        # 文件夹论文计数缓存
        self.folder_paper_cache = {}  # 缓存每个文件夹的论文数据
        self.cache_valid = False  # 缓存是否有效
        
        # 加载语言设置
        self.lang = language.get_text(config.LANGUAGE)
        
        # 初始化主题（固定使用亮色主题）
        self.theme = AppTheme(is_dark_mode=False)
        
        # 设置窗口标题和大小
        self.title(self.lang["app_title"])
        self.geometry("1200x900")
        self.minsize(1200, 850)  # 设置最小窗口大小
        
        # 设置窗口图标
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'icon', 'icon.ico')
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass  # 图标加载失败时不做处理
        
        # 配置自定义字体
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Arial", size=10)
        
        self.heading_font = font.Font(family="Arial", size=12, weight="bold")
        self.large_font = font.Font(family="Arial", size=11)
        self.small_font = font.Font(family="Arial", size=9)
        
        # 配置ttk样式
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        # 应用主题颜色
        self.apply_theme()
        
        # 创建菜单栏
        self.create_menu()
        
        # 检查配置文件中的文件夹路径
        self.first_time_user = False
        if (config.DATA_FOLDER == "default" or 
            config.APIKEY_FOLDER == "default" or 
            config.RESULT_FOLDER == "default" or 
            config.LOG_FOLDER == "default"):
            self.first_time_user = True

        # 设置背景色
        self.configure(bg=self.theme.get_color('bg'))
        
        # Main layout with padding
        main_frame = ttk.Frame(self, padding="15", style="Main.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建选项卡控件
        self.tab_control = ttk.Notebook(main_frame, style="App.TNotebook")
        
        # 创建主设置选项卡
        self.main_tab = ttk.Frame(self.tab_control, style="Tab.TFrame")
        self.tab_control.add(self.main_tab, text=self.lang["main_tab"])
        
        # 创建数据选择选项卡
        self.data_selection_tab = ttk.Frame(self.tab_control, style="Tab.TFrame")
        self.tab_control.add(self.data_selection_tab, text=self.lang.get("data_selection_tab", "选择数据"))

        # 创建文件夹设置选项卡
        self.folder_tab = ttk.Frame(self.tab_control, style="Tab.TFrame")
        self.tab_control.add(self.folder_tab, text=self.lang["folder_tab"])
        
        # 创建语言设置选项卡
        self.language_tab = ttk.Frame(self.tab_control, style="Tab.TFrame")
        self.tab_control.add(self.language_tab, text=self.lang["language_tab"])
        
        # 创建工具选项卡
        self.tools_tab = ttk.Frame(self.tab_control, style="Tab.TFrame")
        self.tab_control.add(self.tools_tab, text=self.lang.get("tools_tab", "工具"))
        
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 在主设置选项卡中创建控件
        controls_frame = ttk.LabelFrame(self.main_tab, text=self.lang["config_label"], padding="15", style="Config.TLabelframe")
        controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=15)

        log_frame = ttk.LabelFrame(self.main_tab, text=self.lang["log_label"], padding="15", style="Log.TLabelframe")
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=15, pady=15)

        # 在文件夹设置选项卡中创建控件
        self.setup_folder_tab()
        
        # 在语言设置选项卡中创建控件
        self.setup_language_tab()
        
        # 在工具选项卡中创建控件
        self.setup_tools_tab()

        # --- Controls --- 
        self.setup_controls(controls_frame)
        
        # 在数据选择选项卡中创建控件
        self.setup_data_selection_tab()





        # --- Log view ---
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            state='disabled', 
            wrap=tk.WORD, 
            bg=self.theme.get_color('log_bg'),
            fg=self.theme.get_color('fg'),
            insertbackground=self.theme.get_color('accent'),
            selectbackground=self.theme.get_color('selection'),
            selectforeground=self.theme.get_color('fg'),
            font=self.default_font,
            relief=tk.FLAT,
            borderwidth=1
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Status Bar ---
        self.status_bar = ttk.Label(
            self, 
            text=self.lang["loading"], 
            relief=tk.FLAT, 
            anchor=tk.W, 
            padding=5,
            style="Status.TLabel"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        # Redirect print_and_log to the UI
        utils.print_and_log = self.log_message

        # Initial load
        self.preload_info()

    def apply_theme(self):
        """应用主题样式到UI组件"""
        # 配置ttk样式
        # 主框架样式
        self.style.configure(
            "Main.TFrame", 
            background=self.theme.get_color('bg')
        )
        
        # 选项卡样式
        self.style.configure(
            "Tab.TFrame", 
            background=self.theme.get_color('bg')
        )
        
        # 标签框架样式
        self.style.configure(
            "TLabelframe", 
            background=self.theme.get_color('bg'),
            foreground=self.theme.get_color('fg')
        )
        self.style.configure(
            "TLabelframe.Label", 
            background=self.theme.get_color('bg'),
            foreground=self.theme.get_color('fg'),
            font=self.heading_font
        )
        
        # 配置框架样式
        self.style.configure(
            "Config.TLabelframe", 
            background=self.theme.get_color('bg'),
            foreground=self.theme.get_color('fg')
        )
        self.style.configure(
            "Config.TLabelframe.Label", 
            background=self.theme.get_color('bg'),
            foreground=self.theme.get_color('accent'),
            font=self.heading_font
        )
        
        # 日志框架样式
        self.style.configure(
            "Log.TLabelframe", 
            background=self.theme.get_color('bg'),
            foreground=self.theme.get_color('fg')
        )
        self.style.configure(
            "Log.TLabelframe.Label", 
            background=self.theme.get_color('bg'),
            foreground=self.theme.get_color('accent'),
            font=self.heading_font
        )
        
        # 标签样式
        self.style.configure(
            "TLabel", 
            background=self.theme.get_color('bg'),
            foreground=self.theme.get_color('fg'),
            font=self.default_font
        )
        
        # 状态栏样式
        self.style.configure(
            "Status.TLabel", 
            background=self.theme.get_color('bg'),
            foreground=self.theme.get_color('fg'),
            font=self.small_font
        )
        
        # 按钮样式
        self.style.configure(
            "TButton", 
            background=self.theme.get_color('button_bg'),
            foreground=self.theme.get_color('button_fg'),
            font=self.default_font
        )
        self.style.map(
            "TButton",
            background=[('active', self.theme.get_color('button_active'))],
            foreground=[('active', self.theme.get_color('button_fg'))]
        )
        
        # 开始按钮样式
        self.style.configure(
            "Start.TButton", 
            background=self.theme.get_color('success'),
            foreground=self.theme.get_color('button_fg'),
            font=self.large_font
        )
        self.style.map(
            "Start.TButton",
            background=[('active', self.theme.get_color('button_active'))],
            foreground=[('active', self.theme.get_color('button_fg'))]
        )
        
        # 停止按钮样式
        self.style.configure(
            "Stop.TButton", 
            background=self.theme.get_color('error'),
            foreground=self.theme.get_color('button_fg'),
            font=self.large_font
        )
        self.style.map(
            "Stop.TButton",
            background=[('active', self.theme.get_color('button_active'))],
            foreground=[('active', self.theme.get_color('button_fg'))]
        )
        
        # 复选框样式
        self.style.configure(
            "TCheckbutton", 
            background=self.theme.get_color('bg'),
            foreground=self.theme.get_color('fg'),
            font=self.default_font
        )
        
        # 输入框样式
        self.style.configure(
            "TEntry", 
            fieldbackground=self.theme.get_color('input_bg'),
            foreground=self.theme.get_color('fg'),
            insertcolor=self.theme.get_color('accent'),
            font=self.default_font
        )
        
        # 下拉框样式
        self.style.configure(
            "TCombobox", 
            fieldbackground=self.theme.get_color('input_bg'),
            foreground=self.theme.get_color('fg'),
            font=self.default_font
        )
        
        # 选项卡样式
        self.style.configure(
            "App.TNotebook", 
            background=self.theme.get_color('bg'),
            tabmargins=[2, 5, 2, 0]
        )
        self.style.configure(
            "App.TNotebook.Tab", 
            background=self.theme.get_color('tab_inactive'),
            foreground=self.theme.get_color('fg'),
            padding=[10, 5],
            font=self.default_font
        )
        self.style.map(
            "App.TNotebook.Tab",
            background=[('selected', self.theme.get_color('tab_active'))],
            foreground=[('selected', self.theme.get_color('fg'))],
            expand=[('selected', [1, 1, 1, 0])]
        )
        
        # 更新主窗口背景色
        self.configure(bg=self.theme.get_color('bg'))
        
    # 移除主题设置相关方法
        
    def setup_folder_tab(self):
        """设置文件夹路径选项卡"""
        frame = ttk.Frame(self.folder_tab, padding="15", style="Tab.TFrame")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Data文件夹路径
        data_frame = ttk.Frame(frame, style="Tab.TFrame")
        data_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(data_frame, text=self.lang["data_folder_label"], style="TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        self.data_folder_var = tk.StringVar(value=config.DATA_FOLDER)
        data_entry = ttk.Entry(data_frame, textvariable=self.data_folder_var, width=50, style="TEntry")
        data_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        data_browse_btn = ttk.Button(data_frame, text=self.lang["browse_button"], 
                                    command=lambda: self.browse_folder(self.data_folder_var, "Data"),
                                    style="TButton")
        data_browse_btn.pack(side=tk.LEFT)
        
        # APIKey文件夹路径
        apikey_frame = ttk.Frame(frame, style="Tab.TFrame")
        apikey_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(apikey_frame, text=self.lang["apikey_folder_label"], style="TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        self.apikey_folder_var = tk.StringVar(value=config.APIKEY_FOLDER)
        apikey_entry = ttk.Entry(apikey_frame, textvariable=self.apikey_folder_var, width=50, style="TEntry")
        apikey_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        apikey_browse_btn = ttk.Button(apikey_frame, text=self.lang["browse_button"], 
                                      command=lambda: self.browse_folder(self.apikey_folder_var, "APIKey"),
                                      style="TButton")
        apikey_browse_btn.pack(side=tk.LEFT)
        
        # Result文件夹路径
        result_frame = ttk.Frame(frame, style="Tab.TFrame")
        result_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(result_frame, text=self.lang["result_folder_label"], style="TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        self.result_folder_var = tk.StringVar(value=config.RESULT_FOLDER)
        result_entry = ttk.Entry(result_frame, textvariable=self.result_folder_var, width=50, style="TEntry")
        result_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        result_browse_btn = ttk.Button(result_frame, text=self.lang["browse_button"], 
                                      command=lambda: self.browse_folder(self.result_folder_var, "Result"),
                                      style="TButton")
        result_browse_btn.pack(side=tk.LEFT)
        
        # Log文件夹路径
        log_frame = ttk.Frame(frame, style="Tab.TFrame")
        log_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(log_frame, text=self.lang["log_folder_label"], style="TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        self.log_folder_var = tk.StringVar(value=config.LOG_FOLDER)
        log_entry = ttk.Entry(log_frame, textvariable=self.log_folder_var, width=50, style="TEntry")
        log_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        log_browse_btn = ttk.Button(log_frame, text=self.lang["browse_button"], 
                                   command=lambda: self.browse_folder(self.log_folder_var, "Log"),
                                   style="TButton")
        log_browse_btn.pack(side=tk.LEFT)
        

    
    def browse_folder(self, path_var, folder_type):
        """打开文件夹浏览器选择路径并自动保存更改"""
        folder_path = filedialog.askdirectory(initialdir=path_var.get())
        if folder_path:
            path_var.set(folder_path)
            # 如果程序正在运行，则不应用更改
            if self.is_running:
                messagebox.showwarning(self.lang.get("warning_title", "警告"), self.lang.get("running_warning", "程序正在运行中，无法更改路径设置！"))
                return
                
            # 更新config中的路径
            config.DATA_FOLDER = self.data_folder_var.get()
            config.APIKEY_FOLDER = self.apikey_folder_var.get()
            config.RESULT_FOLDER = self.result_folder_var.get()
            config.LOG_FOLDER = self.log_folder_var.get()
            
            # 保存配置到JSON文件
            config.save_config()
            
            # 确保文件夹存在
            folder_name = ""
            if path_var == self.data_folder_var:
                folder_name = "Data"
            elif path_var == self.apikey_folder_var:
                folder_name = "APIKey"
            elif path_var == self.result_folder_var:
                folder_name = "Result"
            elif path_var == self.log_folder_var:
                folder_name = "Log"
            
            folder_path = path_var.get()
            if folder_name and not os.path.exists(folder_path):
                os.makedirs(folder_path)
                self.log_message(f"已创建{folder_name}文件夹: {folder_path}")
            
            # 重新加载信息
            self.preload_info()
    

    
    def change_language(self, event=None):
        """切换界面语言"""
        if self.is_running:
            messagebox.showwarning(self.lang["warning_title"], self.lang["running_warning"])
            # 恢复原来的语言设置
            self.language_var.set(config.LANGUAGE)
            return
            
        config.LANGUAGE = self.language_var.get()
        # 保存配置到JSON文件
        config.save_config()
        messagebox.showinfo(self.lang.get("info_title", "提示"), self.lang.get("language_changed", "语言设置已更改，重启程序后生效"))
    
    def setup_controls(self, parent):
        # 顶部控件框架
        top_frame = ttk.Frame(parent, style="Tab.TFrame")
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Checkboxes with status
        checkbox_frame = ttk.LabelFrame(top_frame, text=self.lang.get("options_settings", "选项设置"), style="Config.TLabelframe")
        checkbox_frame.pack(fill=tk.X, pady=5)
        
        self.save_full_log_var = tk.BooleanVar(value=config.save_full_log)
        self.save_full_log_cb = ttk.Checkbutton(checkbox_frame, variable=self.save_full_log_var, style="TCheckbutton")
        self.save_full_log_cb.pack(anchor='w', pady=5)

        self.include_req_var = tk.BooleanVar(value=config.include_requirements_in_prompt)
        self.include_req_cb = ttk.Checkbutton(checkbox_frame, variable=self.include_req_var, style="TCheckbutton")
        self.include_req_cb.pack(anchor='w', pady=5)

        self.include_keywords_var = tk.BooleanVar(value=config.include_keywords_in_prompt)
        self.include_keywords_cb = ttk.Checkbutton(checkbox_frame, variable=self.include_keywords_var, style="TCheckbutton")
        self.include_keywords_cb.pack(anchor='w', pady=5)

        self.save_full_log_var.trace_add('write', self.update_checkbox_text)
        self.include_req_var.trace_add('write', self.update_checkbox_text)
        self.include_keywords_var.trace_add('write', self.update_checkbox_text)
        self.update_checkbox_text() # Initial text setup

        # Research Question (Multiline)
        ttk.Label(parent, text=self.lang["research_question_label"], style="TLabel").pack(anchor='w', pady=(10, 0))
        self.research_question_text = scrolledtext.ScrolledText(
            parent, 
            height=5, 
            width=40,
            bg=self.theme.get_color('input_bg'),
            fg=self.theme.get_color('fg'),
            insertbackground=self.theme.get_color('accent'),
            selectbackground=self.theme.get_color('selection'),
            selectforeground=self.theme.get_color('fg'),
            font=self.default_font
        )
        self.research_question_text.insert(tk.END, config.ResearchQuestion)
        self.research_question_text.pack(anchor='w', fill='x')

        # Requirements
        ttk.Label(parent, text=self.lang["requirements_label"], style="TLabel").pack(anchor='w', pady=(10, 0))
        self.requirements_text = scrolledtext.ScrolledText(
            parent, 
            height=8, 
            width=40,
            bg=self.theme.get_color('input_bg'),
            fg=self.theme.get_color('fg'),
            insertbackground=self.theme.get_color('accent'),
            selectbackground=self.theme.get_color('selection'),
            selectforeground=self.theme.get_color('fg'),
            font=self.default_font
        )
        self.requirements_text.insert(tk.END, config.Requirements)
        self.requirements_text.pack(anchor='w', fill='x')

        # Keywords
        ttk.Label(parent, text=self.lang["keywords_label"], style="TLabel").pack(anchor='w', pady=(10, 0))
        self.keywords_text = scrolledtext.ScrolledText(
            parent, 
            height=5, 
            width=40,
            bg=self.theme.get_color('input_bg'),
            fg=self.theme.get_color('fg'),
            insertbackground=self.theme.get_color('accent'),
            selectbackground=self.theme.get_color('selection'),
            selectforeground=self.theme.get_color('fg'),
            font=self.default_font
        )
        self.keywords_text.insert(tk.END, config.Keywords)
        self.keywords_text.pack(anchor='w', fill='x')

        # 主要操作按钮区域
        main_button_frame = ttk.Frame(parent, style="Tab.TFrame")
        main_button_frame.pack(pady=(20, 10), fill='x')

        self.start_button = ttk.Button(main_button_frame, text=self.lang["start_button"], command=self.start_processing, style="Start.TButton")
        self.start_button.pack(side=tk.LEFT, expand=True, fill='x', padx=(0, 5))

        self.stop_button = ttk.Button(main_button_frame, text=self.lang["stop_button"], command=self.stop_processing, state='disabled', style="Stop.TButton")
        self.stop_button.pack(side=tk.LEFT, expand=True, fill='x', padx=(5, 0))
        
        # 辅助功能按钮区域
        utility_button_frame = ttk.Frame(parent, style="Tab.TFrame")
        utility_button_frame.pack(pady=(5, 0), fill='x')
        
        self.clear_log_button = ttk.Button(utility_button_frame, text=self.lang.get("clear_log_button", "清空日志"), command=self.clear_log, style="TButton")
        self.clear_log_button.pack(side=tk.LEFT, expand=True, fill='x', padx=(0, 5))
        
        self.help_button = ttk.Button(utility_button_frame, text=self.lang["help_button"], command=self.show_help, style="TButton")
        self.help_button.pack(side=tk.LEFT, expand=True, fill='x', padx=(5, 0))

    def update_checkbox_text(self, *args):
        enabled_text = self.lang["enabled"]
        disabled_text = self.lang["disabled"]
        self.save_full_log_cb.config(text=f"{self.lang['save_full_log']} ({enabled_text if self.save_full_log_var.get() else disabled_text})")
        self.include_req_cb.config(text=f"{self.lang['include_req']} ({enabled_text if self.include_req_var.get() else disabled_text})")
        self.include_keywords_cb.config(text=f"{self.lang['include_keywords']} ({enabled_text if self.include_keywords_var.get() else disabled_text})")

    def preload_info(self):
        self.log_message(self.lang["preloading"])
        load_api_keys_from_files()
        
        # Clear previous paper data before reading
        data.paper_data.clear()
        # 标记缓存无效，强制重建
        self.cache_valid = False
        # 加载并显示文件夹列表
        # update_folder_checkboxes 会触发 on_folder_selection_change, 
        # on_folder_selection_change 会触发 update_paper_count,
        # update_paper_count 会加载数据并更新UI
        self.update_folder_checkboxes(force_rebuild_cache=True)
        
        # 记录日志
        api_key_count = len(config.API_KEYS)
        paper_count = len(data.paper_data)
        status_text = f"\n{'='*50}\n{self.lang['api_key_count']} {api_key_count}\n{self.lang['paper_count']} {paper_count}\n{'='*50}"
        self.log_message(f"{self.lang['preload_complete']}\n{status_text}")
        
        # 如果是首次使用（文件夹路径为default），自动打开帮助窗口
        if self.first_time_user:
            self.after(1000, self.show_help)

    def log_message(self, message="", thread_id=None):
        if thread_id is not None:
            message = f"[Thread-{thread_id}] {message}"
        
        def append_message():
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, message + '\n')
            self.log_text.config(state='disabled')
            self.log_text.see(tk.END)
        
        self.after(0, append_message)
    
    def clear_log(self):
        """清空日志内容"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        self.log_message(self.lang.get("log_cleared", "日志已清空"))

    def start_processing(self):
        # 检查文件夹路径是否已设置
        if (config.DATA_FOLDER == "default" or 
            config.APIKEY_FOLDER == "default" or 
            config.RESULT_FOLDER == "default" or 
            config.LOG_FOLDER == "default"):
            messagebox.showwarning(
                self.lang["warning_title"] if "warning_title" in self.lang else "警告", 
                self.lang["folder_not_set_message"] if "folder_not_set_message" in self.lang else 
                "请先在文件夹设置选项卡中设置所有文件夹路径，然后再开始处理。"
            )
            return
        
        # 设置运行状态标志
        self.is_running = True
        
        # 禁用开始按钮，启用停止按钮
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # 清空日志
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

        # 锁定配置控件
        self.lock_config_widgets(True)

        # 更新config中的配置
        config.save_full_log = self.save_full_log_var.get()
        config.include_requirements_in_prompt = self.include_req_var.get()
        config.include_keywords_in_prompt = self.include_keywords_var.get()
        config.ResearchQuestion = self.research_question_text.get("1.0", tk.END).strip()
        config.Requirements = self.requirements_text.get("1.0", tk.END).strip()
        config.Keywords = self.keywords_text.get("1.0", tk.END).strip()
        
        # 保存配置到JSON文件
        config.save_config()

        # 在单独的线程中运行处理
        self.processing_thread = threading.Thread(target=self.run_paper_processing)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        # 记录开始处理的日志
        self.log_message(self.lang["processing_start"])

    def stop_processing(self):
        self.log_message(self.lang["processing_stop"])
        
        # 设置data模块中的停止事件，通知处理线程停止
        data.progress_stop_event.set()
        
        # 等待处理线程结束
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
        
        # 重置UI状态
        self.reset_ui_state()
        
    def setup_data_selection_tab(self):
        """设置数据选择选项卡"""
        # --- 年份范围设置 ---
        year_range_frame = ttk.LabelFrame(self.data_selection_tab, text=self.lang.get("year_range_label", "年份范围设置"), padding="15", style="Config.TLabelframe")
        year_range_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        # 包含所有年份的复选框
        self.include_all_years_var = tk.BooleanVar(value=config.INCLUDE_ALL_YEARS)
        self.include_all_years_cb = ttk.Checkbutton(
            year_range_frame, 
            text=self.lang.get("include_all_years", "包含所有年份（包括不带年份的文件）"), 
            variable=self.include_all_years_var, 
            command=self.on_year_range_change,
            style="TCheckbutton"
        )
        self.include_all_years_cb.pack(anchor='w', pady=(0, 10))
        
        # 年份范围设置框架
        year_input_frame = ttk.Frame(year_range_frame, style="Tab.TFrame")
        year_input_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 起始年份
        ttk.Label(year_input_frame, text=self.lang.get("start_year", "起始年份:"), style="TLabel").pack(side=tk.LEFT, padx=(0, 5))
        self.start_year_var = tk.StringVar(value=str(config.YEAR_RANGE_START))
        self.start_year_entry = ttk.Entry(year_input_frame, textvariable=self.start_year_var, width=8, style="TEntry")
        self.start_year_entry.pack(side=tk.LEFT, padx=(0, 15))
        self.start_year_entry.bind('<KeyRelease>', self.on_year_range_change)
        
        # 结束年份
        ttk.Label(year_input_frame, text=self.lang.get("end_year", "结束年份:"), style="TLabel").pack(side=tk.LEFT, padx=(0, 5))
        self.end_year_var = tk.StringVar(value=str(config.YEAR_RANGE_END))
        self.end_year_entry = ttk.Entry(year_input_frame, textvariable=self.end_year_var, width=8, style="TEntry")
        self.end_year_entry.pack(side=tk.LEFT, padx=(0, 15))
        self.end_year_entry.bind('<KeyRelease>', self.on_year_range_change)
        
        # 年份范围提示
        self.year_range_info_label = ttk.Label(
            year_range_frame, 
            text=self.get_year_range_info_text(), 
            font=self.small_font, 
            style="TLabel",
            foreground=self.theme.get_color('accent')
        )
        self.year_range_info_label.pack(anchor='w', pady=(5, 0))
        
        # --- 文件夹选择 ---
        folder_selection_frame = ttk.LabelFrame(self.data_selection_tab, text=self.lang.get("folder_selection_label", "选择数据文件夹"), padding="15", style="Config.TLabelframe")
        folder_selection_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))

        self.select_all_var = tk.BooleanVar(value=True)
        self.select_all_cb = ttk.Checkbutton(folder_selection_frame, text=self.lang.get("select_all", "全选"), 
                                               variable=self.select_all_var, command=self.toggle_all_folders,
                                               style="TCheckbutton")
        self.select_all_cb.pack(anchor='w', pady=(5, 10))

        # 创建一个带滚动条的Canvas
        canvas = tk.Canvas(folder_selection_frame, bg=self.theme.get_color('bg'), highlightthickness=0)
        scrollbar = ttk.Scrollbar(folder_selection_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style="Tab.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.folder_vars = {}

        # 增加一个标签显示选择信息
        self.selection_info_label = ttk.Label(folder_selection_frame, text="", 
                                             font=self.default_font, 
                                             style="TLabel",
                                             foreground=self.theme.get_color('accent'))
        self.selection_info_label.pack(anchor='w', pady=(10, 5))

    def lock_config_widgets(self, lock=True):
        """锁定或解锁配置控件"""
        state = 'disabled' if lock else 'normal'
        
        # 锁定复选框
        self.save_full_log_cb.config(state=state)
        self.include_req_cb.config(state=state)
        self.include_keywords_cb.config(state=state)
        
        # 锁定文本框
        self.research_question_text.config(state=state)
        self.requirements_text.config(state=state)
        self.keywords_text.config(state=state)
        
        # 锁定数据选择和文件夹设置选项卡
        self.tab_control.tab(1, state=state)
        self.tab_control.tab(2, state=state)

    def build_folder_cache(self):
        """构建文件夹论文缓存"""
        self.folder_paper_cache.clear()
        data_folder = config.DATA_FOLDER
        
        if os.path.exists(data_folder) and os.path.isdir(data_folder):
            subfolders = load_paper.get_subfolders()
            
            for folder in subfolders:
                folder_path = os.path.join(data_folder, folder)
                folder_data = {
                    'all_bib_files': [],
                    'file_papers': {}  # 每个文件的论文数量
                }
                
                if os.path.exists(folder_path):
                    all_bib_files = [f for f in os.listdir(folder_path) if f.endswith('.bib')]
                    folder_data['all_bib_files'] = all_bib_files
                    
                    # 缓存每个文件的论文数量
                    for bib_file in all_bib_files:
                        try:
                            with open(os.path.join(folder_path, bib_file), 'r', encoding='utf-8') as file:
                                content = file.read()
                                # 使用正则表达式匹配每个论文条目
                                paper_entries = re.findall(r'@\w+\{[^@]*?\}(?=\s*(?:@|$))', content, re.DOTALL)
                                folder_data['file_papers'][bib_file] = len(paper_entries)
                        except Exception:
                            folder_data['file_papers'][bib_file] = 0
                
                self.folder_paper_cache[folder] = folder_data
        
        self.cache_valid = True
    
    def get_folder_paper_count(self, folder):
        """获取文件夹的论文数量（考虑年份筛选）"""
        if not self.cache_valid or folder not in self.folder_paper_cache:
            return 0, 0, 0  # paper_count, bib_file_count, filtered_bib_file_count
        
        folder_data = self.folder_paper_cache[folder]
        all_bib_files = folder_data['all_bib_files']
        bib_file_count = len(all_bib_files)
        
        paper_count = 0
        filtered_bib_file_count = 0
        
        for bib_file in all_bib_files:
            # 检查文件是否在年份范围内
            if load_paper.is_file_in_year_range(bib_file):
                filtered_bib_file_count += 1
                paper_count += folder_data['file_papers'].get(bib_file, 0)
        
        return paper_count, bib_file_count, filtered_bib_file_count
    
    def update_folder_info_display(self):
        """只更新文件夹信息显示，不重建UI"""
        if not hasattr(self, 'folder_checkboxes') or not self.folder_checkboxes:
            return
        
        # 遍历现有的文件夹复选框，更新信息显示
        for folder, checkbox in self.folder_checkboxes.items():
            # 获取复选框所在的框架
            folder_item_frame = checkbox.master
            
            # 查找并更新论文信息标签
            for widget in folder_item_frame.winfo_children():
                if isinstance(widget, ttk.Label) and widget != checkbox:
                    # 使用缓存获取论文数量信息
                    paper_count, bib_file_count, filtered_bib_file_count = self.get_folder_paper_count(folder)
                    
                    # 根据语言设置显示不同的文本（显示筛选后的数量）
                    if config.LANGUAGE == 'zh_CN':
                        if config.INCLUDE_ALL_YEARS or filtered_bib_file_count == bib_file_count:
                            info_text = f"({bib_file_count} 个.bib文件, {paper_count} 篇论文)"
                        else:
                            info_text = f"({filtered_bib_file_count}/{bib_file_count} 个.bib文件, {paper_count} 篇论文)"
                    else:
                        if config.INCLUDE_ALL_YEARS or filtered_bib_file_count == bib_file_count:
                            info_text = f"({bib_file_count} .bib files, {paper_count} papers)"
                        else:
                            info_text = f"({filtered_bib_file_count}/{bib_file_count} .bib files, {paper_count} papers)"
                    
                    widget.config(text=info_text)
                    break
    
    def update_folder_checkboxes(self, force_rebuild_cache=False):
        """更新文件夹复选框列表"""
        # 如果缓存无效或强制重建，则重建缓存
        if not self.cache_valid or force_rebuild_cache:
            self.build_folder_cache()
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.folder_vars.clear()
        self.folder_checkboxes = {}
        
        # 获取Data文件夹中的子文件夹
        data_folder = config.DATA_FOLDER
        if os.path.exists(data_folder) and os.path.isdir(data_folder):
            subfolders = load_paper.get_subfolders()
            
            for folder in subfolders:
                var = tk.BooleanVar(value=True)  # 默认选中
                self.folder_vars[folder] = var
                
                # 创建一个框架来包含复选框和文件夹信息
                folder_item_frame = ttk.Frame(self.scrollable_frame, style="Tab.TFrame")
                folder_item_frame.pack(fill=tk.X, pady=2)
                
                # 添加复选框
                checkbox = ttk.Checkbutton(
                    folder_item_frame,
                    text=folder,
                    variable=var,
                    command=self.on_folder_selection_change,
                    style="TCheckbutton"
                )
                checkbox.pack(side=tk.LEFT, padx=5)
                self.folder_checkboxes[folder] = checkbox
                
                # 使用缓存获取论文数量信息
                paper_count, bib_file_count, filtered_bib_file_count = self.get_folder_paper_count(folder)
                
                # 根据语言设置显示不同的文本（显示筛选后的数量）
                if config.LANGUAGE == 'zh_CN':
                    if config.INCLUDE_ALL_YEARS or filtered_bib_file_count == bib_file_count:
                        info_text = f"({bib_file_count} 个.bib文件, {paper_count} 篇论文)"
                    else:
                        info_text = f"({filtered_bib_file_count}/{bib_file_count} 个.bib文件, {paper_count} 篇论文)"
                else:
                    if config.INCLUDE_ALL_YEARS or filtered_bib_file_count == bib_file_count:
                        info_text = f"({bib_file_count} .bib files, {paper_count} papers)"
                    else:
                        info_text = f"({filtered_bib_file_count}/{bib_file_count} .bib files, {paper_count} papers)"
                
                paper_info = ttk.Label(
                    folder_item_frame,
                    text=info_text,
                    foreground=self.theme.get_color('accent'),
                    font=self.small_font,
                    style="TLabel"
                )
                paper_info.pack(side=tk.LEFT, padx=5)
        else:
            # 如果Data文件夹不存在，显示提示
            no_data_frame = ttk.Frame(self.scrollable_frame, style="Tab.TFrame")
            no_data_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(
                no_data_frame,
                text=self.lang.get("no_data_folder", "Data文件夹不存在或未设置"),
                foreground=self.theme.get_color('error'),
                font=self.default_font,
                style="TLabel"
            ).pack(padx=5)
        
        self.on_folder_selection_change() # 初始加载

    def toggle_all_folders(self):
        """全选/全不选所有文件夹"""
        is_selected = self.select_all_var.get()
        for var in self.folder_vars.values():
            var.set(is_selected)
        self.on_folder_selection_change()

    def on_folder_selection_change(self, event=None):
        """当文件夹选择变化时，更新论文计数"""
        # 更新全选复选框的状态
        all_selected = all(var.get() for var in self.folder_vars.values())
        self.select_all_var.set(all_selected)
        self.update_paper_count()

    def update_paper_count(self):
        """根据当前选择的文件夹更新论文计数"""
        selected_folders = [folder for folder, var in self.folder_vars.items() if var.get()]
        
        # 清空旧数据并重新加载
        data.paper_data.clear()
        if selected_folders:
            load_paper.read_bib_files(selected_folders)
        
        # 更新UI
        paper_count = len(data.paper_data)
        utils.print_and_log(f"{self.lang['update_paper_count'].format(count=paper_count)}")
        api_key_count = len(config.API_KEYS)
        selected_folder_count = len(selected_folders)
        
        # 计算选中文件夹中的.bib文件总数
        bib_file_count = 0
        data_folder = config.DATA_FOLDER
        for folder in selected_folders:
            folder_path = os.path.join(data_folder, folder)
            if os.path.exists(folder_path):
                bib_file_count += len([f for f in os.listdir(folder_path) if f.endswith('.bib')])
        
        # 使用语言文件中的文本
        selection_info_text = self.lang.get("selection_info", "已选择 {count} 个文件夹, {bib_files} 个.bib文件, 共 {papers} 篇论文").format(
            count=selected_folder_count, 
            bib_files=bib_file_count, 
            papers=paper_count
        )
            
        self.selection_info_label.config(text=selection_info_text)

        # 更新状态栏，显示API密钥数量、.bib文件数量和论文数量
        status_text = f"{self.lang['api_key_count']} {api_key_count} | {self.lang['bib_file_count']} {bib_file_count} | {self.lang['paper_count']} {paper_count}"
        self.status_bar.config(text=status_text)

    def on_year_range_change(self, event=None):
        """当年份范围设置变化时的处理函数"""
        if self.is_running:
            return
            
        try:
            # 更新配置
            config.INCLUDE_ALL_YEARS = self.include_all_years_var.get()
            
            # 验证年份输入
            start_year_str = self.start_year_var.get().strip()
            end_year_str = self.end_year_var.get().strip()
            
            if start_year_str and end_year_str:
                start_year = int(start_year_str)
                end_year = int(end_year_str)
                
                if start_year > end_year:
                    # 如果起始年份大于结束年份，交换它们
                    start_year, end_year = end_year, start_year
                    self.start_year_var.set(str(start_year))
                    self.end_year_var.set(str(end_year))
                
                config.YEAR_RANGE_START = start_year
                config.YEAR_RANGE_END = end_year
            
            # 保存配置
            config.save_config()
            
            # 更新年份范围信息显示
            self.year_range_info_label.config(text=self.get_year_range_info_text())
            
            # 优化：只更新文件夹信息显示，不重新构建整个UI
            self.update_folder_info_display()
            
            # 重新更新论文计数
            self.update_paper_count()
            
        except ValueError:
            # 如果年份输入无效，不做处理
            pass
    
    def get_year_range_info_text(self):
        """获取年份范围信息文本"""
        if config.INCLUDE_ALL_YEARS:
            return self.lang.get("year_range_all", "当前设置：包含所有年份的文件")
        else:
            return self.lang.get("year_range_specific", "当前设置：仅包含 {start} - {end} 年份的文件").format(
                start=config.YEAR_RANGE_START, 
                end=config.YEAR_RANGE_END
            )

    def run_paper_processing(self):
        try:
            # API keys are already loaded during preload
            if not config.API_KEYS:
                self.log_message(self.lang["no_api_keys"])
                self.log_message(self.lang["add_api_keys"])
                return

            # 论文数据已根据复选框实时加载，这里只需检查是否为空
            if not data.paper_data:
                self.log_message(self.lang["no_papers"])
                self.log_message(self.lang["check_data_folder"])
                return

            # 获取选中的文件夹列表
            selected_folders = [folder for folder, var in self.folder_vars.items() if var.get()]
            
            # 获取年份范围信息
            year_range_info = self.get_year_range_info_text()

            process_papers(config.ResearchQuestion, config.Keywords, config.Requirements, -1, selected_folders, year_range_info)
            self.log_message(self.lang["processing_complete"])
        except Exception as e:
            self.log_message(f"{self.lang['error_occurred']} {e}")
        finally:
            self.after(0, self.reset_ui_state)

    def reset_ui_state(self):
        # 重置运行状态标志
        self.is_running = False
        
        # 启用开始按钮，禁用停止按钮
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        
        # 解锁配置控件
        self.lock_config_widgets(False)
    
    def create_menu(self):
        """创建菜单栏"""
        menu_bar = tk.Menu(self)
        
        # 创建帮助菜单
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label=self.lang["help_title"], command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label=self.lang["menu_about"], command=self.show_about)
        
        # 将帮助菜单添加到菜单栏
        menu_bar.add_cascade(label=self.lang["menu_help"], menu=help_menu)
        
        # 设置菜单栏
        self.config(menu=menu_bar)
    
    def show_help(self):
        """显示帮助对话框"""
        help_window = tk.Toplevel(self)
        help_window.title(self.lang["help_title"])
        help_window.geometry("800x600")
        help_window.minsize(600, 400)
        help_window.configure(bg=self.theme.get_color('bg'))
        
        # 设置图标
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'icon', 'icon.ico')
            if os.path.exists(icon_path):
                help_window.iconbitmap(icon_path)
        except Exception:
            pass
        
        # 创建主框架
        main_frame = ttk.Frame(help_window, style="Main.TFrame", padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标题标签
        title_label = ttk.Label(
            main_frame,
            text=self.lang["help_title"],
            font=self.heading_font,
            style="TLabel"
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # 创建滚动文本框显示帮助内容
        help_text = scrolledtext.ScrolledText(
            main_frame, 
            wrap=tk.WORD,
            font=self.default_font,
            bg=self.theme.get_color('log_bg'),
            fg=self.theme.get_color('fg'),
            insertbackground=self.theme.get_color('accent'),
            selectbackground=self.theme.get_color('selection'),
            selectforeground=self.theme.get_color('fg'),
            relief=tk.FLAT,
            borderwidth=1
        )
        help_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置tag
        help_text.tag_configure('bold', font=('Arial', 10, 'bold'))
        
        # 插入帮助内容
        content = self.lang["help_content"]
        parts = content.split('**')
        for i, part in enumerate(parts):
            if i % 2 == 1:
                help_text.insert(tk.END, part, 'bold')
            else:
                help_text.insert(tk.END, part)
        
        help_text.config(state='disabled')  # 设置为只读
        
        # 关闭按钮
        button_frame = ttk.Frame(main_frame, style="Tab.TFrame")
        button_frame.pack(pady=15, anchor=tk.CENTER)
        
        close_button = ttk.Button(
            button_frame, 
            text=self.lang.get("close_button", "关闭" if config.LANGUAGE == 'zh_CN' else "Close"), 
            command=help_window.destroy,
            style="TButton"
        )
        close_button.pack()
    
    def show_about(self):
        """显示关于对话框"""
        about_window = tk.Toplevel(self)
        about_window.title(self.lang["about_title"])
        about_window.geometry("500x400")
        about_window.minsize(400, 300)
        about_window.configure(bg=self.theme.get_color('bg'))
        about_window.resizable(True, True)
        
        # 设置图标
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'icon', 'icon.ico')
            if os.path.exists(icon_path):
                about_window.iconbitmap(icon_path)
        except Exception:
            pass
        
        # 创建主框架
        main_frame = ttk.Frame(about_window, style="Main.TFrame", padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标题标签
        title_label = ttk.Label(
            main_frame,
            text=self.lang["about_title"],
            font=self.heading_font,
            style="TLabel"
        )
        title_label.pack(anchor=tk.CENTER, pady=(0, 15))
        
        # 创建关于内容
        about_text = scrolledtext.ScrolledText(
            main_frame, 
            wrap=tk.WORD,
            height=10,
            font=self.default_font,
            bg=self.theme.get_color('log_bg'),
            fg=self.theme.get_color('fg'),
            insertbackground=self.theme.get_color('accent'),
            selectbackground=self.theme.get_color('selection'),
            selectforeground=self.theme.get_color('fg'),
            relief=tk.FLAT,
            borderwidth=1
        )
        about_text.pack(fill=tk.BOTH, expand=True)
        about_text.insert(tk.END, self.lang["about_text"])
        about_text.config(state='disabled')  # 设置为只读
        
        # 关闭按钮
        button_frame = ttk.Frame(main_frame, style="Tab.TFrame")
        button_frame.pack(pady=15, anchor=tk.CENTER)
        
        close_button = ttk.Button(
            button_frame, 
            text=self.lang.get("close_button", "关闭" if config.LANGUAGE == 'zh_CN' else "Close"), 
            command=about_window.destroy,
            style="TButton"
        )
        close_button.pack()
    
    def setup_language_tab(self):
        """设置语言选择选项卡"""
        frame = ttk.Frame(self.language_tab, padding="15", style="Tab.TFrame")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 语言选择
        lang_frame = ttk.Frame(frame, style="Tab.TFrame")
        lang_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(lang_frame, text=self.lang["language_label"], style="TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        self.language_var = tk.StringVar(value=config.LANGUAGE)
        language_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, state="readonly", style="TCombobox")
        language_combo['values'] = ('zh_CN', 'en_US')
        language_combo.pack(side=tk.LEFT)
        language_combo.bind('<<ComboboxSelected>>', self.change_language)
    
    def setup_tools_tab(self):
        """设置工具选项卡"""
        frame = ttk.Frame(self.tools_tab, padding="15", style="Tab.TFrame")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # TXT到BibTeX转换工具
        converter_frame = ttk.LabelFrame(frame, text="知网TXT文献格式转换工具", padding="15", style="Config.TLabelframe")
        converter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 源文件夹选择
        source_frame = ttk.Frame(converter_frame, style="Tab.TFrame")
        source_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(source_frame, text="源文件夹:", style="TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        self.txt_source_var = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.txt_source_var, width=40, style="TEntry")
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        source_browse_btn = ttk.Button(source_frame, text="浏览", 
                                      command=self.browse_txt_source_folder,
                                      style="TButton")
        source_browse_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 目标文件夹选择
        target_frame = ttk.Frame(converter_frame, style="Tab.TFrame")
        target_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(target_frame, text="目标文件夹:", style="TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        self.txt_target_var = tk.StringVar()
        target_entry = ttk.Entry(target_frame, textvariable=self.txt_target_var, width=40, style="TEntry")
        target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        target_browse_btn = ttk.Button(target_frame, text="浏览", 
                                      command=self.browse_txt_target_folder,
                                      style="TButton")
        target_browse_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 转换按钮
        convert_btn = ttk.Button(target_frame, text="开始转换", 
                                command=self.start_txt_conversion,
                                style="Start.TButton")
        convert_btn.pack(side=tk.RIGHT)
    
    def browse_txt_source_folder(self):
        """浏览源文件夹"""
        folder_path = filedialog.askdirectory(title="选择包含TXT文件的源文件夹")
        if folder_path:
            self.txt_source_var.set(folder_path)
    
    def browse_txt_target_folder(self):
        """浏览目标文件夹"""
        folder_path = filedialog.askdirectory(title="选择转换后BibTeX文件的保存文件夹")
        if folder_path:
            self.txt_target_var.set(folder_path)
    
    def start_txt_conversion(self):
        """开始TXT到BibTeX转换"""
        source_dir = self.txt_source_var.get().strip()
        target_dir = self.txt_target_var.get().strip()
        
        if not source_dir:
            messagebox.showerror("错误", "请选择源文件夹")
            return
        
        if not target_dir:
            messagebox.showerror("错误", "请选择目标文件夹")
            return
        
        if not os.path.exists(source_dir):
            messagebox.showerror("错误", "源文件夹不存在")
            return
        
        try:
            converter = TxtToBibConverter()
            self.log_message(f"开始转换: {source_dir} -> {target_dir}")
            converter.convert_directory(source_dir, target_dir)
            messagebox.showinfo("完成", "TXT文件转换完成！")
        except Exception as e:
            error_msg = f"转换过程中出现错误: {str(e)}"
            self.log_message(error_msg)
            messagebox.showerror("错误", error_msg)

if __name__ == "__main__":
    app = App()
    app.mainloop()