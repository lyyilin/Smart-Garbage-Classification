from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QTableWidget, QTableWidgetItem, QPushButton, QWidget,
                              QTextEdit, QMessageBox, QProgressDialog)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
import json
import os
from datetime import datetime
from openai import OpenAI

class ReportGeneratorThread(QThread):
    """报告生成线程"""
    finished = Signal(str)  # 生成完成信号
    error = Signal(str)     # 错误信号

    def __init__(self, stats):
        super().__init__()
        self.stats = stats

    def run(self):
        try:
            report_prompt = f"""
            请根据以下垃圾分类数据生成一份环保报告：
            其他垃圾：{self.stats['其他垃圾']}次
            厨余垃圾：{self.stats['厨余垃圾']}次
            可回收物：{self.stats['可回收物']}次
            有害垃圾：{self.stats['有害垃圾']}次
            
            请包含以下内容：
            1. 用户的垃圾分类情况分析
            2. 环保贡献
            3. 改进建议
            4. 鼓励性的总结
            """

            client = OpenAI(
                api_key="fc2fd56184b9f72241cf2871ff6515524bf1f991",
                base_url="https://aistudio.baidu.com/llm/lmapi/v3",
            )

            chat_completion = client.chat.completions.create(
                messages=[
                    {'role': 'system', 'content': '你是一个环保专家，负责生成垃圾分类的环保报告。'},
                    {'role': 'user', 'content': report_prompt}
                ],
                model="ernie-3.5-8k",
            )

            report = chat_completion.choices[0].message.content
            self.finished.emit(report)

        except Exception as e:
            self.error.emit(str(e))

class HistoryWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("历史记录")
        self.setGeometry(200, 200, 1000, 600)
        self.init_ui()
        self.load_history()

    def init_ui(self):
        # 主布局
        main_layout = QHBoxLayout(self)
        
        # 左侧布局（历史记录）
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["时间", "垃圾类型", "图片", "操作"])
        self.table.setColumnWidth(0, 150)  # 时间列宽
        self.table.setColumnWidth(1, 100)  # 类型列宽
        self.table.setColumnWidth(2, 120)  # 图片列宽调整为适合100*100的图片
        self.table.setColumnWidth(3, 80)   # 操作列宽
        left_layout.addWidget(self.table)

        # 统计信息
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        self.stats_label = QLabel()
        stats_layout.addWidget(self.stats_label)
        
        # 生成报告按钮
        self.report_button = QPushButton("生成环保报告")
        self.report_button.clicked.connect(self.generate_report)
        self.report_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        stats_layout.addWidget(self.report_button)
        
        left_layout.addWidget(stats_widget)
        
        # 右侧布局（环保报告）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 报告标题
        report_title = QLabel("环保分析报告")
        report_title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 4px;
            }
        """)
        report_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(report_title)

        # 报告显示区域
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        self.report_text.setPlaceholderText('点击"生成环保报告"按钮获取您的个性化环保分析...')
        right_layout.addWidget(self.report_text)

        # 设置左右布局的比例为4:3
        main_layout.addWidget(left_widget, 4)
        main_layout.addWidget(right_widget, 3)

    def load_history(self):
        """加载历史记录"""
        if os.path.exists("history.json"):
            with open("history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []

        self.table.setRowCount(len(history))
        for i, record in enumerate(history):
            # 设置行高为110（图片高度+边距）
            self.table.setRowHeight(i, 110)
            
            # 时间
            time_item = QTableWidgetItem(record["time"])
            time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, time_item)
            
            # 类型
            type_item = QTableWidgetItem(record["type"])
            type_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, type_item)
            
            # 图片
            if os.path.exists(record["image"]):
                image_container = QWidget()
                image_layout = QHBoxLayout(image_container)
                image_layout.setContentsMargins(5, 5, 5, 5)
                
                label = QLabel()
                pixmap = QPixmap(record["image"])
                scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(scaled_pixmap)
                label.setStyleSheet("border: 1px solid #bdc3c7; border-radius: 4px;")
                
                image_layout.addWidget(label, alignment=Qt.AlignCenter)
                self.table.setCellWidget(i, 2, image_container)
            
            # 删除按钮
            delete_container = QWidget()
            delete_layout = QHBoxLayout(delete_container)
            delete_layout.setContentsMargins(5, 5, 5, 5)
            
            delete_btn = QPushButton("删除")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            delete_btn.clicked.connect(lambda checked, row=i: self.delete_record(row))
            
            delete_layout.addWidget(delete_btn)
            self.table.setCellWidget(i, 3, delete_container)

        self.update_statistics()

    def generate_report(self):
        """生成环保报告"""
        try:
            # 读取历史记录
            with open("history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
            
            # 统计数据
            stats = {
                "其他垃圾": 0,
                "厨余垃圾": 0,
                "可回收物": 0,
                "有害垃圾": 0
            }
            for record in history:
                stats[record["type"]] += 1

            # 创建进度对话框
            progress = QProgressDialog("正在生成环保报告...", "取消", 0, 0, self)
            progress.setWindowTitle("请稍候")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            # 创建报告生成线程
            self.report_thread = ReportGeneratorThread(stats)
            self.report_thread.finished.connect(self.on_report_generated)
            self.report_thread.error.connect(self.on_report_error)
            self.report_thread.finished.connect(progress.close)
            self.report_thread.error.connect(progress.close)
            
            # 启动线程
            self.report_thread.start()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"准备生成报告失败：{str(e)}")

    def on_report_generated(self, report):
        """报告生成完成的回调"""
        # 在文本框中显示报告
        self.report_text.setPlainText(report)
        
        # 保存报告
        report_file = f"环保报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        QMessageBox.information(self, "成功", f"环保报告已生成并保存：{report_file}")

    def on_report_error(self, error_msg):
        """报告生成错误的回调"""
        QMessageBox.warning(self, "错误", f"生成报告失败：{error_msg}")

    def delete_record(self, row):
        """删除记录"""
        with open("history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
        
        # 删除图片文件
        if os.path.exists(history[row]["image"]):
            os.remove(history[row]["image"])
        
        # 删除记录
        del history[row]
        
        # 保存更新后的历史记录
        with open("history.json", "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        # 刷新显示
        self.load_history()

    def update_statistics(self):
        """更新统计信息"""
        if os.path.exists("history.json"):
            with open("history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
            
            stats = {
                "其他垃圾": 0,
                "厨余垃圾": 0,
                "可回收物": 0,
                "有害垃圾": 0
            }
            
            for record in history:
                stats[record["type"]] += 1
            
            stats_text = "分类统计：  "
            for type_, count in stats.items():
                stats_text += f"{type_}: {count}次  "
            
            self.stats_label.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    font-size: 14px;
                    padding: 5px;
                }
            """)
            self.stats_label.setText(stats_text)
 