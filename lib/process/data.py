import threading
from collections import deque

# 论文处理相关的全局变量
result_file_name = ""
paper_data = {}
token_used = 0

# 更详细的token统计
prompt_tokens_used = 0
completion_tokens_used = 0
prompt_cache_hit_tokens_used = 0
prompt_cache_miss_tokens_used = 0

# 日志文件相关的全局变量
full_log_file = None

# 线程锁
file_write_lock = threading.Lock()
token_lock = threading.Lock()
progress_lock = threading.Lock()

# 进度跟踪相关的全局变量
processed_papers = 0
processing_times = deque(maxlen=10)  # 存储最近10篇文章的处理时间
start_time = None
total_papers_to_process = 0
progress_stop_event = threading.Event()
active_threads = 0  # 活跃线程数追踪