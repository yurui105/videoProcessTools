import os
import cv2
import glob
from moviepy import VideoFileClip


class VideoProcessor:
    """视频处理类，负责视频转GIF的核心功能"""

    def __init__(self):
        self.logger_callback = None

    def set_logger_callback(self, callback):
        """设置日志回调函数"""
        self.logger_callback = callback

    def log(self, message):
        """输出日志"""
        if self.logger_callback:
            self.logger_callback(message)
        else:
            print(message)

    def get_video_files(self, directory):
        """获取目录下的所有视频文件"""
        # 支持的视频文件扩展名
        video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv']
        videos = []

        for ext in video_extensions:
            pattern = os.path.join(directory, ext)
            videos.extend(glob.glob(pattern))

        return sorted(videos)

    def process_videos(self, input_path, output_path, start_time=0,
                       split_duration=None, split_count=None, selected_region=None):
        """处理视频转GIF

        Args:
            input_path: 输入视频路径
            output_path: 输出GIF路径
            start_time: 开始时间（秒）
            split_duration: 分割时长（秒），与split_count互斥
            split_count: 分割数量，与split_duration互斥
            selected_region: 选择的区域(x, y, width, height)，如果为None则转换整个视频
        """
        # 检查参数
        if not os.path.exists(input_path):
            raise ValueError(f"输入路径不存在: {input_path}")

        if not os.path.exists(output_path):
            self.log(f"输出路径不存在，将创建: {output_path}")
            os.makedirs(output_path, exist_ok=True)

        if split_duration is None and split_count is None:
            raise ValueError("分割时长和分割数量不能同时为空")

        if split_duration is not None and split_count is not None:
            self.log("分割时长和分割数量同时指定，将使用分割时长")
            split_count = None

        # 获取视频文件列表
        videos = self.get_video_files(input_path)

        if not videos:
            self.log("未找到视频文件")
            return

        self.log(f"找到 {len(videos)} 个视频文件")

        # 处理每个视频
        for i, video_path in enumerate(videos):
            try:
                self.log(f"处理视频 {i + 1}/{len(videos)}: {os.path.basename(video_path)}")
                self.convert_video_to_gif(video_path, output_path, start_time,
                                          split_duration, split_count, selected_region)
            except Exception as e:
                self.log(f"处理视频出错: {str(e)}")

    def convert_video_to_gif(self, video_path, output_path, start_time=0,
                             split_duration=None, split_count=None, selected_region=None):
        """将单个视频转换为GIF

        Args:
            video_path: 视频路径
            output_path: 输出GIF路径
            start_time: 开始时间（秒）
            split_duration: 分割时长（秒），与split_count互斥
            split_count: 分割数量，与split_duration互斥
            selected_region: 选择的区域(x, y, width, height)，如果为None则转换整个视频
        """
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(output_path, video_name)
        os.makedirs(output_dir, exist_ok=True)

        # 使用moviepy打开视频
        clip = VideoFileClip(video_path)

        # 检查开始时间是否有效
        if start_time >= clip.duration:
            self.log(f"警告: 开始时间 {start_time}秒 超过视频时长 {clip.duration}秒，将不处理此视频")
            clip.close()
            return

        # 裁剪到开始时间
        clip = clip.subclipped(start_time)

        # 如果有选择区域，裁剪视频
        if selected_region:
            x, y, width, height = selected_region
            clip = clip.crop(x1=x, y1=y, x2=x + width, y2=y + height)

        # 根据分割方式计算片段
        segments = []

        if split_duration is not None:
            # 按时长分割
            duration = clip.duration
            current_time = 0
            segment_index = 0

            while current_time < duration:
                end_time = min(current_time + split_duration, duration)
                segments.append((segment_index, current_time, end_time))
                current_time = end_time
                segment_index += 1
        else:
            # 按数量分割
            duration = clip.duration
            segment_duration = duration / split_count

            for i in range(split_count):
                start = i * segment_duration
                end = min((i + 1) * segment_duration, duration)
                segments.append((i, start, end))

        self.log(f"视频 {video_name} 将分割为 {len(segments)} 个片段")

        # 处理每个片段
        for segment_index, seg_start, seg_end in segments:
            self.log(f"处理片段 {segment_index + 1}/{len(segments)}: {seg_start:.1f}秒 - {seg_end:.1f}秒")

            # 创建子片段
            subclip = clip.subclip(seg_start, seg_end)

            # 输出GIF文件路径
            gif_path = os.path.join(output_dir, f"{segment_index + 1}.gif")

            # 转换为GIF
            self.log(f"生成GIF: {gif_path}")
            subclip.write_gif(gif_path, fps=10)  # 使用较低的fps以减小文件大小

            self.log(f"片段 {segment_index + 1} 处理完成")

        # 关闭视频
        clip.close()
        self.log(f"视频 {video_name} 处理完成")