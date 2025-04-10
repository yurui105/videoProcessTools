import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFileDialog,
                             QTextEdit, QSplitter, QMessageBox, QSpinBox,
                             QDoubleSpinBox, QGroupBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon

from ui.video_preview import VideoPreviewWidget
from core.video_processor import VideoProcessor
from utils.logger import Logger


class ProcessingThread(QThread):
    """视频处理线程，防止UI卡死"""
    update_signal = pyqtSignal(str)  # 用于发送日志消息的信号
    finished_signal = pyqtSignal()  # 处理完成信号
    error_signal = pyqtSignal(str)  # 错误信号

    def __init__(self, processor, params):
        super().__init__()
        self.processor = processor
        self.params = params

    def run(self):
        try:
            self.processor.set_logger_callback(self.log_callback)
            self.processor.process_videos(**self.params)
            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))

    def log_callback(self, message):
        self.update_signal.emit(message)


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.logger = Logger()
        self.processor = VideoProcessor()
        self.processing_thread = None

    def init_ui(self):
        """初始化UI界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("视频转GIF工具")
        self.resize(1200, 800)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 创建上下分割器
        splitter = QSplitter(Qt.Vertical)

        # 上半部分 - 参数设置和视频预览
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setSpacing(15)

        # 左侧 - 参数设置
        params_group = QGroupBox("参数设置")
        params_group.setFont(QFont("Arial", 10, QFont.Bold))
        params_layout = QVBoxLayout(params_group)
        params_layout.setSpacing(15)

        # 输入视频路径
        input_layout = QHBoxLayout()
        input_label = QLabel("输入视频路径:")
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("请输入视频所在文件夹路径")
        browse_input_btn = QPushButton("浏览...")
        browse_input_btn.clicked.connect(self.browse_input_path)
        self.style_button(browse_input_btn)

        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(browse_input_btn)
        params_layout.addLayout(input_layout)

        # 输出路径
        output_layout = QHBoxLayout()
        output_label = QLabel("输出路径:")
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("请选择GIF输出路径")
        browse_output_btn = QPushButton("浏览...")
        browse_output_btn.clicked.connect(self.browse_output_path)
        self.style_button(browse_output_btn)

        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(browse_output_btn)
        params_layout.addLayout(output_layout)

        # 开始时间
        start_time_layout = QHBoxLayout()
        start_time_label = QLabel("开始时间(秒):")
        self.start_time = QDoubleSpinBox()
        self.start_time.setMinimum(0)
        self.start_time.setMaximum(999999)
        self.start_time.setValue(0)
        self.start_time.setDecimals(1)
        self.style_spinbox(self.start_time)

        start_time_layout.addWidget(start_time_label)
        start_time_layout.addWidget(self.start_time)
        params_layout.addLayout(start_time_layout)

        # 分割方式选择
        split_type_group = QGroupBox("分割方式")
        split_type_layout = QVBoxLayout(split_type_group)

        self.split_type_group = QButtonGroup(self)
        self.split_by_duration = QRadioButton("按时长分割")
        self.split_by_count = QRadioButton("按数量分割")
        self.split_by_duration.setChecked(True)

        self.split_type_group.addButton(self.split_by_duration, 1)
        self.split_type_group.addButton(self.split_by_count, 2)

        split_type_layout.addWidget(self.split_by_duration)
        split_type_layout.addWidget(self.split_by_count)

        params_layout.addWidget(split_type_group)

        # 分割时长
        duration_layout = QHBoxLayout()
        duration_label = QLabel("分割时长(秒):")
        self.duration = QDoubleSpinBox()
        self.duration.setMinimum(0.1)
        self.duration.setMaximum(999999)
        self.duration.setValue(5)
        self.duration.setDecimals(1)
        self.style_spinbox(self.duration)

        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration)
        params_layout.addLayout(duration_layout)

        # 分割数量
        count_layout = QHBoxLayout()
        count_label = QLabel("分割数量:")
        self.count = QSpinBox()
        self.count.setMinimum(1)
        self.count.setMaximum(999999)
        self.count.setValue(5)
        self.style_spinbox(self.count)

        count_layout.addWidget(count_label)
        count_layout.addWidget(self.count)
        params_layout.addLayout(count_layout)

        # 状态切换
        self.split_by_duration.toggled.connect(self.update_split_type)
        self.update_split_type()

        # 开始按钮
        self.start_button = QPushButton("开始处理")
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self.start_processing)
        self.style_button(self.start_button, is_primary=True)

        params_layout.addWidget(self.start_button)
        params_layout.addStretch()

        # 右侧 - 视频预览
        self.video_preview = VideoPreviewWidget()

        # 将左右两侧添加到上半部分布局
        top_layout.addWidget(params_group, 1)
        top_layout.addWidget(self.video_preview, 2)

        # 下半部分 - 日志显示
        log_group = QGroupBox("处理日志")
        log_group.setFont(QFont("Arial", 10, QFont.Bold))
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-family: Consolas, Monaco, monospace;
                padding: 8px;
            }
        """)

        log_layout.addWidget(self.log_text)

        # 添加到分割器
        splitter.addWidget(top_widget)
        splitter.addWidget(log_group)
        splitter.setSizes([600, 200])

        main_layout.addWidget(splitter)

        # 应用全局样式
        self.apply_styles()

    def apply_styles(self):
        """应用全局样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 1.5ex;
                padding: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: white;
            }
            QLabel {
                font-size: 12px;
            }
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
                min-height: 25px;
            }
            QLineEdit:focus {
                border: 1px solid #4a86e8;
            }
            QPushButton {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: #f8f8f8;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QPushButton:pressed {
                background-color: #d9d9d9;
            }
            QRadioButton {
                font-size: 12px;
                padding: 5px;
            }
            QSpinBox, QDoubleSpinBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
                min-height: 25px;
            }
        """)

    def style_button(self, button, is_primary=False):
        """设置按钮样式"""
        if is_primary:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4a86e8;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3b78de;
                }
                QPushButton:pressed {
                    background-color: #2d5bb9;
                }
                QPushButton:disabled {
                    background-color: #a6c8ff;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f8f8f8;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #e6e6e6;
                }
                QPushButton:pressed {
                    background-color: #d9d9d9;
                }
            """)

    def style_spinbox(self, spinbox):
        """设置数字输入框样式"""
        spinbox.setStyleSheet("""
            QSpinBox, QDoubleSpinBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #4a86e8;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                width: 16px;
                border-radius: 3px;
            }
        """)

    def update_split_type(self):
        """根据选择的分割方式更新UI状态"""
        is_duration = self.split_by_duration.isChecked()
        self.duration.setEnabled(is_duration)
        self.count.setEnabled(not is_duration)

    def browse_input_path(self):
        """浏览并选择输入视频路径"""
        directory = QFileDialog.getExistingDirectory(self, "选择输入视频文件夹")
        if directory:
            self.input_path.setText(directory)
            self.log_text.append(f"输入路径已设置: {directory}")
            # 尝试加载视频列表
            try:
                videos = self.processor.get_video_files(directory)
                if videos:
                    self.log_text.append(f"找到 {len(videos)} 个视频文件")
                    # 设置视频列表到预览窗口
                    self.video_preview.set_video_list(videos)
                    # 设置第一个视频到预览窗口
                    if videos:
                        self.video_preview.set_video(videos[0])
                else:
                    self.log_text.append("未找到视频文件")
            except Exception as e:
                self.log_text.append(f"加载视频列表出错: {str(e)}")

    def browse_output_path(self):
        """浏览并选择输出路径"""
        directory = QFileDialog.getExistingDirectory(self, "选择GIF输出文件夹")
        if directory:
            self.output_path.setText(directory)
            self.log_text.append(f"输出路径已设置: {directory}")

    def start_processing(self):
        """开始处理视频"""
        # 参数检查
        input_path = self.input_path.text().strip()
        output_path = self.output_path.text().strip()
        start_time = self.start_time.value()

        if not input_path:
            QMessageBox.warning(self, "参数错误", "请输入视频路径")
            return

        if not output_path:
            QMessageBox.warning(self, "参数错误", "请选择输出路径")
            return

        # 获取分割参数
        split_by_duration = self.split_by_duration.isChecked()

        if split_by_duration:
            duration = self.duration.value()
            if duration <= 0:
                QMessageBox.warning(self, "参数错误", "分割时长必须大于0")
                return
            count = None
        else:
            count = self.count.value()
            if count <= 0:
                QMessageBox.warning(self, "参数错误", "分割数量必须大于0")
                return
            duration = None

        # 获取视频预览框选区域
        selected_region = self.video_preview.get_selected_region()

        # 准备处理参数
        params = {
            'input_path': input_path,
            'output_path': output_path,
            'start_time': start_time,
            'split_duration': duration,
            'split_count': count,
            'selected_region': selected_region
        }

        # 禁用开始按钮
        self.start_button.setEnabled(False)
        self.log_text.append("开始处理视频...")

        # 创建并启动处理线程
        self.processing_thread = ProcessingThread(self.processor, params)
        self.processing_thread.update_signal.connect(self.update_log)
        self.processing_thread.finished_signal.connect(self.processing_finished)
        self.processing_thread.error_signal.connect(self.processing_error)
        self.processing_thread.start()

    def update_log(self, message):
        """更新日志显示"""
        self.log_text.append(message)
        # 自动滚动到底部
        scroll_bar = self.log_text.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def processing_finished(self):
        """处理完成回调"""
        self.start_button.setEnabled(True)
        self.log_text.append("所有视频处理完成!")
        QMessageBox.information(self, "处理完成", "所有视频已成功转换为GIF")

    def processing_error(self, error_message):
        """处理错误回调"""
        self.start_button.setEnabled(True)
        self.log_text.append(f"处理出错: {error_message}")
        QMessageBox.critical(self, "处理错误", f"发生错误: {error_message}")
