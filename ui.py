import tkinter as tk
from tkinter import ttk, scrolledtext
import config
from lib import utils, ReadPaper, Data
from lib.paper_processor import process_papers
from lib.load_api_keys import load_api_keys_from_files
import threading
import sys

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SearchPaper - 学术论文相关性筛选工具")
        self.geometry("1000x650")
        self.processing_thread = None

        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        # Main layout
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        controls_frame = ttk.LabelFrame(main_frame, text="配置", padding="10")
        controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Controls --- 
        self.setup_controls(controls_frame)

        # --- Log view ---
        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', wrap=tk.WORD, bg="#f0f0f0")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # --- Status Bar ---
        self.status_bar = ttk.Label(self, text="正在加载...", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Redirect print_and_log to the UI
        utils.print_and_log = self.log_message

        # Initial load
        self.preload_info()

    def setup_controls(self, parent):
        # Checkboxes with status
        self.save_full_log_var = tk.BooleanVar(value=config.save_full_log)
        self.save_full_log_cb = ttk.Checkbutton(parent, variable=self.save_full_log_var)
        self.save_full_log_cb.pack(anchor='w', pady=5)

        self.include_req_var = tk.BooleanVar(value=config.include_requirements_in_prompt)
        self.include_req_cb = ttk.Checkbutton(parent, variable=self.include_req_var)
        self.include_req_cb.pack(anchor='w', pady=5)

        self.include_keywords_var = tk.BooleanVar(value=config.include_keywords_in_prompt)
        self.include_keywords_cb = ttk.Checkbutton(parent, variable=self.include_keywords_var)
        self.include_keywords_cb.pack(anchor='w', pady=5)

        self.save_full_log_var.trace_add('write', self.update_checkbox_text)
        self.include_req_var.trace_add('write', self.update_checkbox_text)
        self.include_keywords_var.trace_add('write', self.update_checkbox_text)
        self.update_checkbox_text() # Initial text setup

        # Research Question (Multiline)
        ttk.Label(parent, text="研究问题:").pack(anchor='w', pady=(10, 0))
        self.research_question_text = scrolledtext.ScrolledText(parent, height=5, width=40)
        self.research_question_text.insert(tk.END, config.ResearchQuestion)
        self.research_question_text.pack(anchor='w', fill='x')

        # Requirements
        ttk.Label(parent, text="要求:").pack(anchor='w', pady=(10, 0))
        self.requirements_text = scrolledtext.ScrolledText(parent, height=8, width=40)
        self.requirements_text.insert(tk.END, config.Requirements)
        self.requirements_text.pack(anchor='w', fill='x')

        # Keywords
        ttk.Label(parent, text="关键词:").pack(anchor='w', pady=(10, 0))
        self.keywords_text = scrolledtext.ScrolledText(parent, height=5, width=40)
        self.keywords_text.insert(tk.END, config.Keywords)
        self.keywords_text.pack(anchor='w', fill='x')

        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=20, fill='x')

        self.start_button = ttk.Button(button_frame, text="开始处理", command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, expand=True, fill='x', padx=(0, 5))

        self.stop_button = ttk.Button(button_frame, text="停止处理", command=self.stop_processing, state='disabled')
        self.stop_button.pack(side=tk.LEFT, expand=True, fill='x', padx=(5, 0))

    def update_checkbox_text(self, *args):
        self.save_full_log_cb.config(text=f"保存完整日志 ({'启用' if self.save_full_log_var.get() else '禁用'})")
        self.include_req_cb.config(text=f"提示词中包含要求 ({'启用' if self.include_req_var.get() else '禁用'})")
        self.include_keywords_cb.config(text=f"提示词中包含关键词 ({'启用' if self.include_keywords_var.get() else '禁用'})")

    def preload_info(self):
        self.log_message("正在预加载信息...")
        load_api_keys_from_files()
        api_key_count = len(config.API_KEYS)
        
        # Clear previous paper data before reading
        Data.paper_data.clear()
        ReadPaper.read_bib_files()
        paper_count = len(Data.paper_data)
        
        status_text = f"API密钥数量: {api_key_count} | 总文献数: {paper_count}"
        self.status_bar.config(text=status_text)
        self.log_message("预加载完成。" + status_text)

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
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

        # Update config from UI
        config.save_full_log = self.save_full_log_var.get()
        config.include_requirements_in_prompt = self.include_req_var.get()
        config.include_keywords_in_prompt = self.include_keywords_var.get()
        config.ResearchQuestion = self.research_question_text.get("1.0", tk.END).strip()
        config.Requirements = self.requirements_text.get("1.0", tk.END).strip()
        config.Keywords = self.keywords_text.get("1.0", tk.END).strip()

        # Run processing in a separate thread
        self.processing_thread = threading.Thread(target=self.run_paper_processing)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def stop_processing(self):
        self.log_message("正在尝试停止处理...")
        # A simple way to stop is to exit the app, as safely stopping a thread is complex.
        # For a more graceful shutdown, a flag should be used within the processing loop.
        self.destroy()

    def run_paper_processing(self):
        try:
            self.log_message("处理开始...")
            # API keys are already loaded during preload
            if not config.API_KEYS:
                self.log_message("错误：没有可用的API密钥！")
                self.log_message("请在APIKey文件夹中创建txt文件并添加API密钥。")
                return

            # Papers are already loaded during preload
            if not Data.paper_data:
                self.log_message("错误：没有找到任何文献！")
                self.log_message("请检查Data文件夹中是否包含.bib文件。")
                return

            process_papers(config.ResearchQuestion, config.Keywords, config.Requirements, -1)
            self.log_message("处理完成！")
        except Exception as e:
            self.log_message(f"发生错误: {e}")
        finally:
            self.after(0, self.reset_ui_state)

    def reset_ui_state(self):
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

if __name__ == "__main__":
    app = App()
    app.mainloop()