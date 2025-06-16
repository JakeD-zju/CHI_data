# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 09:22:13 2025

@author: satellite
"""

from fileloadCHI import FileLoaderCHI
from folderselector import FolderSelector
import pandas as pd
import numpy as np
# 如果只是需要一个NaN值, 可以选择math.nan.
# 如果在数据科学项目中使用 pandas, 推荐使用 np.nan
import os

class MainApp:
    def __init__(self):
        self.fl = FileLoaderCHI()
        self.folder_selector = FolderSelector(self.process_data)
        self.folder_selector.mainloop()

    def process_data(self):
        try:
            all_subfolders, button_text = self.get_folder_and_button_info()
            for subfolder in all_subfolders:
                file_timestamps = self.get_file_timestamps(subfolder)
                sorted_files = sorted(file_timestamps, key=lambda x: x[1])
                n, data, plt_name = self.process_sorted_files(sorted_files, subfolder, button_text)
                if n > 0:
                    self.save_data_to_csv(data, subfolder, button_text)
                    self.folder_selector.plot_in_window(n, plt_name, data)
        except Exception as e:
            print(f"Error in process_data: {e}")
        finally:
            # 清除数据
            self.folder_selector.selected_paths = []
            self.folder_selector.subfolders = {}

    def get_folder_and_button_info(self):
        all_subfolders = self.folder_selector.get_all_subfolders()
        button_text = self.folder_selector.button_text
        # print(all_subfolders)
        return all_subfolders, button_text

    def get_file_timestamps(self, subfolder):
        file_timestamps = []
        for f in os.listdir(subfolder):
            if f.endswith('.txt') or f.endswith('.csv'):
                file_path = os.path.join(subfolder, f)
                timestamp = self.fl.get_file_timestamp(file_path)
                if timestamp is not None:
                    file_timestamps.append((f, timestamp))
        return file_timestamps

    def process_sorted_files(self, sorted_files, subfolder, button_text):
        n = 0
        data = {}
        max_length = 0  # 用于记录最大的数据长度
        for name, _ in sorted_files:
            prefix = os.path.splitext(name)[0]
            fname = os.path.join(subfolder, name)
            
            try:
                x, y, plt_name = self.fl.get_data(button_text, fname)
                data[prefix + '_x'] = x
                data[prefix + '_y'] = y
                n += 1
                max_length = max(max_length, len(x))
                
            except Exception as e:
                print(f"Error processing {fname}: {e}\n")
                continue

        # 对所有数据进行填充
        for key in data:
            current_length = len(data[key])
            if current_length < max_length:
                # 用 np.nan 填充到最大长度, 使用list将np数组转化为列表操作
                # 否则会导致操作失败, np数组的+是元素相加而非列表的拼接
                data[key] = list(data[key]) + [np.nan] * (
                    max_length - current_length)
        
        return n, data, plt_name

    def save_data_to_csv(self, data, subfolder, button_text):
        df = pd.DataFrame(data)
        # 仅保留第一个x轴时启用（EIS或ZView数据强制保留所有x轴）
        if self.folder_selector.as_one and button_text != 'EIS' and button_text != 'ZView':
            df = df.iloc[:, [0, 1] + list(range(3, df.shape[1], 2))]
        df.to_csv(os.path.join(subfolder, f'{button_text}_merged.txt'),
                  sep='\t', index=False)

if __name__ == "__main__":
    app = MainApp()
