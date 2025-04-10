import time
from datetime import datetime


class Logger:
    """日志工具类，处理日志记录"""

    def __init__(self, log_file=None):
        """初始化日志工具

        Args:
            log_file: 日志文件路径，如果为None则不保存到文件
        """
        self.log_file = log_file
        self.callbacks = []

        # 如果指定了日志文件，初始化文件
        if log_file:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== 日志开始时间: {self._get_time()} ===\n")

    def add_callback(self, callback):
        """添加日志回调函数"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def remove_callback(self, callback):
        """移除日志回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def _get_time(self):
        """获取格式化的当前时间"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log(self, message, level="INFO"):
        """记录日志

        Args:
            message: 日志消息
            level: 日志级别，如INFO, WARNING, ERROR等
        """
        log_entry = f"[{level}] {self._get_time()}: {message}"

        # 输出到控制台
        print(log_entry)

        # 写入文件
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")

        # 调用回调函数
        for callback in self.callbacks:
            callback(log_entry)

    def info(self, message):
        """记录信息级别日志"""
        self.log(message, "INFO")

    def warning(self, message):
        """记录警告级别日志"""
        self.log(message, "WARNING")

    def error(self, message):
        """记录错误级别日志"""
        self.log(message, "ERROR")

    def success(self, message):
        """记录成功级别日志"""
        self.log(message, "SUCCESS")