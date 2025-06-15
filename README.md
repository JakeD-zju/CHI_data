# CHI_data
This project aims to batch process the data obtained from testing using the CHI electrochemical workstation, converting it into a format that can be directly pasted into Origin for plotting.

该脚本可选择存有辰华工作站数据的文件夹进行数据处理
﻿
数据必须保存为.txt或者.csv格式，无法直接处理.bin文件。
﻿
可实现数据文件批量处理，选定一级文件夹后处理其中所有二级文件夹数据
﻿
导入数据后，选择数据类型，如计时电流法选择CA，可选择多个文件夹同时处理
﻿
选择完成后，点击'结束选择'，开始处理并绘图。当同时导入多个文件夹时，仅能显示最后一次导入的文件夹的图像。
﻿
数据以数据类型_merged.txt格式存储于选择的文件夹内，如CA数据的保存文件为CA_merged.txt
