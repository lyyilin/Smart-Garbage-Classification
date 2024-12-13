<div align="center">
    <img src="assets/logo.png" alt="HOOK Team Logo" width="100"/>
</div>

# 智能垃圾分类系统  (Smart Garbage Classification System)

一个基于深度学习的实时垃圾分类识别系统，集成了计算机视觉、语音提示和物联网控制功能。

## 功能特点

- 🎯 实时垃圾分类识别
  - 支持四类垃圾：可回收物、有害垃圾、厨余垃圾、其他垃圾
  - 基于PaddleX深度学习框架
  - 实时摄像头画面显示

- 🗣️ 智能语音提示
  - 中文语音播报识别结果
  - 可调节语音速率
  - 支持开关语音功能

- 🎛️ IoT控制集成
  - MQTT协议通信
  - 自动控制垃圾桶开关
  - 可配置服务器参数

- 📊 数据统计分析
  - 历史记录管理
  - 分类数据统计
  - AI生成环保报告

## 系统要求

- Python 3.10+
- PySide6
- OpenCV
- PaddleX
- pyttsx3
- MQTT客户端
- 其他依赖见requirements.txt

## 安装说明

1. 克隆仓库 
```bash
git clone https://github.com/your-username/garbage-classification.git
cd garbage-classification
```


2. 安装依赖
```bash
pip install -r requirements.txt
```


3. 配置环境变量
```bash
pip install -r requirements.txt


Linux/Mac
export AI_STUDIO_API_KEY="your_api_key"

Windows
set AI_STUDIO_API_KEY="your_api_key"
```

## 使用说明

1. 运行主程序
```bash
python predict.py
```

2. 硬件控制程序（ESP32）
```bash
上传garbage_control.py到ESP32
```

3. 配置说明
- 修改MQTT服务器地址和端口
- 调整舵机控制参数
- 配置摄像头参数

## 项目结构
```
garbage-classification/
├── assets/ # 静态资源文件
│ └── logo.png # 项目logo
├── history_images/ # 历史识别图片存储
│ └── .jpg # 识别结果图片
├── inference/ # 模型文件目录
│ ├── model.pdmodel # 预训练模型文件
│ └── model.pdiparams # 模型参数文件
├── predict.py # 主程序（GUI界面和识别逻辑）
├── garbage_control.py # ESP32硬件控制程序
├── history_window.py # 历史记录窗口
├── requirements.txt # 项目依赖
├── README.md # 项目说明文档
└── .gitignore # Git忽略文件配置
```

## 系统架构

- 前端界面：PySide6
- 视觉识别：PaddleX
- 语音合成：pyttsx3
- 硬件控制：ESP32 + MicroPython
- 通信协议：MQTT

## 开发计划

- [1] 添加更多垃圾类别支持
- [2] 优化识别准确率
- [3] 添加用户管理功能
- [4] 开发移动端应用
- [5] 云端数据分析

## 贡献指南

欢迎提交问题和改进建议！提交代码请遵循以下步骤：

1. Fork 本仓库
2. 创建新的分支
3. 提交更改
4. 发起 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 作者：HOOK团队
- 邮箱：1447570331@qq.com
- 飞桨主页：https://aistudio.baidu.com/personalcenter/thirdview/2945966

## 致谢
- 飞桨社区提供的算力资源支持
- PySide6提供的GUI开发工具
- 百度文心大模型提供的AI能力

## 项目状态

![GitHub stars](https://img.shields.io/github/stars/username/repo)
![GitHub forks](https://img.shields.io/github/forks/username/repo)
![GitHub issues](https://img.shields.io/github/issues/username/repo)
![GitHub license](https://img.shields.io/github/license/username/repo)