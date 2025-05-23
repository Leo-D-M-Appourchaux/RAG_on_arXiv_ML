import streamlit as st
from datasets import load_dataset
from latex_to_image import save_latex_as_image
from modify_latex import modify_numeric_values
from modify_latex import check_text
import tempfile
import os
import glob
from PIL import Image
from modify_latex import add_column_to_outermost_tabular

st.set_page_config(page_title="ArXiv Table Modifier", layout="centered")
st.title("ArXiv Table Interactive Modifier")

# === 加载数据集 ===
@st.cache_data
def load_data():
    return load_dataset("staghado/ArXiv-tables")["train"]

dataset = load_data()

# === 表格选择 ===
default_index = st.session_state.get("table_index", 0)
table_index = st.number_input("选择表格编号", min_value=0, max_value=len(dataset)-1, step=1, value=default_index)
latex = dataset[table_index]["latex_content"]

if "\\begin{tabular}" not in latex:
    st.warning("这个表格不包含 tabular 环节，请选别的编号。")
    st.stop()

# === 原始图像渲染 ===
st.subheader("原始 LaTeX 表格")
os.makedirs("outputs", exist_ok=True)
outname_base = f"outputs/table_{table_index}_original"
try:
    save_latex_as_image(latex, outname=outname_base)
    orig_path = f"{outname_base}.png"
    st.text(f"图像应保存到：{orig_path}")
    st.text(f"文件是否存在：{os.path.exists(orig_path)}")
    files = glob.glob("outputs/*.png")
    st.text(f"渲染图像如下")
    with open(orig_path, "rb") as img_file:
        st.image(img_file.read(), caption="原始表格")
except Exception as e:
    st.warning("此表格可能含有不支持的 LaTeX 结构，已跳过渲染。")
    st.code(str(e), language="bash")
    # 保存出错的 LaTeX 到 .tex 文件
    with open(f"{outname_base}_error.tex", "w") as f:
        f.write(latex)
    st.info(f"出错的 LaTeX 已保存为 {outname_base}_error.tex")
    st.stop()

# === 修改表格 ===
st.subheader("修改表格中的数值")

with st.form(key="modify_form"):
    n_changes = st.number_input("想修改几个值？", min_value=0, max_value=10, step=1)
    changes = []
    for i in range(n_changes):
        col1, col2 = st.columns(2)
        with col1:
            old_val = st.text_input(f"原值 #{i+1}", key=f"old_{i}")
        with col2:
            new_val = st.text_input(f"新值 #{i+1}", key=f"new_{i}")
        changes.append((old_val, new_val))
    submitted = st.form_submit_button("生成修改图像")
    submitted2 = st.form_submit_button("add a new column")
    submitted3 = st.form_submit_button("preliminary analysis")

# === 渲染修改后的图像 ===
if submitted:
    modified_latex = latex
    for old, new in changes:
        if old and new:
            modified_latex = modify_numeric_values(modified_latex, old, new)
    mod_outname_base = f"outputs/table_{table_index}_modified"
    try:
        save_latex_as_image(modified_latex, outname=mod_outname_base)
        mod_path = f"{mod_outname_base}.png"
        st.subheader("修改后图像")
        with open(mod_path, "rb") as img_file:
            st.image(img_file.read(), caption="修改后表格渲染结果")
    except Exception as e:
        st.error(f"修改后渲染失败：{e}")

if submitted2:
    # 添加新列
        modified_latex = add_column_to_outermost_tabular(latex)
        mod_outname_base = f"outputs/table_{table_index}_modified_with_new_column"
        try:
            save_latex_as_image(modified_latex, outname=mod_outname_base)
            mod_path = f"{mod_outname_base}.png"
            st.subheader("添加新列后的图像")
            with open(mod_path, "rb") as img_file:
                st.image(img_file.read(), caption="添加新列后的表格渲染结果")
        except Exception as e:
            st.error(f"添加新列后渲染失败：{e}")


if submitted3:
    st.text("正在进行初步分析...")
    st.text(check_text(latex))
# === 上一个/下一个表格按钮 ===
col1, col2 = st.columns(2)
with col1:
    if st.button("上一个表格"):
        st.session_state["table_index"] = (table_index - 1) % len(dataset)
        st.rerun()
with col2:
    if st.button("下一个表格"):
        st.session_state["table_index"] = (table_index + 1) % len(dataset)
        st.rerun()