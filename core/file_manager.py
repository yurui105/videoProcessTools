import os
import glob
import shutil


class FileManager:
    """文件管理类，处理文件和目录操作"""

    @staticmethod
    def ensure_directory(directory):
        """确保目录存在，不存在则创建"""
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    @staticmethod
    def get_files_by_extension(directory, extensions):
        """获取指定目录下特定扩展名的文件

        Args:
            directory: 目录路径
            extensions: 扩展名列表，如 ['.mp4', '.avi']

        Returns:
            文件路径列表
        """
        files = []
        for ext in extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            pattern = os.path.join(directory, f"*{ext}")
            files.extend(glob.glob(pattern))
        return sorted(files)

    @staticmethod
    def clean_directory(directory):
        """清空目录内容但保留目录"""
        if os.path.exists(directory):
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        else:
            os.makedirs(directory)
        return directory
