import streamlit as st
from datasets import load_dataset
from latex_to_image import save_latex_as_image
from modify_latex import modify_numeric_values, check_text, add_column_to_outermost_tabular
import tempfile
import os
from collections import Counter
import glob
from PIL import Image
import pandas as pd
import re
import matplotlib.pyplot as plt

st.set_page_config(page_title="ArXiv Table Modifier", layout="centered")
st.title("ArXiv Table Interactive Modifier")

# === Load dataset ===
@st.cache_data
def load_data():
    return load_dataset("staghado/ArXiv-tables")["train"]

dataset = load_data()

latex1 = dataset[0]
latex2 = dataset[0]["latex_content"]
st.subheader("Preliminary Analysis")
button = st.button("Run Analysis")

if button:
    st.text("Table attributes:")
    st.text(check_text(latex1))
    st.text("Length of the first LaTeX content:")
    st.text(len(latex2))
    lengths = [len(str(x["latex_content"])) for x in dataset]
    df = pd.DataFrame({"length": lengths})
    df["length"].plot.hist(bins=30, title="Distribution of LaTeX Content Length")
    st.pyplot(plt.gcf())
    vocab = Counter()
    for entry in dataset.select(range(500)):  # Sample 500 tables
        words = re.findall(r'\\?[a-zA-Z_]+', entry["latex_content"])
        vocab.update(words)
    st.text("Approximate vocabulary size:")
    st.text(len(vocab))

# === Table selection ===
default_index = st.session_state.get("table_index", 0)
table_index1 = st.number_input("Select Table Index", min_value=0, max_value=len(dataset)-1, step=1, value=default_index)
#latex = dataset[table_index]["latex_content"]
# Use session state to persist edits
latex = dataset[table_index1]["latex_content"]
if "working_latex" not in st.session_state or st.session_state.get("table_index",0) != table_index1:
    latex = dataset[table_index1]["latex_content"]
    st.session_state["working_latex"] = latex
    st.session_state["table_index"] = table_index1
    st.write("Updated working_latex from dataset") 

if "\\begin{tabular}" not in latex:
    st.warning("This table does not contain a tabular environment. Please choose another index.")
    st.stop()

# === Original LaTeX table rendering ===
st.subheader("Original LaTeX Table")
os.makedirs("outputs", exist_ok=True)
outname_base = f"outputs/table_{table_index1}_original"
try:
    save_latex_as_image(latex, outname=outname_base)
    orig_path = f"{outname_base}.png"
    st.text(f"Image should be saved to: {orig_path}")
    st.text(f"File exists: {os.path.exists(orig_path)}")
    st.text("Rendered image below:")
    left, center, right = st.columns([1, 200, 1])
    with center:
        with open(orig_path, "rb") as img_file:
            st.image(img_file.read(), caption="Original Table")
except Exception as e:
    st.warning("This table may contain unsupported LaTeX structures. Skipping rendering.")
    st.code(str(e), language="bash")
    with open(f"{outname_base}_error.tex", "w") as f:
        f.write(latex)
    st.info(f"LaTeX with error saved to {outname_base}_error.tex")
    st.stop()

# === Modify table values ===
st.subheader("Modify Values in the Table")
with st.form(key="add_column_form"):
    submitted2 = st.form_submit_button("Add New Column")

if submitted2:
    # Add a new column
    st.session_state["working_latex"] = add_column_to_outermost_tabular(st.session_state["working_latex"])
    modified_latex = st.session_state["working_latex"]
    #print(modified_latex)
    mod_outname_base = f"outputs/table_{table_index1}_modified_with_new_column"
    try:
        save_latex_as_image(modified_latex, outname=mod_outname_base)
        mod_path = f"{mod_outname_base}.png"
        st.subheader("Table with New Column")
        left, center, right = st.columns([200,1, 1])
        print(st.session_state["working_latex"])
        with left:
            with open(mod_path, "rb") as img_file:
                st.image(img_file.read(), caption="Table After Adding Column")
    except Exception as e:
        st.error(f"Rendering failed after adding column: {e}")


test = st.button("Test Button")
if test:
    st.text(st.session_state["working_latex"])


with st.form(key="modify_form"):
    n_changes = st.number_input("How many values do you want to modify?", min_value=0, max_value=10, step=1)
    changes = []
    for i in range(n_changes):
        col1, col2 = st.columns(2)
        with col1:
            old_val = st.text_input(f"Old Value #{i+1}", key=f"old_{i}")
        with col2:
            new_val = st.text_input(f"New Value #{i+1}", key=f"new_{i}")
        changes.append((old_val, new_val))
    submitted = st.form_submit_button("Apply Changes and Render")
 

# === Render modified image ===
if submitted:
    modified_latex = st.session_state["working_latex"]
    #print(modified_latex)
    for old, new in changes:
        if old and new:
            modified_latex = modify_numeric_values(modified_latex, old, new)
    mod_outname_base = f"outputs/table_{table_index1}_modified"
    try:
        save_latex_as_image(modified_latex, outname=mod_outname_base)
        st.session_state["working_latex"] = modified_latex
        mod_path = f"{mod_outname_base}.png"
        st.subheader("Modified Table")
        with open(mod_path, "rb") as img_file:
            st.image(img_file.read(), caption="Table After Modification")
    except Exception as e:
        st.error(f"Rendering failed after modification: {e}")


# === Navigation buttons ===
col1, col2 = st.columns(2)
with col1:
    if st.button("Previous Table"):
        st.session_state["table_index"] = (table_index1 - 1) % len(dataset)
        st.rerun()
with col2:
    if st.button("Next Table"):
        st.session_state["table_index"] = (table_index1 + 1) % len(dataset)
        st.rerun()