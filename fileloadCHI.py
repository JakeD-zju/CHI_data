# # -*- coding: utf-8 -*-
# """
# Created on Tue Feb 18 10:48:33 2025

import pandas as pd
from datetime import datetime
import os


class FileLoaderCHI:
    def __init__(self):
        """
        初始化 FileLoaderCHI 类的实例。
        """
        pass

    def get_file_timestamp(self, filename):
        """
        获取指定文件的时间戳。

        参数:
        filename (str): 要处理的文件的路径。

        返回:
        datetime.datetime: 如果成功获取到时间戳，则返回对应的 datetime 对象；
                           若文件不存在、解码失败或文件为空等情况，则返回 None。
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                # 读取文件的第一行并去除首尾空格
                time_string = f.readline().strip()
                if not time_string:
                    print(f"文件 {filename} 为空或第一行为空。")
                    return None
                #处理5月数据
                time_string = time_string.replace("May", "May.")
                #处理6月数据
                time_string = time_string.replace("June", "Jun.")
                # 将时间字符串解析为 datetime 对象                
                return datetime.strptime(time_string, "%b. %d, %Y %H:%M:%S")
        except FileNotFoundError:
            print(f"文件 {filename} 未找到。")
            return None
        except UnicodeDecodeError:
            print(f"文件 {filename} 解码失败。")
            return None
        except Exception as e:
            print(f"读取文件 {filename} 时出错：{str(e)}")
            return None

    def _find_index_and_key(self, file):
        """
        辅助方法：在文件中查找特定行并确定文件类型。

        参数:
        file (file object): 打开的文件对象。

        返回:
        tuple: 包含行索引和文件类型的元组。
        """
        keys = ['EIS', 'Tafel', 'CV', 'CA', 'CP']
        lines = file.readlines()
        for i, line in enumerate(lines):
            if line.startswith('Freq/Hz'):
                return i, keys[0]
            elif line.startswith('Potential/V, Current/A, log(i/A)'):
                return i, keys[1]
            elif line.startswith('Potential/V'):
                return i, keys[2]
            elif line.startswith('Time/sec, Current/A'):
                return i, keys[3]
            elif line.startswith('Time/sec, Potential/V'):
                return i, keys[4]
        return None, None

    def _read_data_from_file(self, file, header_index, usecols):
        """
        辅助方法：从文件中读取数据并进行处理。

        参数:
        filename (str): 要处理的文件的路径。
        header_index (int): 数据的表头所在行索引。
        usecols (list): 要读取的列的索引列表。

        返回:
        pandas.DataFrame: 处理后的数据 DataFrame。
        """
        data = pd.read_csv(file, sep=',', header=header_index, usecols=usecols, skip_blank_lines=False)
        return data.dropna()

    def get_eis(self, filename, min_freq=None, max_freq=None):
        """
        读取 EIS 数据。

        参数:
        filename (str): 要处理的 EIS 文件的路径。
        min_freq (float, optional): 最小频率，用于筛选数据。默认为 None。
        max_freq (float, optional): 最大频率，用于筛选数据。默认为 None。

        返回:
        tuple: 包含频率和阻抗复数的元组；如果文件不是 EIS 数据，则返回 None。
        """
        with open(filename, mode="r", encoding="utf-8-sig") as f:
            index, key = self._find_index_and_key(f)
            if key != 'EIS':
                print('非EIS数据\n')
                return None
            f.seek(0)
            data = self._read_data_from_file(filename, index, [0, 1, 2])

        freq = data['Freq/Hz'].values.copy()
        z_real = data[' Z\'/ohm'].values.copy()
        z_imag = data[' Z\"/ohm'].values.copy()
        z = z_real + 1j * z_imag

        if min_freq is not None:
            index = freq >= min_freq
            freq = freq[index]
            z = z[index]

        if max_freq is not None:
            index = freq <= max_freq
            freq = freq[index]
            z = z[index]

        return freq, z

    def get_ZView(self, filename):
        """
        处理 EIS 数据并保存为 ZView 格式的文件。

        参数:
        filename (str): 要处理的 EIS 文件的路径。

        返回:
        tuple: 包含实部阻抗、虚部阻抗和绘图名称的元组；如果文件不是 EIS 数据，则返回 None。
        """
        with open(filename, mode="r", encoding="utf-8-sig") as f:
            index, key = self._find_index_and_key(f)
            if key != 'EIS':
                print('非EIS数据\n')
                return None
            f.seek(0)
            data = self._read_data_from_file(filename, index, [0, 1, 2])

        freq = data['Freq/Hz'].values.copy()
        z_real = data[' Z\'/ohm'].values.copy()
        z_imag = data[' Z\"/ohm'].values.copy()

        zv = pd.DataFrame({
            'Freq': freq,
           'real': z_real,
            'imag': z_imag
        })
        # 保存为 ZView 格式的文件
        zv.to_csv(os.path.splitext(filename)[0] + '_ZView.txt', sep='\t', index=False, header=False)
        plt_name = ['z_real/Ω', 'z_imag/Ω']
        z_imag = z_imag * -1
        return z_real, z_imag, plt_name

    def get_CV(self, filename):
        """
        读取 CV 或 LSV 数据。

        参数:
        filename (str): 要处理的 CV 或 LSV 文件的路径。

        返回:
        tuple: 包含电位、电流和绘图名称的元组；如果文件不是 CV 或 LSV 数据，则返回 None。
        """
        with open(filename, mode="r", encoding="utf-8-sig") as f:
            index, key = self._find_index_and_key(f)
            if key != 'CV':
                print('非CV或LSV数据\n')
                return None
            f.seek(0)
            data = self._read_data_from_file(filename, index, [0, 1])

        pot = data['Potential/V'].values.copy()
        cur = data[' Current/A'].values.copy()
        plt_name = data.columns.tolist()
        return pot, cur, plt_name

    def get_Tafel(self, filename):
        """
        读取 Tafel 数据。

        参数:
        filename (str): 要处理的 Tafel 文件的路径。

        返回:
        tuple: 包含电位、对数电流和绘图名称的元组；如果文件不是 Tafel 数据，则返回 None。
        """
        with open(filename, mode="r", encoding="utf-8-sig") as f:
            index, key = self._find_index_and_key(f)
            if key != 'Tafel':
                print('非Tafel数据\n')
                return None
            f.seek(0)
            data = self._read_data_from_file(filename, index, [0, 2])

        pot = data['Potential/V'].values.copy()
        cur = data[' log(i/A)'].values.copy()
        plt_name = data.columns.tolist()
        return pot, cur, plt_name

    def get_CA(self, filename):
        """
        读取 CA 数据。

        参数:
        filename (str): 要处理的 CA 文件的路径。

        返回:
        tuple: 包含时间、电流和绘图名称的元组；如果文件不是 CA 数据，则返回 None。
        """
        with open(filename, mode="r", encoding="utf-8-sig") as f:
            index, key = self._find_index_and_key(f)
            if key != 'CA':
                print('非CA数据\n')
                return None
            f.seek(0)
            data = self._read_data_from_file(filename, index, [0, 1])

        t = data['Time/sec'].values.copy()
        cur = data[' Current/A'].values.copy()
        plt_name = data.columns.tolist()
        return t, cur, plt_name

    def get_CP(self, filename):
        """
        读取 CP 数据。

        参数:
        filename (str): 要处理的 CP 文件的路径。

        返回:
        tuple: 包含时间、电位和绘图名称的元组；如果文件不是 CP 数据，则返回 None。
        """
        with open(filename, mode="r", encoding="utf-8-sig") as f:
            index, key = self._find_index_and_key(f)
            if key != 'CP':
                print('非CP数据\n')
                return None
            f.seek(0)
            data = self._read_data_from_file(filename, index, [0, 1])

        t = data['Time/sec'].values.copy()
        v = data[' Potential/V'].values.copy()
        plt_name = data.columns.tolist()
        return t, v, plt_name

    function_mapping = {
        'EIS': get_ZView,
        'ZView': get_ZView,
        'CV': get_CV,
        'CA': get_CA,
        'CP': get_CP,
        'Tafel': get_Tafel,
        'LSV': get_CV,
    }

    def get_data(self, button_text, filename, *args, **kwargs):
        """
        根据文件类型和文件名获取相应的数据。

        参数:
        button_text (str): 文件类型，如 'EIS', 'CV' 等。
        filename (str): 要处理的文件的路径。
        *args: 可变位置参数。
        **kwargs: 可变关键字参数。

        返回:
        tuple: 处理后的数据元组；如果文件类型不支持，则返回 None。
        """
        if button_text in self.function_mapping:
            func = getattr(self, self.function_mapping[button_text].__name__)
            return func(filename, *args, **kwargs)
        else:
            print(f"不支持的文件类型: {button_text}")
            return None
