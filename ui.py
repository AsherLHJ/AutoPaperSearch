import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import config_loader as config
from lib import utils, ReadPaper, Data
from lib.paper_processor import process_papers
from lib.load_api_keys import load_api_keys_from_files, print_loaded_keys
import threading
import sys
import os
import language

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.processing_thread = None
        self.is_running = False  # 标记程序是否正在运行
        
        # 加载语言设置
        self.lang = language.get_text(config.LANGUAGE)
        
        self.title(self.lang["app_title"])
        self.geometry("1000x650")
        self.minsize(800, 600)  # 设置最小窗口大小

        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        # Main layout
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建选项卡控件
        self.tab_control = ttk.Notebook(main_frame)
        
        # 创建主设置选项卡
        self.main_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.main_tab, text=self.lang["main_tab"])
        
        # 创建文件夹设置选项卡
        self.folder_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.folder_tab, text=self.lang["folder_tab"])
        
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 在主设置选项卡中创建控件
        controls_frame = ttk.LabelFrame(self.main_tab, text=self.lang["config_label"], padding="10")
        controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        log_frame = ttk.LabelFrame(self.main_tab, text=self.lang["log_label"], padding="10")
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 在文件夹设置选项卡中创建控件
        self.setup_folder_tab()

        # --- Controls --- 
        self.setup_controls(controls_frame)

        # --- Log view ---
        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', wrap=tk.WORD, bg="#f0f0f0")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # --- Status Bar ---
        self.status_bar = ttk.Label(self, text=self.lang["loading"], relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Redirect print_and_log to the UI
        utils.print_and_log = self.log_message

        # Initial load
        self.preload_info()

    def setup_folder_tab(self):
        """设置文件夹路径选项卡"""
        frame = ttk.Frame(self.folder_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 语言选择
        lang_frame = ttk.Frame(frame)
        lang_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(lang_frame, text=self.lang["language_label"]).pack(side=tk.LEFT, padx=(0, 10))
        
        self.language_var = tk.StringVar(value=config.LANGUAGE)
        language_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, state="readonly")
        language_combo['values'] = ('zh_CN', 'en_US')
        language_combo.pack(side=tk.LEFT)
        language_combo.bind('<<ComboboxSelected>>', self.change_language)
        
        # Data文件夹路径
        data_frame = ttk.Frame(frame)
        data_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(data_frame, text=self.lang["data_folder_label"]).pack(side=tk.LEFT, padx=(0, 10))
        
        self.data_folder_var = tk.StringVar(value=config.DATA_FOLDER)
        data_entry = ttk.Entry(data_frame, textvariable=self.data_folder_var, width=50)
        data_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        data_browse_btn = ttk.Button(data_frame, text=self.lang["browse_button"], 
                                    command=lambda: self.browse_folder(self.data_folder_var, "Data"))
        data_browse_btn.pack(side=tk.LEFT)
        
        # APIKey文件夹路径
        apikey_frame = ttk.Frame(frame)
        apikey_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(apikey_frame, text=self.lang["apikey_folder_label"]).pack(side=tk.LEFT, padx=(0, 10))
        
        self.apikey_folder_var = tk.StringVar(value=config.APIKEY_FOLDER)
        apikey_entry = ttk.Entry(apikey_frame, textvariable=self.apikey_folder_var, width=50)
        apikey_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        apikey_browse_btn = ttk.Button(apikey_frame, text=self.lang["browse_button"], 
                                      command=lambda: self.browse_folder(self.apikey_folder_var, "APIKey"))
        apikey_browse_btn.pack(side=tk.LEFT)
        
        # Result文件夹路径
        result_frame = ttk.Frame(frame)
        result_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(result_frame, text=self.lang["result_folder_label"]).pack(side=tk.LEFT, padx=(0, 10))
        
        self.result_folder_var = tk.StringVar(value=config.RESULT_FOLDER)
        result_entry = ttk.Entry(result_frame, textvariable=self.result_folder_var, width=50)
        result_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        result_browse_btn = ttk.Button(result_frame, text=self.lang["browse_button"], 
                                      command=lambda: self.browse_folder(self.result_folder_var, "Result"))
        result_browse_btn.pack(side=tk.LEFT)
        
        # 应用按钮
        apply_frame = ttk.Frame(frame)
        apply_frame.pack(fill=tk.X, pady=(15, 0))
        
        apply_button = ttk.Button(apply_frame, text="应用更改", command=self.apply_folder_changes)
        apply_button.pack(side=tk.RIGHT)
    
    def browse_folder(self, path_var, folder_type):
        """打开文件夹浏览器选择路径"""
        folder_path = filedialog.askdirectory(initialdir=path_var.get())
        if folder_path:
            path_var.set(folder_path)
    
    def apply_folder_changes(self):
        """应用文件夹路径更改"""
        if self.is_running:
            messagebox.showwarning("警告", "程序正在运行中，无法更改路径设置！")
            return
            
        # 更新config中的路径
        config.DATA_FOLDER = self.data_folder_var.get()
        config.APIKEY_FOLDER = self.apikey_folder_var.get()
        config.RESULT_FOLDER = self.result_folder_var.get()
        config.LANGUAGE = self.language_var.get()
        
        # 保存配置到JSON文件
        config.save_config()
        
        # 确保文件夹存在
        for folder_path, folder_name in [
            (config.DATA_FOLDER, "Data"),
            (config.APIKEY_FOLDER, "APIKey"),
            (config.RESULT_FOLDER, "Result")
        ]:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                self.log_message(f"已创建{folder_name}文件夹: {folder_path}")
        
        # 重新加载信息
        self.preload_info()
        messagebox.showinfo("成功", "文件夹路径设置已更新！")
    
    def change_language(self, event=None):
        """切换界面语言"""
        config.LANGUAGE = self.language_var.get()
        # 保存配置到JSON文件
        config.save_config()
        messagebox.showinfo("提示", "语言设置已更改，重启程序后生效")
    
    def setup_controls(self, parent):
        # 顶部控件框架
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Checkboxes with status
        checkbox_frame = ttk.LabelFrame(top_frame, text="选项设置")
        checkbox_frame.pack(fill=tk.X, pady=5)
        
        self.save_full_log_var = tk.BooleanVar(value=config.save_full_log)
        self.save_full_log_cb = ttk.Checkbutton(checkbox_frame, variable=self.save_full_log_var)
        self.save_full_log_cb.pack(anchor='w', pady=5)

        self.include_req_var = tk.BooleanVar(value=config.include_requirements_in_prompt)
        self.include_req_cb = ttk.Checkbutton(checkbox_frame, variable=self.include_req_var)
        self.include_req_cb.pack(anchor='w', pady=5)

        self.include_keywords_var = tk.BooleanVar(value=config.include_keywords_in_prompt)
        self.include_keywords_cb = ttk.Checkbutton(checkbox_frame, variable=self.include_keywords_var)
        self.include_keywords_cb.pack(anchor='w', pady=5)

        self.save_full_log_var.trace_add('write', self.update_checkbox_text)
        self.include_req_var.trace_add('write', self.update_checkbox_text)
        self.include_keywords_var.trace_add('write', self.update_checkbox_text)
        self.update_checkbox_text() # Initial text setup

        # Research Question (Multiline)
        ttk.Label(parent, text=self.lang["research_question_label"]).pack(anchor='w', pady=(10, 0))
        self.research_question_text = scrolledtext.ScrolledText(parent, height=5, width=40)
        self.research_question_text.insert(tk.END, config.ResearchQuestion)
        self.research_question_text.pack(anchor='w', fill='x')

        # Requirements
        ttk.Label(parent, text=self.lang["requirements_label"]).pack(anchor='w', pady=(10, 0))
        self.requirements_text = scrolledtext.ScrolledText(parent, height=8, width=40)
        self.requirements_text.insert(tk.END, config.Requirements)
        self.requirements_text.pack(anchor='w', fill='x')

        # Keywords
        ttk.Label(parent, text=self.lang["keywords_label"]).pack(anchor='w', pady=(10, 0))
        self.keywords_text = scrolledtext.ScrolledText(parent, height=5, width=40)
        self.keywords_text.insert(tk.END, config.Keywords)
        self.keywords_text.pack(anchor='w', fill='x')

        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=20, fill='x')

        self.start_button = ttk.Button(button_frame, text=self.lang["start_button"], command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, expand=True, fill='x', padx=(0, 5))

        self.stop_button = ttk.Button(button_frame, text=self.lang["stop_button"], command=self.stop_processing, state='disabled')
        self.stop_button.pack(side=tk.LEFT, expand=True, fill='x', padx=(5, 0))

    def update_checkbox_text(self, *args):
        enabled_text = self.lang["enabled"]
        disabled_text = self.lang["disabled"]
        self.save_full_log_cb.config(text=f"{self.lang['save_full_log']} ({enabled_text if self.save_full_log_var.get() else disabled_text})")
        self.include_req_cb.config(text=f"{self.lang['include_req']} ({enabled_text if self.include_req_var.get() else disabled_text})")
        self.include_keywords_cb.config(text=f"{self.lang['include_keywords']} ({enabled_text if self.include_keywords_var.get() else disabled_text})")

    def preload_info(self):
        self.log_message(self.lang["preloading"])
        load_api_keys_from_files()
        api_key_count = len(config.API_KEYS)
        
        # Clear previous paper data before reading
        Data.paper_data.clear()
        ReadPaper.read_bib_files()
        paper_count = len(Data.paper_data)
        
        status_text = f"{self.lang['api_key_count']} {api_key_count} | {self.lang['paper_count']} {paper_count}"
        self.status_bar.config(text=status_text)
        self.log_message(f"{self.lang['preload_complete']} {status_text}")

    def log_message(self, message="", thread_id=None):
        if thread_id is not None:
            message = f"[Thread-{thread_id}] {message}"
        
        def append_message():
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, message + '\n')
            self.log_text.config(state='disabled')
            self.log_text.see(tk.END)
        
        self.after(0, append_message)

    def start_processing(self):
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
        
        # 设置Data模块中的停止事件，通知处理线程停止
        Data.progress_stop_event.set()
        
        # 等待处理线程结束
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
        
        # 重置UI状态
        self.reset_ui_state()
        
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
        
        # 锁定文件夹设置选项卡
        self.tab_control.tab(1, state=state)

    def run_paper_processing(self):
        try:
            # API keys are already loaded during preload
            if not config.API_KEYS:
                self.log_message(self.lang["no_api_keys"])
                self.log_message(self.lang["add_api_keys"])
                return

            # Papers are already loaded during preload
            if not Data.paper_data:
                self.log_message(self.lang["no_papers"])
                self.log_message(self.lang["check_data_folder"])
                return

            process_papers(config.ResearchQuestion, config.Keywords, config.Requirements, -1)
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

if __name__ == "__main__":
    app = App()
    app.mainloop()