import sys
import cv2
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QLabel, QMessageBox, 
                              QDialog, QGroupBox, QCheckBox, QSlider, QLineEdit, 
                              QSpinBox, QFormLayout, QDialogButtonBox)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QImage, QPixmap
from paddlex import create_model
import paho.mqtt.client as mqtt
import numpy as np
import time
import pyttsx3
from playsound import playsound
import os
import threading
import json
from datetime import datetime
import shutil

class HoverButton(QPushButton):
    def __init__(self, text, parent=None, size_factor=1.0):
        super().__init__(text, parent)
        self.size_factor = size_factor
        self.default_size = QSize(int(100 * size_factor), int(40 * size_factor))
        self.hover_size = QSize(int(110 * size_factor), int(44 * size_factor))
        self.setFixedSize(self.default_size)

        # 创建动画对象
        self.animation = QPropertyAnimation(self, b"size")
        self.animation.setDuration(200)  # 200ms的动画时长
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def enterEvent(self, event):
        self.animation.setStartValue(self.size())
        self.animation.setEndValue(self.hover_size)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.setStartValue(self.size())
        self.animation.setEndValue(self.default_size)
        self.animation.start()
        super().leaveEvent(event)

class GarbageClassificationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("垃圾分类识别系统")
        self.setGeometry(100, 100, 1200, 600)

        # 初始化语音引擎
        self.engine = pyttsx3.init()
        # 设置语音速率
        self.engine.setProperty('rate', 200)
        # 设置音量
        self.engine.setProperty('volume', 1.0)
        # 设置声音为女声
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "chinese" in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                break

        # 语音线程锁
        self.voice_lock = threading.Lock()
        
        # MQTT配置
        self.MQTT_BROKER = "1.94.212.189"
        self.MQTT_PORT = 1883
        self.MQTT_TOPIC = "garbage/category"
        self.mqtt_client = None

        # 垃圾类别映射
        self.garbage_map = {
            "其他垃圾": "other",
            "厨余垃圾": "kitchen",
            "可回收物": "recyclable",
            "有害垃圾": "harmful"
        }

        # 加载模型
        self.model = create_model(r"F:\myitem2\paddle_test\garbage\inference")

        # 初始化UI
        self.init_ui()
        
        # 初始化摄像头
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 30ms刷新一次

        # 存储当前帧
        self.current_frame = None

    def play_voice_thread(self, text):
        """在新线程中生成并播放语音"""
        with self.voice_lock:  # 使用锁确保同一时间只有一个语音在播放
            try:
                # 生成wav文件
                audio_file = f"garbage_type_{threading.get_ident()}.wav"
                self.engine.save_to_file(text, audio_file)
                self.engine.runAndWait()
                
                # 播放语音
                playsound(audio_file)
                
                # 删除临时音频文件
                try:
                    os.remove(audio_file)
                except:
                    pass
            except Exception as e:
                print(f"语音播放错误: {str(e)}")

    def play_voice(self, text):
        """启动语音播放线程"""
        thread = threading.Thread(target=self.play_voice_thread, args=(text,))
        thread.daemon = True  # 设置为守护线程，随主线程退出而退出
        thread.start()

    def connect_mqtt(self):
        """尝试连接MQTT服务器"""
        try:
            if self.mqtt_client is None:
                self.mqtt_client = mqtt.Client()
                self.mqtt_client.connect(self.MQTT_BROKER, self.MQTT_PORT, 5)  # 设置超时时间为5秒
            return True
        except Exception as e:
            QMessageBox.warning(self, "连接错误", f"无法连接到MQTT服务器: {str(e)}")
            return False

    def send_mqtt_message(self, message):
        """发送MQTT消息"""
        try:
            if self.connect_mqtt():
                self.mqtt_client.publish(self.MQTT_TOPIC, message)
                print(f"已发送MQTT消息: {message}")
        except Exception as e:
            print(f"发送MQTT消息失败: {str(e)}")
        
    def init_ui(self):
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QLabel {
                color: #2c3e50;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2573a7;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)  # 增加组件间距
        main_layout.setContentsMargins(20, 20, 20, 20)  # 设置边距

        # 左侧布局 - 摄像头预览
        left_widget = QWidget()
        left_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 10px;
            }
        """)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        # 摄像头标题
        camera_title = QLabel("实时预览")
        camera_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px 0;
            }
        """)
        left_layout.addWidget(camera_title)

        # 摄像头预览区域
        camera_container = QWidget()
        camera_container.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                border-radius: 8px;
                padding: 2px;
            }
        """)
        camera_layout = QVBoxLayout(camera_container)
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(640, 480)
        self.camera_label.setStyleSheet("border-radius: 8px;")
        camera_layout.addWidget(self.camera_label)
        left_layout.addWidget(camera_container)
        
        # 按钮区域
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setSpacing(15)  # 增加按钮间距

        # 识别按钮 (1.3倍大小)
        self.detect_button = HoverButton("识别", size_factor=1.3)
        self.detect_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        self.detect_button.clicked.connect(self.detect_garbage)

        # 功能按钮
        self.help_button = HoverButton("分类指南")
        self.help_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 14px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.help_button.clicked.connect(self.show_guide)

        self.history_button = HoverButton("历史记录")
        self.history_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-size: 14px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.history_button.clicked.connect(self.show_history)

        self.settings_button = HoverButton("设置")
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                font-size: 14px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        """)
        self.settings_button.clicked.connect(self.show_settings)

        # 添加所有按钮到布局
        buttons_layout.addWidget(self.detect_button, alignment=Qt.AlignCenter)
        buttons_layout.addWidget(self.help_button, alignment=Qt.AlignCenter)
        buttons_layout.addWidget(self.history_button, alignment=Qt.AlignCenter)
        buttons_layout.addWidget(self.settings_button, alignment=Qt.AlignCenter)

        # 将按钮区域添加到左侧布局
        left_layout.addWidget(buttons_widget)

        # 右侧布局 - 识别结果
        right_widget = QWidget()
        right_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 10px;
            }
        """)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(15, 15, 15, 15)

        # 结果标题
        result_title = QLabel("识别结果")
        result_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px 0;
            }
        """)
        right_layout.addWidget(result_title)

        # 结果标签
        self.result_label = QLabel("等待识别...")
        self.result_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #7f8c8d;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)
        self.result_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.result_label)

        # 结果图片容器
        result_image_container = QWidget()
        result_image_container.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                border-radius: 8px;
                padding: 2px;
            }
        """)
        result_image_layout = QVBoxLayout(result_image_container)
        self.result_image_label = QLabel()
        self.result_image_label.setFixedSize(640, 480)
        self.result_image_label.setStyleSheet("""
            QLabel {
                border-radius: 8px;
                background-color: #ecf0f1;
            }
        """)
        self.result_image_label.setAlignment(Qt.AlignCenter)
        result_image_layout.addWidget(self.result_image_label)
        right_layout.addWidget(result_image_container)

        # 添加到主布局
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

        # 添加状态栏
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: white;
                color: #7f8c8d;
            }
        """)
        self.statusBar().showMessage("系统就绪")

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            # 转换图像格式用于显示
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.camera_label.setPixmap(pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio))

    def detect_garbage(self):
        if self.current_frame is None:
            return

        try:
            # 保存当前帧为临时文件
            temp_path = "temp_frame.jpg"
            cv2.imwrite(temp_path, self.current_frame)

            # 进行预测
            result = self.model.predict(temp_path, batch_size=1)

            for res in result:
                label = res['label_names'][0].split("/")[0]
                print(f"检测到垃圾类别: {label}")
                self.result_label.setText(f"检测到垃圾类别: {label}")
                
                # 在新线程中播放语音提示
                voice_text = f"这是{label}，请放入{label}桶"
                self.play_voice(voice_text)
                
                # 发送MQTT消息
                if label in self.garbage_map:
                    message = self.garbage_map[label]
                    self.send_mqtt_message(message)

                # 显示识别结果图像
                output_path = "output_frame.jpg"
                res.save_to_img(output_path)
                result_pixmap = QPixmap(output_path)
                self.result_image_label.setPixmap(
                    result_pixmap.scaled(self.result_image_label.size(), Qt.KeepAspectRatio))

                # 保存历史记录
                self.save_to_history(label, output_path)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"识别过程出错: {str(e)}")

    def closeEvent(self, event):
        # 程序关闭时释放资源
        self.cap.release()
        if self.mqtt_client is not None:
            try:
                self.mqtt_client.disconnect()
            except:
                pass
        # 关闭语音引擎
        self.engine.stop()
        event.accept()

    def show_history(self):
        """显示历史记录窗口"""
        from history_window import HistoryWindow
        history_window = HistoryWindow(self)
        history_window.exec()

    def save_to_history(self, label, image_path):
        """保存识别记录到历史"""
        # 创建历史记录目录
        if not os.path.exists("history_images"):
            os.makedirs("history_images")
        
        # 保存图片副本
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_image = f"history_images/image_{timestamp}.jpg"
        shutil.copy2(image_path, history_image)
        
        # 读取现有历史记录
        if os.path.exists("history.json"):
            with open("history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []
        
        # 添加新记录
        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": label,
            "image": history_image
        }
        history.append(record)
        
        # 保存历史记录
        with open("history.json", "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def show_guide(self):
        """显示垃圾分类指南"""
        guide_text = """
        垃圾分类指南：

        1. 可回收物
        - 废纸张、废塑料、废玻璃、废金属、废织物等
        - 特点：适合回收利用的垃圾

        2. 有害垃圾
        - 废电池、废灯管、废药品、废油漆等
        - 特点：对人体健康或环境有害的垃圾

        3. 厨余垃圾
        - 剩菜剩饭、骨头、菜根菜叶等
        - 特点：易腐烂的生物质垃圾

        4. 其他垃圾
        - 砖瓦陶瓷、渣土、卫生纸等
        - 特点：除上述三种之外的其他垃圾
        """
        QMessageBox.information(self, "垃圾分类指南", guide_text)

    def show_settings(self):
        """显示设置对话框"""
        # 创建设置对话框
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("设置")
        settings_dialog.setGeometry(300, 300, 400, 300)
        
        # 创建布局
        layout = QVBoxLayout(settings_dialog)
        
        # 语音设置
        voice_group = QGroupBox("语音设置")
        voice_layout = QVBoxLayout()
        
        # 语音开关
        self.voice_enabled = QCheckBox("启用语音提示")
        self.voice_enabled.setChecked(True)
        voice_layout.addWidget(self.voice_enabled)
        
        # 语音速率滑块
        rate_layout = QHBoxLayout()
        rate_label = QLabel("语音速率:")
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setMinimum(100)
        self.rate_slider.setMaximum(300)
        self.rate_slider.setValue(200)
        self.rate_slider.valueChanged.connect(self.update_voice_rate)
        rate_layout.addWidget(rate_label)
        rate_layout.addWidget(self.rate_slider)
        voice_layout.addLayout(rate_layout)
        
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)
        
        # MQTT设置
        mqtt_group = QGroupBox("MQTT设置")
        mqtt_layout = QFormLayout()
        
        self.mqtt_broker_input = QLineEdit(self.MQTT_BROKER)
        self.mqtt_port_input = QSpinBox()
        self.mqtt_port_input.setRange(1, 65535)
        self.mqtt_port_input.setValue(self.MQTT_PORT)
        
        mqtt_layout.addRow("服务器地址:", self.mqtt_broker_input)
        mqtt_layout.addRow("端口:", self.mqtt_port_input)
        
        mqtt_group.setLayout(mqtt_layout)
        layout.addWidget(mqtt_group)
        
        # 确定和取消按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, settings_dialog)
        buttons.accepted.connect(settings_dialog.accept)
        buttons.rejected.connect(settings_dialog.reject)
        layout.addWidget(buttons)
        
        # 显示对话框
        if settings_dialog.exec() == QDialog.Accepted:
            # 保存设置
            self.MQTT_BROKER = self.mqtt_broker_input.text()
            self.MQTT_PORT = self.mqtt_port_input.value()
            # 断开现有连接，以便使用新设置重新连接
            if self.mqtt_client:
                self.mqtt_client.disconnect()
                self.mqtt_client = None

    def update_voice_rate(self, value):
        """更新语音速率"""
        self.engine.setProperty('rate', value)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GarbageClassificationApp()
    window.show()
    sys.exit(app.exec())