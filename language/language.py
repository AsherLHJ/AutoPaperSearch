# 语言配置文件

# 中文界面文本
zh_CN = {
    # 窗口标题
    "app_title": "SearchPaper - 学术论文相关性筛选工具",
    
    # 菜单
    "menu_help": "帮助",
    "menu_about": "关于",
    "about_title": "关于",
    "about_text": "SearchPaper - 学术论文相关性筛选工具\n\n版本: 1.0\n作者: 李宏基，栗梓明\n© 2025 版权所有",
    
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
    "preloading": "正在预加载信息...",
    
    # 帮助信息
    "help_button": "帮助",
    "help_title": "使用帮助",
    "help_content": """AutoPaperSearch 使用指南

【文件夹结构说明】
• Data文件夹: 存放学术论文的.bib文件
  ⚠️ 重要提醒：必须在Data文件夹下新建子文件夹来存放.bib文件！
  - 正确做法：Data/CHI/、Data/IEEEVR/ 等子文件夹中存放.bib文件
  - 错误做法：直接将.bib文件放在Data根目录下（不会被识别）
  - 支持按会议、年份等分类存放
  - 系统会自动读取所有子文件夹中的.bib文件
  
• APIKey文件夹: 存放API密钥文件
  - 在此文件夹中创建.txt文件并添加您的API密钥
  - 支持多个API密钥文件，系统会自动加载
  
• Result文件夹: 存放筛选结果
  - 生成的相关论文会保存为.bib格式
  - 文件名包含时间戳便于管理
  
• Log文件夹: 存放处理日志
  - Log_Result: 筛选结果日志
  - Log_YoN: 是否相关判断日志
  - Log_ALL: 完整处理日志

【使用步骤】
1. 确保Data文件夹中有.bib文件
2. 在APIKey文件夹中添加API密钥
3. 填写研究问题、要求和关键词
4. 点击"开始处理"进行论文筛选

【注意事项】
• 处理过程中请勿关闭程序
• 可随时点击"停止处理"中断任务
• 建议定期备份重要的筛选结果"""
}

# 英文界面文本
en_US = {
    # 窗口标题
    "app_title": "SearchPaper - Academic Paper Relevance Screening Tool",
    
    # 菜单
    "menu_help": "Help",
    "menu_about": "About",
    "about_title": "About",
    "about_text": "SearchPaper - Academic Paper Relevance Screening Tool\n\nVersion: 1.0\nAuthors: Li Hongji, Li Ziming\n© 2025 All Rights Reserved",
    
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
    "preloading": "Preloading information...",
    
    # 帮助信息
    "help_button": "Help",
    "help_title": "User Guide",
    "help_content": """AutoPaperSearch User Guide

【Folder Structure】
• Data Folder: Store academic paper .bib files
  ⚠️ Important: You MUST create subfolders under Data folder to store .bib files!
  - Correct: Store .bib files in Data/CHI/, Data/IEEEVR/ subfolders
  - Wrong: Placing .bib files directly in Data root directory (will NOT be recognized)
  - Support classification by conference, year, etc.
  - System automatically reads all .bib files in subfolders
  
• APIKey Folder: Store API key files
  - Create .txt files and add your API keys
  - Support multiple API key files, auto-loaded
  
• Result Folder: Store screening results
  - Relevant papers saved in .bib format
  - Filenames include timestamps for management
  
• Log Folder: Store processing logs
  - Log_Result: Screening result logs
  - Log_YoN: Relevance judgment logs
  - Log_ALL: Complete processing logs

【Usage Steps】
1. Ensure .bib files exist in Data folder
2. Add API keys to APIKey folder
3. Fill in research question, requirements, and keywords
4. Click "Start Processing" to screen papers

【Notes】
• Do not close program during processing
• Click "Stop Processing" to interrupt anytime
• Regularly backup important screening results"""
}

# 获取当前语言文本
def get_text(language_code):
    if language_code == 'en_US':
        return en_US
    else:  # 默认使用中文
        return zh_CN