import os  # 导入操作系统相关的模块
import numpy as np  # 导入 NumPy，用于数值计算
import matplotlib.pyplot as plt  # 导入 Matplotlib，用于绘图
from hybdrt.models import DRT  # 从库中导入 DRT 模型
from fileloadCHI import FileLoaderCHI  # 导入文件加载模块
import pandas as pd
from folderselector import FolderSelector

class MainApp:
    def __init__(self):
        self.fl = FileLoaderCHI()
        self.folder_selector = FolderSelector(self.process_data, show_buttons = [])
        self.folder_selector.flag_text = '是否开启DOP'
        self.folder_selector.as_one_fuc()
        self.folder_selector.as_one_fuc()
        self.folder_selector.mainloop()
        
    def process_data(self):
        try:
            all_subfolders = self.folder_selector.get_all_subfolders()
            for subfolder in all_subfolders:
                file_timestamps = self.get_file_timestamps(subfolder)
                sorted_files = sorted(file_timestamps, key=lambda x: x[1])
                fits, data = self.process_sorted_files(sorted_files, subfolder)
                plt_name = f'DRT_Fit_Results_{sorted_files[0][0].split(".")[0]}'
                parent_dir = os.path.dirname(subfolder)
                self.save_data_to_csv(data, parent_dir, plt_name)
                if fits:
                    self.plot_out_window(fits, plt_name, parent_dir)
        except Exception as e:
            print(f"Error in process_data: {e}")
        finally:
            # 确保即使出现异常也能清除数据
            self.folder_selector.selected_paths = []
            self.folder_selector.subfolders = {}
    
    def get_file_timestamps(self, subfolder):
        file_timestamps = []
        for f in os.listdir(subfolder):
            if f.endswith('.txt') or f.endswith('.csv'):
                file_path = os.path.join(subfolder, f)
                timestamp = self.fl.get_file_timestamp(file_path)
                if timestamp is not None:
                    file_timestamps.append((f, timestamp))
        return file_timestamps

    def process_sorted_files(self, sorted_files, subfolder):
        fits = {}
        fixed_basis_tau=np.logspace(-7, 2, 181)
        data = {'0x': fixed_basis_tau}
    
        # 对每个文件进行DRT分析
        for txt_file, _ in sorted_files:
            try:
                file_path = os.path.join(subfolder, txt_file)
                
                # 创建独立的 DRT 对象
                eis_drt = DRT(fit_dop=self.folder_selector.as_one, fixed_basis_tau=np.logspace(-7, 2, 181))
                
                # 加载 EIS 测量数据
                eis_tup = self.fl.get_eis(file_path)  # 读取EIS 文件
                
                # 拟合 EIS 数据
                eis_drt.fit_eis(*eis_tup, iw_l2_lambda_0=10)  # 拟合 EIS 数据
            
                # 将拟合结果存储到字典
                fits[txt_file] = eis_drt
                
                # 将拟合结果存储到列表
                data[txt_file] = eis_drt.fit_parameters['x']
            except Exception as e:
                print(f"Error processing {os.path.join(subfolder, txt_file)}: {e}\n")
                continue
                
        return fits, data

    def plot_out_window(self, fits, plt_name, parent_dir):
        # 绘制所有文件的EIS拟合结果
        fig, axes = plt.subplots(1, 1, figsize=(7, 7), constrained_layout=True)
        
        # 获取颜色映射
        colormap = plt.get_cmap("tab20c")  # 选择调色板
    
        # 绘制所有拟合结果，每个文件使用不同颜色
        for idx, (label, fit) in enumerate(fits.items()):
            eis_fmt = dict(c=colormap(idx / len(fits)), alpha=0.9)  # 使用颜色映射，idx用于索引颜色
            fit.plot_distribution(ax=axes, label=label, **eis_fmt)
        
        # 设置图形格式
        axes.set_xlim(1e-7, 1e2)
        axes.legend()
        
        # 保存图形
        fig.tight_layout()
        fig.savefig(os.path.join(parent_dir, f'{plt_name}.png'), dpi=300)
        
                
        # 将图形嵌入到 FolderSelector 的 right_frame 中
        try:
            # 导入 FigureCanvasTkAgg（如果尚未导入）
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            # 获取 FolderSelector 的 right_frame
            right_frame = self.folder_selector.right_frame
            
            # 清除 right_frame 中的所有现有控件
            for widget in right_frame.winfo_children():
                widget.destroy()
            
            # 创建并添加画布
            canvas = FigureCanvasTkAgg(fig, master=right_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # 保存画布引用，避免被垃圾回收
            self.folder_selector.canvas = canvas
            
        except Exception as e:
            print(f"无法在窗口中显示图形: {e}")
            plt.close(fig)  # 关闭图形，避免内存泄漏

if __name__ == "__main__":
    app = MainApp()
