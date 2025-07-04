import os
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import Data, SearchPaper
from . import utils
import config_loader as config
import json

def process_paper_batch(paper_indices, rq, keywords, requirements, api_key, thread_id, result_file_path, log_file_path, yon_log_file_path, total_papers):
    """
    处理一批论文的函数，由单个线程执行
    """
    relevant_count = 0
    batch_tokens = 0
    
    for idx, paper_index in enumerate(paper_indices):
        if paper_index in Data.paper_data:
            # 记录单篇论文处理开始时间
            single_start_time = time.time()
            
            paper = Data.paper_data[paper_index]
            title = paper['title']
            abstract = paper['abstract']
            entry = paper['entry']
            
            try:
                # 调用SearchPaper中的方法检查相关性，传入对应的API密钥和requirements
                relevance, tokens, reason, prompt_tokens, completion_tokens, cache_hit, cache_miss = SearchPaper.check_paper_relevance(
                    rq, keywords, requirements, title, abstract, api_key)
                
                # 累加token使用量
                batch_tokens += tokens
                with Data.token_lock:
                    Data.token_used += tokens
                    Data.prompt_tokens_used += prompt_tokens
                    Data.completion_tokens_used += completion_tokens
                    Data.prompt_cache_hit_tokens_used += cache_hit
                    Data.prompt_cache_miss_tokens_used += cache_miss
                
                # 计算单篇论文处理时间
                single_elapsed_time = time.time() - single_start_time
                
                # 更新进度信息
                utils.update_progress(single_elapsed_time)
                
                # 记录到Y/N日志文件（无论结果是Y还是N）
                with Data.file_write_lock:
                    with open(yon_log_file_path, 'a', encoding='utf-8') as yon_log_file:
                        yon_log_file.write('{\n')
                        yon_log_file.write(f'    "title": "{title}",\n')
                        yon_log_file.write(f'    "result": "{relevance.strip().upper()}",\n')
                        yon_log_file.write(f'    "reason": "{reason}"\n')
                        yon_log_file.write('}\n\n')
                
                # 如果相关，则添加到结果文件中
                if relevance.strip().upper() == 'Y':
                    relevant_count += 1
                    
                    # 使用线程锁保护文件写入
                    with Data.file_write_lock:
                        # 将entry写入结果文件（追加模式）
                        with open(result_file_path, 'a', encoding='utf-8') as result_file:
                            result_file.write(entry + "\n\n")
                        
                        # 同时写入日志文件（JSON格式）
                        with open(log_file_path, 'a', encoding='utf-8') as log_file:
                            log_file.write('{\n')
                            log_file.write(f'    "title": "{title}",\n')
                            log_file.write(f'    "reason": "{reason}"\n')
                            log_file.write('}\n')
                    
            except Exception as e:
                # 静默处理错误，只在完整日志中记录
                with Data.file_write_lock:
                    if config.save_full_log and Data.full_log_file:
                        Data.full_log_file.write(f"[Thread-{thread_id}] 处理论文 {paper_index} 时出错: {str(e)}\n")
                        Data.full_log_file.flush()
    
    return relevant_count, batch_tokens

def process_papers(rq, keywords, requirements, n):
    """
    处理paper_data中的文章，将相关的文章保存到结果文件中
    """
    # 重置进度跟踪变量
    utils.reset_progress_tracking()
    
    # 确保Result文件夹存在
    result_folder = config.RESULT_FOLDER
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)
    
    # 确保Log文件夹存在
    log_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Log')
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    
    # 生成带时间戳的结果文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    Data.result_file_name = f"Result_{timestamp}"
    result_file_path = os.path.join(result_folder, f"{Data.result_file_name}.bib")
    
    # 创建日志文件路径（移到Log文件夹）
    log_file_path = os.path.join(log_folder, f"Log_{Data.result_file_name}.txt")
    
    # 创建Y/N判断结果日志文件路径
    yon_log_file_path = os.path.join(log_folder, f"Log_YoN_{timestamp}.txt")
    
    # 如果启用完整日志，创建完整日志文件
    if config.save_full_log:
        full_log_file_path = os.path.join(log_folder, f"Log_ALL_{timestamp}.txt")
        Data.full_log_file = open(full_log_file_path, 'w', encoding='utf-8')
        utils.print_and_log(f"完整日志文件已创建: {full_log_file_path}")
    
    # 在结果文件开头写入搜索主题
    with open(result_file_path, 'w', encoding='utf-8') as result_file:
        result_file.write(f"Search Topic {{{rq}}}\n\n")
    
    # 在日志文件开头写入搜索主题、关键词和要求
    with open(log_file_path, 'w', encoding='utf-8') as log_file:
        # 写入注释形式的头部信息
        log_file.write(f"// Search Topic: {rq}\n")
        log_file.write(f"// Keywords: {keywords}\n")
        if requirements:
            log_file.write(f"// Requirements: {requirements}\n")
        log_file.write("\n")
    
    # 在Y/N日志文件开头写入搜索信息
    with open(yon_log_file_path, 'w', encoding='utf-8') as yon_log_file:
        yon_log_file.write(f"// Search Topic: {rq}\n")
        yon_log_file.write(f"// Keywords: {keywords}\n")
        if requirements:
            yon_log_file.write(f"// Requirements: {requirements}\n")
    
    # 获取研究方向
    research_direction = rq
    
    # 处理前N篇文章（或者所有文章）
    paper_count = len(Data.paper_data)
    if n == -1:
        max_papers = paper_count
    else:
        max_papers = min(n, paper_count)
    
    Data.total_papers_to_process = max_papers
    
    utils.print_and_log(f"\n开始处理{max_papers}篇文章的相关性...")
    utils.print_and_log(f"文章总数: {paper_count}")
    utils.print_and_log(f"系统最多可配置的并行数: {len(config.API_KEYS)}")

    # 将论文索引分配给不同的线程
    paper_indices = list(range(1, max_papers + 1))
    num_threads = min(len(config.API_KEYS), max_papers)  # 关键代码：线程数取API密钥数和论文数的较小值
    batch_size = max_papers // num_threads
    remainder = max_papers % num_threads
    
    # 分配论文给各个线程
    batches = []
    start_idx = 0
    for i in range(num_threads):
        # 前remainder个线程多分配一篇论文
        current_batch_size = batch_size + (1 if i < remainder else 0)
        batch = paper_indices[start_idx:start_idx + current_batch_size]
        batches.append(batch)
        start_idx += current_batch_size
    
    # 计算平均每个线程分配的论文数
    avg_papers_per_thread = max_papers / num_threads
    utils.print_and_log(f"实际使用线程数: {num_threads}, 平均每线程处理: {avg_papers_per_thread:.1f}篇")
    
    # 启动进度监控线程
    Data.progress_stop_event.clear()
    progress_thread = threading.Thread(target=utils.progress_monitor, daemon=True)
    progress_thread.start()
    
    # 使用线程池并行处理
    total_relevant_count = 0
    
    # 设置活跃线程数
    Data.active_threads = num_threads  # 记录实际使用的线程数
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:  # 使用动态计算的线程数
        # 提交所有任务
        future_to_thread = {}
        for i, batch in enumerate(batches):
            if batch:  # 确保批次不为空
                future = executor.submit(
                    process_paper_batch,
                    batch,
                    research_direction,
                    keywords,
                    requirements,  # 添加requirements参数
                    config.API_KEYS[i],  # 为每个线程分配不同的API密钥
                    i + 1,
                    result_file_path,
                    log_file_path,
                    yon_log_file_path,  # 添加Y/N日志文件路径
                    max_papers
                )
                future_to_thread[future] = i + 1
        
        # 等待所有任务完成
        for future in as_completed(future_to_thread):
            thread_id = future_to_thread[future]
            try:
                relevant_count, batch_tokens = future.result()
                total_relevant_count += relevant_count
            except Exception as e:
                with Data.file_write_lock:
                    if config.save_full_log and Data.full_log_file:
                        Data.full_log_file.write(f"\n线程{thread_id}发生错误: {str(e)}\n")
                        Data.full_log_file.flush()
    
    # 停止进度监控线程
    Data.progress_stop_event.set()
    progress_thread.join(timeout=2)
    
    # 计算总耗时
    total_elapsed_time = time.time() - Data.start_time
    
    # 格式化总耗时
    hours = int(total_elapsed_time // 3600)
    minutes = int((total_elapsed_time % 3600) // 60)
    seconds = int(total_elapsed_time % 60)
    
    # 计算平均单篇文章耗时（考虑并发处理）
    # 实际平均速度 = 总文章数 / 总耗时
    actual_papers_per_second = max_papers / total_elapsed_time if total_elapsed_time > 0 else 0
    # 实际单篇耗时 = 1 / 实际平均速度
    average_time_per_paper = 1 / actual_papers_per_second if actual_papers_per_second > 0 else 0
    
    # 计算最终价格
    from . import Price
    final_price = Price.calculate_token_price(
        Data.prompt_tokens_used,
        Data.completion_tokens_used,
        Data.prompt_cache_hit_tokens_used,
        Data.prompt_cache_miss_tokens_used
    )
    
    utils.print_and_log(f"\n处理完成! 共找到{total_relevant_count}篇相关文章")
    utils.print_and_log(f"----- 耗时统计 -----")
    utils.print_and_log(f"  总耗时: {hours}h{minutes}m{seconds}s")
    utils.print_and_log(f"  平均单篇文章耗时: {average_time_per_paper:.2f}秒（{num_threads}个线程并发处理）")
    utils.print_and_log(f"  实际处理速度: {actual_papers_per_second:.2f}篇/秒")
    utils.print_and_log(f"----- Token使用统计 -----")
    utils.print_and_log(f"  输入Token: {Data.prompt_tokens_used} (缓存命中: {Data.prompt_cache_hit_tokens_used}, 未命中: {Data.prompt_cache_miss_tokens_used})")
    utils.print_and_log(f"  输出Token: {Data.completion_tokens_used}")
    utils.print_and_log(f"  总计Token: {Data.token_used}")
    utils.print_and_log(f"----- 价格统计 -----")
    utils.print_and_log(f"  总费用估算: {Price.format_price(final_price)}")
    utils.print_and_log(f"----- 结果文件 -----")
    utils.print_and_log(f"  相关文章已保存到: {result_file_path}")
    utils.print_and_log(f"  相关文章日志已保存到: {log_file_path}")
    utils.print_and_log(f"  所有判断结果已保存到: {yon_log_file_path}")
    
    # 关闭完整日志文件
    if Data.full_log_file:
        Data.full_log_file.close()
