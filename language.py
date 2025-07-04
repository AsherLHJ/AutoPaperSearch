# 语言配置文件

# 中文界面文本
zh_CN = {
    # 窗口标题
    "app_title": "SearchPaper - 学术论文相关性筛选工具",
    
    # 主要标签
    "config_label": "配置",
    "log_label": "日志",
    
    # 复选框
    "save_full_log": "保存完整日志",
    "include_req": "提示词中包含要求",
    "include_keywords": "提示词中包含关键词",
    "enabled": "启用",
    "disabled": "禁用",
    
    # 输入框标签
    "research_question_label": "研究问题:",
    "requirements_label": "要求:",
    "keywords_label": "关键词:",
    
    # 按钮
    "start_button": "开始处理",
    "stop_button": "停止处理",
    
    # 文件夹路径
    "data_folder_label": "Data文件夹路径:",
    "apikey_folder_label": "APIKey文件夹路径:",
    "result_folder_label": "Result文件夹路径:",
    "browse_button": "浏览...",
    
    # 标签页
    "main_tab": "主要设置",
    "folder_tab": "文件夹设置",
    
    # 语言选择
    "language_label": "界面语言:",
    "language_zh": "中文",
    "language_en": "English",
    
    # 状态和日志消息
    "loading": "正在加载...",
    "preload_complete": "预加载完成。",
    "api_key_count": "API密钥数量:",
    "paper_count": "总文献数:",
    "processing_start": "处理开始...",
    "processing_stop": "正在尝试停止处理...",
    "processing_complete": "处理完成！",
    "error_occurred": "发生错误:",
    "no_api_keys": "错误：没有可用的API密钥！",
    "add_api_keys": "请在APIKey文件夹中创建txt文件并添加API密钥。",
    "no_papers": "错误：没有找到任何文献！",
    "check_data_folder": "请检查Data文件夹中是否包含.bib文件。",
    "creating_folder": "正在创建{0}文件夹...",
    "folder_not_exist": "错误：{0}文件夹不存在:",
    "preloading": "正在预加载信息..."
}

# 英文界面文本
en_US = {
    # 窗口标题
    "app_title": "SearchPaper - Academic Paper Relevance Screening Tool",
    
    # 主要标签
    "config_label": "Configuration",
    "log_label": "Log",
    
    # 复选框
    "save_full_log": "Save Full Log",
    "include_req": "Include Requirements in Prompt",
    "include_keywords": "Include Keywords in Prompt",
    "enabled": "Enabled",
    "disabled": "Disabled",
    
    # 输入框标签
    "research_question_label": "Research Question:",
    "requirements_label": "Requirements:",
    "keywords_label": "Keywords:",
    
    # 按钮
    "start_button": "Start Processing",
    "stop_button": "Stop Processing",
    
    # 文件夹路径
    "data_folder_label": "Data Folder Path:",
    "apikey_folder_label": "APIKey Folder Path:",
    "result_folder_label": "Result Folder Path:",
    "browse_button": "Browse...",
    
    # 标签页
    "main_tab": "Main Settings",
    "folder_tab": "Folder Settings",
    
    # 语言选择
    "language_label": "Interface Language:",
    "language_zh": "中文",
    "language_en": "English",
    
    # 状态和日志消息
    "loading": "Loading...",
    "preload_complete": "Preload complete.",
    "api_key_count": "API Key Count:",
    "paper_count": "Total Papers:",
    "processing_start": "Processing started...",
    "processing_stop": "Attempting to stop processing...",
    "processing_complete": "Processing complete!",
    "error_occurred": "Error occurred:",
    "no_api_keys": "Error: No API keys available!",
    "add_api_keys": "Please create txt files in the APIKey folder and add API keys.",
    "no_papers": "Error: No papers found!",
    "check_data_folder": "Please check if the Data folder contains .bib files.",
    "creating_folder": "Creating {0} folder...",
    "folder_not_exist": "Error: {0} folder does not exist:",
    "preloading": "Preloading information..."
}

# 获取当前语言文本
def get_text(language_code):
    if language_code == 'en_US':
        return en_US
    else:  # 默认使用中文
        return zh_CN