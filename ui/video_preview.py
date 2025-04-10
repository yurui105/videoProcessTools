import cv2
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout,
                             QPushButton, QComboBox, QSizePolicy, QSlider)
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QMouseEvent, QFont


class VideoPreviewWidget(QWidget):
    """视频预览窗口，支持视频播放和区域选择"""

    def __init__(self):
        super().__init__()
        self.init_ui()

        # 视频相关变量
        self.video_path = None
        self.cap = None
        self.frame = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # 区域选择相关变量
        self.selecting = False
        self.selection_rect = QRect()
        self.start_point = QPoint()
        self.current_point = QPoint()

        # 视频文件下拉框
        self.videos = []

        # 帧位置和总帧数
        self.current_frame_position = 0
        self.total_frames = 0
        self.is_slider_updating = False

    def init_ui(self):
        """初始化UI界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title_label = QLabel("视频预览")
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 视频选择下拉框
        select_layout = QHBoxLayout()
        select_label = QLabel("选择视频:")
        self.video_selector = QComboBox()
        self.video_selector.currentIndexChanged.connect(self.change_video)
        select_layout.addWidget(select_label)
        select_layout.addWidget(self.video_selector)
        layout.addLayout(select_layout)

        # 预览标签
        self.preview_label = QLabel("无视频")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setMinimumHeight(300)
        layout.addWidget(self.preview_label)

        # 添加进度条
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(100)
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(False)
        self.progress_slider.valueChanged.connect(self.slider_value_changed)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 10px;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #4a86e8;
                border: 1px solid #777;
                height: 10px;
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #fff;
                border: 1px solid #777;
                height: 10px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #369;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #2a7fff;
            }
        """)
        layout.addWidget(self.progress_slider)

        # 添加时间显示标签
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

        # 控制按钮
        controls_layout = QHBoxLayout()

        self.play_button = QPushButton("播放")
        self.play_button.clicked.connect(self.toggle_play)
        self.play_button.setEnabled(False)

        self.reset_button = QPushButton("重置选择")
        self.reset_button.clicked.connect(self.reset_selection)
        self.reset_button.setEnabled(False)

        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.reset_button)
        layout.addLayout(controls_layout)

        # 提示信息
        hint_label = QLabel("提示: 拖动鼠标在视频上选择区域。只有选择的区域将被转换为GIF。")
        hint_label.setStyleSheet("color: #666; font-size: 11px;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)

        # 鼠标事件设置
        self.preview_label.setMouseTracking(True)
        self.preview_label.mousePressEvent = self.mouse_press_event
        self.preview_label.mouseMoveEvent = self.mouse_move_event
        self.preview_label.mouseReleaseEvent = self.mouse_release_event

    def set_video_list(self, videos):
        """设置视频列表"""
        self.videos = videos
        self.video_selector.clear()
        for video in videos:
            self.video_selector.addItem(os.path.basename(video))

    def change_video(self, index):
        """切换视频"""
        if index >= 0 and index < len(self.videos):
            self.set_video(self.videos[index])

    def set_video(self, video_path):
        """设置视频路径并初始化"""
        # 停止当前播放
        self.stop_video()

        self.video_path = video_path

        try:
            # 打开视频
            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                raise Exception("无法打开视频文件")

            # 读取第一帧
            ret, self.frame = self.cap.read()
            if not ret:
                raise Exception("无法读取视频帧")

            # 获取视频总帧数和FPS
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            duration = self.total_frames / fps if fps > 0 else 0

            # 更新进度条
            self.progress_slider.setEnabled(True)
            self.progress_slider.setMaximum(self.total_frames - 1)
            self.progress_slider.setValue(0)
            self.current_frame_position = 0

            # 更新时间显示
            self.update_time_display()

            # 显示第一帧
            self.display_frame(self.frame)

            # 启用控制按钮
            self.play_button.setEnabled(True)
            self.reset_button.setEnabled(True)

            # 更新视频选择下拉框
            current_filename = os.path.basename(video_path)
            index = self.video_selector.findText(current_filename)
            if index >= 0:
                self.video_selector.setCurrentIndex(index)

        except Exception as e:
            self.preview_label.setText(f"视频加载失败: {str(e)}")
            self.play_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            self.progress_slider.setEnabled(False)

    def update_time_display(self):
        """更新时间显示"""
        if self.cap is None:
            return

        # 计算当前时间和总时间
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30  # 默认值

        current_time = self.current_frame_position / fps
        total_time = self.total_frames / fps

        # 格式化为分:秒
        current_min, current_sec = divmod(int(current_time), 60)
        total_min, total_sec = divmod(int(total_time), 60)

        time_text = f"{current_min:02d}:{current_sec:02d} / {total_min:02d}:{total_sec:02d}"
        self.time_label.setText(time_text)

    def slider_value_changed(self, value):
        """进度条值改变时的处理"""
        if self.is_slider_updating or self.cap is None:
            return

        # 设置视频位置
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, value)
        ret, self.frame = self.cap.read()
        if ret:
            self.current_frame_position = value
            self.display_frame(self.frame)
            self.update_time_display()

    def toggle_play(self):
        """切换播放/暂停状态"""
        if self.timer.isActive():
            self.timer.stop()
            self.play_button.setText("播放")
        else:
            self.timer.start(33)  # 约30FPS
            self.play_button.setText("暂停")

    def stop_video(self):
        """停止视频播放"""
        if self.timer.isActive():
            self.timer.stop()
            self.play_button.setText("播放")

        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def update_frame(self):
        """更新显示下一帧"""
        if self.cap is not None and self.cap.isOpened():
            ret, self.frame = self.cap.read()
            if ret:
                self.current_frame_position += 1

                # 更新进度条，防止递归调用
                self.is_slider_updating = True
                self.progress_slider.setValue(self.current_frame_position)
                self.is_slider_updating = False

                # 更新时间显示
                self.update_time_display()

                # 显示帧
                self.display_frame(self.frame)
            else:
                # 视频播放完毕，重新开始
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.current_frame_position = 0
                self.progress_slider.setValue(0)
                self.update_time_display()
                self.timer.stop()
                self.play_button.setText("播放")

    def display_frame(self, frame):
        """显示视频帧"""
        if frame is None:
            return

        # 将BGR转换为RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 获取预览标签大小
        label_size = self.preview_label.size()

        # 调整帧大小以适应标签
        h, w, ch = frame_rgb.shape
        aspect_ratio = w / h

        if label_size.width() / label_size.height() > aspect_ratio:
            # 按高度缩放
            new_height = label_size.height()
            new_width = int(aspect_ratio * new_height)
        else:
            # 按宽度缩放
            new_width = label_size.width()
            new_height = int(new_width / aspect_ratio)

        # 缩放图像
        frame_resized = cv2.resize(frame_rgb, (new_width, new_height))

        # 创建QImage
        h, w, ch = frame_resized.shape
        img = QImage(frame_resized.data, w, h, w * ch, QImage.Format_RGB888)

        # 创建QPixmap并设置到标签
        pixmap = QPixmap.fromImage(img)

        # 计算图像在标签中的偏移量（居中显示）
        x_offset = (label_size.width() - new_width) // 2
        y_offset = (label_size.height() - new_height) // 2

        # 存储显示偏移量，用于鼠标事件坐标转换
        self.display_offset = (x_offset, y_offset)
        self.display_size = (new_width, new_height)
        self.original_size = (frame.shape[1], frame.shape[0])

        # 如果有选择区域，绘制选择框
        if not self.selection_rect.isEmpty():
            # 创建可以绘制的副本
            temp_pixmap = QPixmap(pixmap)
            painter = QPainter(temp_pixmap)
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(2)
            painter.setPen(pen)

            # 考虑图像在标签中的偏移量
            scaled_rect = self.scale_rect_to_pixmap(self.selection_rect,
                                                    self.original_size,
                                                    self.display_size)
            painter.drawRect(scaled_rect)
            painter.end()

            # 设置偏移后的pixmap
            full_pixmap = QPixmap(label_size)
            full_pixmap.fill(Qt.transparent)
            full_painter = QPainter(full_pixmap)
            full_painter.drawPixmap(x_offset, y_offset, temp_pixmap)
            full_painter.end()

            self.preview_label.setPixmap(full_pixmap)
        else:
            # 设置偏移后的pixmap
            full_pixmap = QPixmap(label_size)
            full_pixmap.fill(Qt.transparent)
            full_painter = QPainter(full_pixmap)
            full_painter.drawPixmap(x_offset, y_offset, pixmap)
            full_painter.end()

            self.preview_label.setPixmap(full_pixmap)

    def mouse_press_event(self, event: QMouseEvent):
        """鼠标按下事件"""
        if self.frame is None:
            return

        # 获取图像区域内的坐标
        x, y = event.x() - self.display_offset[0], event.y() - self.display_offset[1]

        # 检查点击是否在图像区域内
        if (0 <= x < self.display_size[0] and 0 <= y < self.display_size[1]):
            # 只有在左键点击时才开始选择
            if event.button() == Qt.LeftButton:
                self.selecting = True
                self.start_point = QPoint(x, y)
                self.current_point = QPoint(x, y)
                self.selection_rect = QRect()

    def mouse_move_event(self, event: QMouseEvent):
        """鼠标移动事件"""
        if self.selecting and self.frame is not None:
            # 获取图像区域内的坐标
            x, y = event.x() - self.display_offset[0], event.y() - self.display_offset[1]

            # 限制坐标在图像区域内
            x = max(0, min(x, self.display_size[0] - 1))
            y = max(0, min(y, self.display_size[1] - 1))

            self.current_point = QPoint(x, y)
            self.selection_rect = QRect(self.start_point, self.current_point).normalized()

            # 更新显示以显示选择框
            if self.frame is not None:
                self.display_frame(self.frame)

    def mouse_release_event(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False

            # 获取图像区域内的坐标
            x, y = event.x() - self.display_offset[0], event.y() - self.display_offset[1]

            # 限制坐标在图像区域内
            x = max(0, min(x, self.display_size[0] - 1))
            y = max(0, min(y, self.display_size[1] - 1))

            self.current_point = QPoint(x, y)
            self.selection_rect = QRect(self.start_point, self.current_point).normalized()

            # 显示选择区域信息
            if not self.selection_rect.isEmpty() and self.frame is not None:
                # 将选择区域从显示坐标转换为原始视频坐标
                original_rect = self.scale_rect_to_original(self.selection_rect,
                                                            self.display_size,
                                                            self.original_size)
                print(f"选择区域: {original_rect}")

                # 更新显示
                self.display_frame(self.frame)

    def scale_rect_to_original(self, rect, display_size, original_size):
        """将显示坐标的矩形转换为原始视频坐标的矩形"""
        x_ratio = original_size[0] / display_size[0]
        y_ratio = original_size[1] / display_size[1]

        return QRect(
            int(rect.x() * x_ratio),
            int(rect.y() * y_ratio),
            int(rect.width() * x_ratio),
            int(rect.height() * y_ratio)
        )

    def scale_rect_to_pixmap(self, rect, original_size, display_size):
        """将原始视频坐标的矩形转换为显示坐标的矩形"""
        x_ratio = display_size[0] / original_size[0]
        y_ratio = display_size[1] / original_size[1]

        return QRect(
            int(rect.x() * x_ratio),
            int(rect.y() * y_ratio),
            int(rect.width() * x_ratio),
            int(rect.height() * y_ratio)
        )

    def reset_selection(self):
        """重置选择区域"""
        self.selection_rect = QRect()
        if self.frame is not None:
            self.display_frame(self.frame)

    def get_selected_region(self):
        """获取选择的区域，返回(x, y, width, height)元组"""
        if self.selection_rect.isEmpty() or self.frame is None:
            return None

        # 将选择区域从显示坐标转换为原始视频坐标
        original_rect = self.scale_rect_to_original(self.selection_rect,
                                                    self.display_size,
                                                    self.original_size)

        return (original_rect.x(), original_rect.y(),
                original_rect.width(), original_rect.height())
