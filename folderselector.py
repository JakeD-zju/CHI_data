# -*- coding: utf-8 -*-
"""
Created on Wed Mar 12 13:55:35 2025

@author: satellite
"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askdirectory
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

plt.rcParams['font.family'] = 'Microsoft YaHei'  # 使用微软雅黑字体

class FolderSelector(tk.Tk):
    def __init__(self, process_callback, show_buttons=None):
        super().__init__()
        self.geometry("1500x700")  # 调整窗口大小以容纳绘图区域
        self.title("工作站数据处理")
        self.selected_paths = []
        # self.selected_paths = ''
        self.subfolders = {}  # 用于存储每个路径下的一级子文件夹
        self.button_text = None  # 用于存储当前选择的按钮文本
        self.as_one = False  # 存储一个布尔值
        self.flag_text = '仅保留第一个x轴'
        self.process_callback = process_callback
        self.canvas = None  # 用于存储绘图的 canvas

        # 创建左侧框架用于放置按钮和标签
        self.left_frame = tk.Frame(self)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.path_label = tk.Label(self.left_frame, text="工作站数据转换\n请先将数据存储为txt或者csv格式",
                                   wraplength=700)
        self.path_label.pack(pady=10)

        self.add_folder_button = ttk.Button(self.left_frame, text="选择文件夹",
                                            command=self.add_folder, width=40)
        self.add_folder_button.pack(pady=10)

        # 创建用于显示所选路径的标签
        self.path_label = tk.Label(self.left_frame, text="未选择文件夹", wraplength=700)
        self.path_label.pack(pady=10)
        
        # 选择是否只保留一个x轴
        self.as_one_button = ttk.Button(self.left_frame, text=f"{self.flag_text}: {self.as_one}",
                                        command=self.as_one_fuc, width=40)
        self.as_one_button.pack(pady=10)
        
        # 默认显示的按钮列表
        default_buttons = ["EIS", "ZView", "CA", "CV", "Tafel", "CP", "LSV"]
        if show_buttons is None:
            show_buttons = default_buttons

            # 数据类型选择提示
            self.button_label = tk.Label(self.left_frame, text="请选择数据类型")
            self.button_label.pack(pady=10)

        for button_name in show_buttons:
            self.create_button(button_name)

        self.end_button = ttk.Button(self.left_frame, text="结束选择", command=self.on_end, width=40)
        self.end_button.pack(pady=10)
        # 创建右侧框架用于放置绘图区域
        self.right_frame = tk.Frame(self)
        self.right_frame.pack(side=tk.RIGHT, padx=10, pady=10)

    def create_button(self, key):
        """动态创建按钮并传递不同的值"""
        button = ttk.Button(self.left_frame, text=key, command=lambda: self.key_select(key))
        button.pack(pady=10)

    def add_folder(self):
        folder_selected = askdirectory()
        if folder_selected:
            self.selected_paths.append(folder_selected)
            # self.selected_paths=folder_selected
            self.update_subfolders(folder_selected)
            # 更新显示所选路径的标签内容
            self.path_label.config(text="\n".join(self.selected_paths))

    def as_one_fuc(self):
        """更新是否仅保留一列x轴"""
        self.as_one = not self.as_one  # 更新选择的按钮文本
        self.as_one_button.config(text=f"{self.flag_text}: {self.as_one}")

    def key_select(self, button_text):
        """根据点击的按钮返回不同的值"""
        self.button_label.config(text=f"选择了{button_text}格式")
        self.button_text = button_text  # 更新选择的按钮文本

    def update_subfolders(self, folder_path):
        """更新存储的一级子文件夹信息，如果没有子文件夹，则返回所选择的文件夹"""
        subfolders = [name for name in os.listdir(folder_path)
                      if os.path.isdir(os.path.join(folder_path, name))]
        self.subfolders[folder_path] = subfolders or [folder_path]

    def get_all_subfolders(self):
        """获取所有存储的一级子文件夹路径"""
        all_subfolders_paths = []
        for path, subfolders in self.subfolders.items():
            for subfolder in subfolders:
                subfolder_path = os.path.join(path, subfolder)
                all_subfolders_paths.append(subfolder_path)
        return all_subfolders_paths

    def on_end(self):
        """结束选择，调用处理函数"""
        self.process_callback()
        # self.selected_paths = []
        # self.subfolders = {}

    def plot_in_window(self, n, plt_name, data):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()  # 销毁之前的绘图 canvas
        """在窗口内绘图"""
        fig = plt.Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)

        # 给每个文件的数据选择不同的颜色
        colors = plt.cm.tab20(np.linspace(0, 1, n))
        # y轴坐标自适应
        y_data_list = []
        for i in range(0, 2 * n, 2):
            key1, value1 = list(data.items())[i]
            key2, value2 = list(data.items())[i + 1]

            x = value1
            y = value2
            y_data_list.extend(y)
            ax.plot(x, y, label=key2.split('_y')[0], color=colors[i // 2])
            
        # 找到合适的缩放因子
        max_abs_y = max([abs(y) for y in y_data_list])
        if max_abs_y == 0:
            scale_factor = 1
            scale_label = ''
        else:
            power = int(np.floor(np.log10(max_abs_y) / 3) * 3)
            scale_factor = 10 ** power
            if power == 3:
                scale_label = 'k'
            elif power == 6:
                scale_label = 'M'
            elif power == -3:
                scale_label = 'm'
            elif power == -6:
                scale_label = 'μ'
            elif power == -9:
                scale_label = 'n'
            else:
                scale_label = ''

        # 自定义 y 轴刻度标签
        def format_func(value, tick_number):
            scaled_value = value / scale_factor
            return f'{scaled_value:.1f}{scale_label}'

        ax.yaxis.set_major_formatter(plt.FuncFormatter(format_func))

        # 添加标签、标题和图例
        ax.set_xlabel(plt_name[0])
        ax.set_ylabel(f'{plt_name[1]}')
        ax.set_title('曲线一览')
        ax.legend()
        ax.grid(True)

        # 在右侧框架中嵌入绘图
        self.canvas = FigureCanvasTkAgg(fig, master=self.right_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()
