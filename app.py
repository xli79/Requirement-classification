import streamlit as st
import openpyxl
from openai import OpenAI
import io

# 页面设置
st.set_page_config(page_title="汽车需求分析助手", layout="wide")
st.title("🚗 汽车需求智能分析助手")
st.markdown("上传需求Excel文件，AI自动完成分类、质量评分和改进建议")

# 侧边栏设置
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("API Key", type="password", placeholder="输入你的API Key")
    model = st.selectbox("选择模型", [
        "deepseek-ai/DeepSeek-V3",
        "google/gemini-2.0-flash-001"
    ])
    st.markdown("---")
    st.markdown("**使用说明**")
    st.markdown("1. 输入API Key")
    st.markdown("2. 上传Excel文件（A列为需求）")
    st.markdown("3. 点击开始分析")
    st.markdown("4. 下载结果")

# 主界面
uploaded_file = st.file_uploader("上传需求Excel文件", type=["xlsx"])

if uploaded_file and api_key:
    # 读取Excel
    wb = openpyxl.load_workbook(uploaded_file)
    ws = wb.active
    
    requirements = []
    for row in range(1, ws.max_row + 1):
        val = ws[f"A{row}"].value
        if val:
            requirements.append(str(val))
    
    st.success(f"✅ 成功读取 {len(requirements)} 条需求")
    
    # 预览需求
    with st.expander("📋 查看需求列表"):
        for i, r in enumerate(requirements):
            st.write(f"{i+1}. {r}")
    
    if st.button("🚀 开始分析", type="primary"):
        client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
        
        # 第一步：归纳类型
        with st.spinner("AI正在归纳需求类型..."):
            all_reqs = "\n".join([f"{i+1}. {r}" for i, r in enumerate(requirements)])
            response = client.chat.completions.create(
                model=model,
                temperature=0.1,
                messages=[{"role": "user", "content": f"""你是汽车行业需求分析专家。
根据以下需求自己归纳出最合适的需求类型，不要使用预设分类。
每个类型给出名称和简短定义。

需求列表：
{all_reqs}

回复格式：
类型1：xxx | 定义：xxx
类型2：xxx | 定义：xxx"""}]
            )
            categories = response.choices[0].message.content
        
        st.subheader("📊 AI归纳的需求类型")
        st.text(categories)
        st.markdown("---")
        
        # 第二步：逐条分析
        st.subheader("📝 逐条分析结果")
        results = []
        progress = st.progress(0)
        
        for i, req in enumerate(requirements):
            with st.spinner(f"正在分析第 {i+1}/{len(requirements)} 条..."):
                response = client.chat.completions.create(
                    model=model,
                    temperature=0.1,
                    messages=[{"role": "user", "content": f"""你是汽车行业需求分析专家。
根据以下类型定义分析这条需求：

可用类型：
{categories}

需求：{req}

回复格式（严格按此格式）：
类型：xxx
评分：1-5分的整数
建议：xxx"""}]
                )
                result = response.choices[0].message.content
                
                req_type, score, suggestion = "", "", ""
                for line in result.strip().split("\n"):
                    if line.startswith("类型："):
                        req_type = line.replace("类型：", "").strip()
                    elif line.startswith("评分："):
                        score = line.replace("评分：", "").strip()
                    elif line.startswith("建议："):
                        suggestion = line.replace("建议：", "").strip()
                
                results.append({
                    "需求原文": req,
                    "AI类型": req_type,
                    "质量评分": score,
                    "改进建议": suggestion
                })
                
                # 显示结果卡片
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{req}**")
                        st.caption(f"建议：{suggestion}")
                    with col2:
                        st.metric("类型", req_type)
                        st.metric("评分", score)
                    st.markdown("---")
                
                progress.progress((i + 1) / len(requirements))
        
        # 生成下载文件
        wb_out = openpyxl.Workbook()
        ws_out = wb_out.active
        ws_out.append(["需求原文", "AI类型", "质量评分", "改进建议"])
        for r in results:
            ws_out.append([r["需求原文"], r["AI类型"], r["质量评分"], r["改进建议"]])
        
        buffer = io.BytesIO()
        wb_out.save(buffer)
        buffer.seek(0)
        
        st.success("🎉 分析完成！")
        st.download_button(
            label="📥 下载分析结果Excel",
            data=buffer,
            file_name="需求分析结果.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

elif uploaded_file and not api_key:
    st.warning("⚠️ 请在左侧填入API Key")
elif not uploaded_file:
    st.info("👆 请上传Excel文件开始分析")