import os
import numpy as np
import matplotlib.pyplot as plt
from hybdrt.models import DRT
from fileloadCHI import FileLoaderCHI
import pandas as pd
from folderselector import FolderSelector
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class MainApp:
    """电化学阻抗谱(EIS)分析类，用于DRT拟合和DOP分析"""
    def __init__(self):
        
        self.fl = FileLoaderCHI()
        self.norm_tau = (1 / (2 * np.pi * 1e5), 1 / (2 * np.pi * 1e-2))    
        self.dop_l2_lambda_0 = 10
        self.folder_selector = FolderSelector(self.process_data, show_buttons = [])
        self.folder_selector.flag_text = '是否开启DOP'
        self.folder_selector.as_one_fuc()
        self.folder_selector.as_one_fuc()
        self.folder_selector.mainloop()
    
    def process_data(self):
        """处理选中文件夹中的数据"""
        try:
            all_subfolders = self.folder_selector.get_all_subfolders()
            for subfolder in all_subfolders:
                file_timestamps = self.get_file_timestamps(subfolder)
                sorted_files = sorted(file_timestamps, key=lambda x: x[1])
                lambda_0 = self.folder_selector.lambda_value
                fits, data, data_dop = self.process_sorted_files(sorted_files, subfolder, lambda_0)
                plt_name = f'DRT_Fit_Results_{sorted_files[0][0].split(".")[0]}_λ={lambda_0}'
                parent_dir = os.path.dirname(subfolder)
                self.save_data_to_txt(data, data_dop, parent_dir, plt_name)
                # print("sss")
                if fits:
                    self.plot_out_window(fits, plt_name, parent_dir)
        except Exception as e:
            print(f"Error in process_data: {e}")
        finally:
            # 确保即使出现异常也能清除数据
            if self.folder_selector:
                self.folder_selector.selected_paths = []
                self.folder_selector.subfolders = {}
    
    def get_file_timestamps(self, subfolder):
        """获取指定文件夹中所有EIS文件的时间戳"""
        file_timestamps = []
        for f in os.listdir(subfolder):
            if f.endswith('.txt') or f.endswith('.csv'):
                file_path = os.path.join(subfolder, f)
                timestamp = self.fl.get_file_timestamp(file_path)
                if timestamp is not None:
                    file_timestamps.append((f, timestamp))
        return file_timestamps
    
    def process_sorted_files(self, sorted_files, subfolder, iw_l2_lambda_0):
        """处理排序后的文件列表，进行DRT分析"""
        fits = {}
        fixed_basis_tau = np.logspace(-7, 2, 181)
        data = {'0x': fixed_basis_tau}
        data_dop = None  # 默认为None，仅在需要时初始化

        # 对每个文件进行DRT分析
        for txt_file, _ in sorted_files:
            try:
                file_path = os.path.join(subfolder, txt_file)
                eis_drt = DRT(fit_dop=self.folder_selector.as_one, fixed_basis_tau=fixed_basis_tau)
                eis_tup = self.fl.get_eis(file_path)
                
                # 动态传递参数
                fit_kwargs = {'iw_l2_lambda_0': iw_l2_lambda_0}
                if self.folder_selector.as_one:
                    fit_kwargs['dop_l2_lambda_0'] = self.dop_l2_lambda_0
                eis_drt.fit_eis(*eis_tup, **fit_kwargs)
                
                fits[txt_file] = eis_drt
                data[txt_file] = eis_drt.predict_distribution(fixed_basis_tau)
                
                # 仅在as_one为True时收集DOP数据
                if self.folder_selector.as_one:
                    # 延迟初始化data_dop
                    if data_dop is None:
                        data_dop = {'0x_dop': None}
                    data_dop[txt_file] = eis_drt.predict_dop(
                        normalize=True, normalize_tau=self.norm_tau)

            except Exception as e:
                print(f"Error processing {txt_file}: {e}")
                continue

        # 仅在as_one为True时处理DOP的x轴数据
        if self.folder_selector.as_one and data_dop is not None:
            data_dop['0x_dop'], __ = eis_drt.predict_dop(
                normalize=True, normalize_tau=self.norm_tau, return_nu=True)
            data_dop['0x_dop'] = data_dop['0x_dop'] * -90
    
        return fits, data, data_dop
    
    def plot_out_window(self, fits, plt_name, parent_dir):
        """绘制四个子图并分别设置标题：DRT、DOP、拟合结果、残差"""
        # 创建 2x2 子图布局
        fig, axes = plt.subplots(2, 2, figsize=(10, 6), constrained_layout=True)
        axes = axes.flatten()  # 展平为一维数组
        
        # 子图标题列表
        subplot_titles = ["DRT 分布", "DOP 分布", "EIS 拟合结果", "拟合残差"]
        
        # 确保至少有一个拟合结果
        if not fits:
            for ax in axes:
                ax.text(0.5, 0.5, "无数据可绘制", ha='center', va='center', fontsize=12)
            plt.close(fig)
            return
        
        # 颜色映射
        colormap = plt.get_cmap("tab20c")
        # 绘制四个子图
        for i, ax in enumerate(axes):
            if i == 0:
                # 子图1：DRT 分布
                ax.set_title(subplot_titles[0], fontsize=7)
                for idx, (label, fit) in enumerate(fits.items()):
                    eis_fmt = dict(c=colormap(idx / len(fits)), alpha=0.9)
                    fit.plot_distribution(ax=ax, label=label, **eis_fmt)
                ax.set_xlim(1e-7, 1e2)
                
            elif i == 1:
                # 子图2：DOP 分布
                ax.set_title(subplot_titles[1], fontsize=7)
                if self.folder_selector.as_one:
                    for idx, (label, fit) in enumerate(fits.items()):
                        if hasattr(fit, 'plot_dop'):
                            eis_fmt = dict(c=colormap(idx / len(fits)), alpha=0.9)
                            fit.plot_dop(ax=ax, label=label, **eis_fmt, 
                                         normalize=True, normalize_tau=self.norm_tau)
                        else:
                            ax.text(0.5, 0.5, "无DOP数据", ha='center', va='center')
                else:
                    ax.text(0.5, 0.5, "DOP未开启", ha='center', va='center', transform=ax.transAxes )
                ax.set_xlim(0, 90)
                
            elif i == 2:
                # 子图3：EIS 拟合结果
                ax.set_title(subplot_titles[2], fontsize=7)
                for idx, (label, fit) in enumerate(fits.items()):
                    eis_fmt = dict(c=colormap(idx / len(fits)), alpha=0.9)
                    fit.plot_eis_fit(axes=axes[2], **eis_fmt,
                                            label='Fit', data_label='Data')
                
            elif i == 3:
                # 子图4：拟合残差
                ax.set_title(subplot_titles[3], fontsize=7)
                for idx, (label, fit) in enumerate(fits.items()):
                    color = colormap(idx / len(fits))
                    eis_fmt = dict(color=color, alpha=0.9)
                    fit.plot_eis_residuals(axes=axes[3], **eis_fmt,
                                            plot_sigma=False, facecolors='none', part='imag')
            
            # 统一设置
            ax.legend()
            ax.grid(True, linestyle='--', alpha=0.5)
        
        # 保存图形
        fig.savefig(os.path.join(parent_dir, f'{plt_name}.png'), dpi=300)

        
        # 嵌入到窗口
        try:
            if self.folder_selector:
                right_frame = self.folder_selector.right_frame
                for widget in right_frame.winfo_children():
                    widget.destroy()
                
                self.canvas = FigureCanvasTkAgg(fig, master=right_frame)
                self.canvas.draw()
                self.canvas.get_tk_widget().pack(fill="both", expand=True)
                
        except Exception as e:
            print(f"图形嵌入错误: {e}")
            plt.close(fig)
    
    def save_data_to_txt(self, data, data_dop, parent_dir, plt_name):
        """将数据保存为txt文件"""
        # 保存DRT数据
        data_df = pd.DataFrame(data)
        data_df.to_csv(os.path.join(parent_dir, f'{plt_name}.txt'), 
                       sep='\t', index=False)
        if data_dop is None:
            return
        data_dop_df = pd.DataFrame(data_dop)
        data_dop_df.to_csv(os.path.join(parent_dir, f'{plt_name}_dop.txt'), 
                           sep='\t', index=False)


if __name__ == "__main__":
    app = MainApp()
