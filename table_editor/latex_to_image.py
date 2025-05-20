import os
from pylatex import Document, NoEscape
from pdf2image import convert_from_path
from datasets import load_dataset
from modify_latex import finalize_latex_structure

#负责 把表格字符串保存为图像：
#	•	用 pylatex 把 LaTeX 写入 .tex
#	•	编译成 .pdf
#	•	再用 pdf2image 转为 .png
def save_latex_as_image(latex_str, outname="outputs/xxx"):
    latex_str = finalize_latex_structure(latex_str)
    ...
# 加载 ArXiv 表格数据集（可以选 staghado/ArXiv-tables 或 neulab/latex-table）
dataset = load_dataset("staghado/ArXiv-tables") 

# 看看每条数据有哪些字段
print(dataset["train"].column_names)

# 取一条真实表格的 LaTeX 代码
#example = dataset["train"][0]  # 第 0 条，可换成其他下标
#latex_str = example["latex_content"]
#print(latex_str)
#要批量处理 N 条数据
for i in range(10):  # 前 10 个
    latex_str = dataset["train"][i]["latex_content"]
    if "\\begin{tabular}" in latex_str:
        print(f"第 {i} 条：")
        print(latex_str)
       # save_latex_as_image(latex_str, outname=f"outputs/real_table_{i}") # type: ignore
    else:
        print(f"第 {i} 条不是标准表格，跳过")
   # if "\\begin{tabular}" in latex_str:
   #     save_latex_as_image(latex_str, outname=f"outputs/real_table_{i}")

def save_latex_as_image(latex_str, outname="outputs/output"):
    """
    将 LaTeX 表格代码编译为 PNG 图像。
    参数:
        latex_str: 一个完整的 LaTeX 表格字符串
        outname: 输出文件名（不带后缀）
    """
    # 创建输出目录
    os.makedirs("outputs", exist_ok=True)

    # 创建 LaTeX 文档对象
    doc = Document()
    doc.packages.append(NoEscape(r'\usepackage{float}'))   # 支持 [H]
    doc.packages.append(NoEscape(r'\usepackage{booktabs}'))  # 添加表格美化包
    doc.packages.append(NoEscape(r'\usepackage{graphicx}'))  # 支持 \resizebox
    doc.append(NoEscape(latex_str))  # 加入表格内容

    # 生成 PDF 文件
    doc.generate_pdf(outname, clean_tex=True)

    # 将 PDF 转为 PNG 图像
    images = convert_from_path(f"{outname}.pdf", poppler_path="/opt/local/bin")
    images[0].save(f"{outname}.png", "PNG")
    print(f"图像保存成功：{outname}.png")
    # outputs/ 中生成：•	test_table.pdf •	test_table.png
if __name__ == "__main__":
        dataset = load_dataset("staghado/ArXiv-tables")
        latex_str = dataset["train"][0]["latex_content"]
        save_latex_as_image(latex_str, outname="outputs/real_table_0")
        print("图像生成完毕")