import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import scipy.stats as stats
import io
import base64

# ==========================================
# 0. 页面配置与全局样式
# ==========================================
st.set_page_config(
    page_title="Howland 电流源分析台", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .metric-sub { font-size: 0.85em; color: #666; padding: 8px; background: #f8f9fa; border-radius: 4px; border-left: 4px solid #ccc; line-height: 1.6;}
    .metric-sub-dac { border-left-color: #ffc107; }
    .metric-sub-hw { border-left-color: #17a2b8; }
    .metric-sub-sys { border-left-color: #28a745; }
    .acc-text { color: #d9534f; font-weight: bold; font-family: monospace; font-size: 1.05em; }
    .formula-ui { background-color: #eef2f5; padding: 12px 15px; border-left: 4px solid #17a2b8; margin-bottom: 15px; font-size: 0.9em; border-radius: 4px;}
    </style>
    """, unsafe_allow_html=True)

def apply_chart_style(fig, title, x_title, y_title):
    fig.update_layout(
        title=title, plot_bgcolor='white', paper_bgcolor='white', hovermode="x unified",
        margin=dict(l=80, r=40, t=60, b=80), 
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5) 
    )
    fig.update_xaxes(title_text=x_title, automargin=True, showgrid=True, gridcolor='LightGray', zeroline=True, zerolinecolor='gray')
    fig.update_yaxes(title_text=y_title, automargin=True, showgrid=True, gridcolor='LightGray', zeroline=True, zerolinecolor='gray')
    return fig

# ==========================================
# 1. 侧边栏：导入与硬件配置
# ==========================================
st.sidebar.title("📁 导入与硬件配置")

uploaded_file = st.sidebar.file_uploader("上传测试数据 (CSV/Excel)", type=["csv", "xlsx", "xls"])

df_raw = None
if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df_raw = pd.read_csv(uploaded_file)
    else:
        df_raw = pd.read_excel(uploaded_file)

if df_raw is not None:
    df_raw.columns = df_raw.columns.str.strip()
    all_columns = df_raw.columns.tolist()
    
    st.sidebar.markdown("### ⚙️ 硬件参数设定")
    R_set = st.sidebar.number_input("设定电阻 R_set (Ω)", value=240.0, step=1.0, format="%.2f")
    FS_I = st.sidebar.number_input("满量程电流 FS (mA)", value=12.0, step=1.0)
    k_factor = st.sidebar.selectbox("扩展不确定度 (K 因子)", [1, 2, 3], index=1)
    
    st.sidebar.markdown("### 🧹 数据列映射")
    col_v_theo = st.sidebar.selectbox("理论电压 (DAC 设定值) [mV]", all_columns, index=all_columns.index('DAC_out(mV)') if 'DAC_out(mV)' in all_columns else 0)
    col_v_act = st.sidebar.selectbox("实际电压 (DAC 物理输出) [mV]", all_columns, index=all_columns.index('DMM_meas_volt(mV)') if 'DMM_meas_volt(mV)' in all_columns else 0)
    col_i_act = st.sidebar.selectbox("实际输出电流 [mA]", all_columns, index=all_columns.index('DMM_meas_curr(mA)') if 'DMM_meas_curr(mA)' in all_columns else 0)
    col_i_theo = st.sidebar.selectbox("理论输出电流 [mA]", all_columns, index=all_columns.index('Target_curr(mA)') if 'Target_curr(mA)' in all_columns else 0)

    # 清洗数据
    df_valid = df_raw.copy().dropna(subset=[col_v_theo, col_v_act, col_i_act, col_i_theo])
    for col in [col_v_theo, col_v_act, col_i_act, col_i_theo]:
        df_valid[col] = pd.to_numeric(df_valid[col].astype(str).str.strip(), errors='coerce')
    df_valid = df_valid.dropna().sort_values(by=col_v_theo).reset_index(drop=True)

    if len(df_valid) < 2:
        st.error("🚨 致命数据错误：有效数据点少于 2 个！")
        st.stop()

    # ==========================================
    # 2. 核心分析引擎：三节点解耦
    # ==========================================
    df_mean = df_valid.groupby(col_v_theo, as_index=False).mean().sort_values(by=col_v_theo).reset_index(drop=True)
    N_avg = len(df_valid) / len(df_mean)
    is_staircase = N_avg >= 1.5  

    def calc_r2(y_true, y_pred):
        ss_res = np.sum((y_true - y_pred)**2)
        ss_tot = np.sum((y_true - np.mean(y_true))**2)
        return 1.0 if ss_tot == 0 else 1 - (ss_res / ss_tot)
    
    def calc_acc(x_meas, y_meas, k_ideal, fs_val, k_cov):
        k_ep, b_ep = np.polyfit(x_meas, y_meas, 1)
        rmse = np.sqrt(np.mean((y_meas - (k_ep * x_meas + b_ep))**2))
        pct_rdg = (abs(k_ep - k_ideal) / k_ideal) * 100 if k_ideal != 0 else 0
        pct_fs = ((abs(b_ep) + k_cov * rmse) / fs_val) * 100 if fs_val != 0 else 0
        return pct_rdg, pct_fs

    ideal_Gm = 1.0 / R_set  
    
    # --- 模块 A: DAC 电压域 (mV vs mV) ---
    k_dac, b_dac = np.polyfit(df_mean[col_v_theo], df_mean[col_v_act], 1)
    fit_dac = k_dac * df_mean[col_v_theo] + b_dac
    inl_dac_v = df_mean[col_v_act] - fit_dac
    r2_dac = calc_r2(df_mean[col_v_act], fit_dac)
    acc_dac_rdg, acc_dac_fs = calc_acc(df_mean[col_v_theo], df_mean[col_v_act], 1.0, FS_I * R_set, k_factor)

    # --- 模块 B: Howland 核心 V-I 转换 (mV vs mA) ---
    k_hw, b_hw = np.polyfit(df_mean[col_v_act], df_mean[col_i_act], 1)
    fit_hw = k_hw * df_mean[col_v_act] + b_hw
    inl_hw_i = df_mean[col_i_act] - fit_hw
    r2_hw = calc_r2(df_mean[col_i_act], fit_hw)
    acc_hw_rdg, acc_hw_fs = calc_acc(df_mean[col_v_act], df_mean[col_i_act], ideal_Gm, FS_I, k_factor)

    # --- 模块 C: 系统全链路 (mV vs mA) ---
    k_sys, b_sys = np.polyfit(df_mean[col_v_theo], df_mean[col_i_act], 1)
    fit_sys = k_sys * df_mean[col_v_theo] + b_sys
    inl_sys_i = df_mean[col_i_act] - fit_sys
    r2_sys = calc_r2(df_mean[col_i_act], fit_sys)
    acc_sys_rdg, acc_sys_fs = calc_acc(df_mean[col_v_theo], df_mean[col_i_act], ideal_Gm, FS_I, k_factor)

    # --- 误差折算 ---
    err_v_dac = df_mean[col_v_act] - df_mean[col_v_theo]
    err_i_from_dac = err_v_dac / R_set  
    err_i_howland_pure = df_mean[col_i_act] - (df_mean[col_v_act] / R_set)
    err_i_sys_total = df_mean[col_i_act] - df_mean[col_i_theo]

    # ✨ 校准后残差与噪声计算 (新增部分)
    err_cal_sys_i_all = df_valid[col_i_act] - (k_sys * df_valid[col_v_theo] + b_sys)
    err_cal_sys_i_mean = df_mean[col_i_act] - (k_sys * df_mean[col_v_theo] + b_sys)
    
    rms_sys = np.std(err_cal_sys_i_all, ddof=1) if len(err_cal_sys_i_all) > 1 else 0
    pp_sys = (np.max(err_cal_sys_i_all) - np.min(err_cal_sys_i_all)) if len(err_cal_sys_i_all) > 1 else 0
    max_err_cal_sys = np.max(np.abs(err_cal_sys_i_all))
    
    enob_sys = f"{np.log2(FS_I / rms_sys):.2f} Bits" if rms_sys > 0 else "N/A"
    nfr_sys = f"{np.log2(FS_I / pp_sys):.2f} Bits" if pp_sys > 0 else "N/A"
    
    lbl_rms = "全局纯底噪 RMS (1σ)" if is_staircase else "综合均方根残差 (RMSE)"
    lbl_pp = "全局极限跳动 (P-P)" if is_staircase else "综合残差峰峰值 (P-P)"

    # ==========================================
    # 3. 矩阵式诊断 Dashboard
    # ==========================================
    st.title("⚡ Howland 电流源分析报告")
    if is_staircase:
        st.success(f"✅ **阶梯降维引擎激活：** 侦测到平均每个设定台阶 **{N_avg:.1f}** 个采样点，可提取纯交流动态噪声。")
    else:
        st.info("💡 **当前状态：** 检测为单点快速扫频。仅展示静态线性误差，动态底噪特征折叠。")

    st.markdown(f"### 🎯 V-I 信号链精度解构 (FS = {FS_I} mA, R_set = {R_set} Ω)")
    
    col_1, col_2, col_3 = st.columns(3)
    with col_1:
        st.info("🛠️ **模块 1: 前端 DAC 电压域**")
        st.metric("实际电压增益 (k)", f"{k_dac:.6f} V/V")
        st.metric("零点失调电压 (b)", f"{b_dac:.4f} mV")
        st.markdown(f"<div class='metric-sub metric-sub-dac'><b>线性度 R²:</b> {r2_dac:.6f}<br><b>综合精度:</b> <span class='acc-text'>±({acc_dac_rdg:.4f}% R + {acc_dac_fs:.4f}% FS)</span></div>", unsafe_allow_html=True)
        
    with col_2:
        st.warning("🧲 **模块 2: Howland V-I 转换域**")
        st.metric("实际跨导 Gm", f"{k_hw*1000:.4f} mA/V")
        st.metric("本底偏置电流 (I_os)", f"{b_hw*1000:.4f} μA")
        st.markdown(f"<div class='metric-sub metric-sub-hw'><b>线性度 R²:</b> {r2_hw:.6f}<br><b>综合精度:</b> <span class='acc-text'>±({acc_hw_rdg:.4f}% R + {acc_hw_fs:.4f}% FS)</span></div>", unsafe_allow_html=True)
        
    with col_3:
        st.success("🔗 **模块 3: 系统全链路 (端到端)**")
        st.metric("系统跨导等效增益", f"{k_sys*1000:.4f} mA/V")
        st.metric("系统总失调电流", f"{b_sys*1000:.4f} μA")
        st.markdown(f"<div class='metric-sub metric-sub-sys'><b>线性度 R²:</b> {r2_sys:.6f}<br><b>综合精度:</b> <span class='acc-text'>±({acc_sys_rdg:.4f}% R + {acc_sys_fs:.4f}% FS)</span></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background: #eef2f5; padding: 15px; border-radius: 5px; border-left: 5px solid #28a745; margin-bottom: 15px;'>
        <b>✨ 系统级线性校准后评估 (动态底噪与非线性残差)：</b><br>
        最大绝对极值：<span style='color: #d9534f; font-weight: bold;'>{max_err_cal_sys*1000:.4f} μA</span> |
        {lbl_rms}：<span style='color: #28a745; font-weight: bold;'>{rms_sys*1000:.4f} μA</span> |
        {lbl_pp}：<span style='color: #d9534f; font-weight: bold;'>{pp_sys*1000:.4f} μA</span><br>
        全局 ENOB：<span style='color: #28a745; font-weight: bold;'>{enob_sys}</span> |
        全局 NFR (无噪声分辨率)：<span style='color: #28a745; font-weight: bold;'>{nfr_sys}</span>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================
    # 4. 可视化图表 (Tabs)
    # ==========================================
    tab_trace, tab_tue, tab_inl, tab_cal, tab_fit, tab_hist, tab_export = st.tabs([
        "🔪 误差溯源拆解", "🔮 绝对误差", "🏹 INL非线性", "✨ 校准残差图", "📉 传递函数拟合", "📊 定点微观统计", "💾 看板导出"
    ])
    
    with tab_trace:
        st.markdown("### 🔪 绝对电流误差溯源拆解图")
        fig_trace = go.Figure()
        fig_trace.add_trace(go.Scatter(x=df_mean[col_v_theo], y=err_i_from_dac * 1000, mode='lines', fill='tozeroy', name='[1] DAC 引入的误差 (μA)', line=dict(color='#ffc107', width=2)))
        fig_trace.add_trace(go.Scatter(x=df_mean[col_v_theo], y=err_i_howland_pure * 1000, mode='lines', name='[2] Howland 纯转换误差 (μA)', line=dict(color='#17a2b8', width=2)))
        fig_trace.add_trace(go.Scatter(x=df_mean[col_v_theo], y=err_i_sys_total * 1000, mode='lines', name='系统总电流误差 (μA)', line=dict(color='black', width=3, dash='dash')))
        fig_trace.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)
        st.plotly_chart(apply_chart_style(fig_trace, "", "理论设定电压 DAC_out (mV)", "输出电流误差 (μA)"), use_container_width=True)

    with tab_tue:
        st.markdown("### 系统全链路绝对误差 vs 输入图")
        fig_tue = go.Figure()
        fig_tue.add_trace(go.Scatter(x=df_mean[col_v_theo], y=err_i_sys_total * 1000, mode='lines', name='系统总绝对误差 (μA)', line=dict(color='#d9534f', width=2)))
        st.plotly_chart(apply_chart_style(fig_tue, "", "理论设定电压 DAC_out (mV)", "绝对电流误差 (μA)"), use_container_width=True)

    with tab_inl:
        st.markdown("### 系统各级积分非线性 (INL) 对比")
        fig_inl = go.Figure()
        fig_inl.add_trace(go.Scatter(x=df_mean[col_v_theo], y=(inl_dac_v / R_set) * 1000, mode='lines', name="DAC 等效 INL (μA)", line=dict(color='#ffc107', width=2)))
        fig_inl.add_trace(go.Scatter(x=df_mean[col_v_theo], y=inl_hw_i * 1000, mode='lines', name="Howland 硬件 INL (μA)", line=dict(color='#17a2b8', width=2)))
        fig_inl.add_trace(go.Scatter(x=df_mean[col_v_theo], y=inl_sys_i * 1000, mode='lines', name="系统总 INL (μA)", line=dict(color='#28a745', width=3, dash='dot')))
        st.plotly_chart(apply_chart_style(fig_inl, "", "理论设定电压 DAC_out (mV)", "积分非线性绝对残差 INL (μA)"), use_container_width=True)

    with tab_cal:
        st.markdown("### ✨ 系统级线性校准后残差 (评估纯非线性与底噪)")
        st.markdown("<div class='formula-ui'><b>💡 意义：</b> 模拟 MCU 两点校准后，系统无法通过软件轻易消除的终极残余误差。若包含阶梯驻留数据，散点云即可代表动态热噪声带来的随机跳动带。</div>", unsafe_allow_html=True)
        fig_cal = go.Figure()
        if is_staircase:
            fig_cal.add_trace(go.Scatter(x=df_valid[col_v_theo], y=err_cal_sys_i_all * 1000, mode='markers', marker=dict(size=4, opacity=0.3, color='#28a745'), name="单次采样残差 (μA)"))
            fig_cal.add_trace(go.Scatter(x=df_mean[col_v_theo], y=err_cal_sys_i_mean * 1000, mode='lines', line=dict(color='#28a745', width=2), name="均值中心线 (μA)"))
        else:
            fig_cal.add_trace(go.Scatter(x=df_valid[col_v_theo], y=err_cal_sys_i_all * 1000, mode='lines+markers', line=dict(color='#28a745', width=1.5), marker=dict(size=4), name="扫频残差 (μA)"))
        fig_cal.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(apply_chart_style(fig_cal, "", "理论设定电压 DAC_out (mV)", "校准后残差电流 (μA)"), use_container_width=True)

    with tab_fit:
        st.markdown("### 硬件传递函数拟合全景图")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fig_f1 = go.Figure()
            fig_f1.add_trace(go.Scatter(x=df_valid[col_v_theo], y=df_valid[col_v_act], mode='markers', name="实测散点", marker=dict(color='#ffc107', size=4)))
            fig_f1.add_trace(go.Scatter(x=df_mean[col_v_theo], y=fit_dac, mode='lines', name="线性拟合", line=dict(dash='dash', color='black')))
            st.plotly_chart(apply_chart_style(fig_f1, f"DAC 响应 | R²={r2_dac:.6f}", "理论 DAC 电压 (mV)", "实际 DAC 电压 (mV)"), use_container_width=True)
        with col_f2:
            fig_f2 = go.Figure()
            fig_f2.add_trace(go.Scatter(x=df_valid[col_v_act], y=df_valid[col_i_act], mode='markers', name="实测散点", marker=dict(color='#17a2b8', size=4)))
            fig_f2.add_trace(go.Scatter(x=df_mean[col_v_act], y=fit_hw, mode='lines', name="线性拟合", line=dict(dash='dash', color='black')))
            st.plotly_chart(apply_chart_style(fig_f2, f"Howland V-I 转换 | R²={r2_hw:.6f}", "实际输入电压 (mV)", "实际输出电流 (mA)"), use_container_width=True)

    # ==========================================
    # 5. Tab_hist: 定点微观统计 (Staircase Dwell)
    # ==========================================
    hist_htmls_export = ""
    with tab_hist:
        def get_i_stats_html(curr_series, color):
            N = len(curr_series)
            if N < 2: return ""
            mean_val = curr_series.mean()
            std_val_uA = curr_series.std(ddof=1) * 1000 
            pp_val_uA = (curr_series.max() - curr_series.min()) * 1000
            return f"""
            <div style='background: #f8f9fa; border-left: 4px solid {color}; padding: 12px 15px; margin-top: -20px; margin-bottom: 15px; border-radius: 4px; font-size: 0.88em; color: #333;'>
                <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;'>
                    <div><b>N (样本数):</b> {N}</div>
                    <div><b>Mean (均值):</b> {mean_val:.6f} mA</div>
                    <div><b>RMS (本底噪声):</b> <span style='color:#d9534f;'>{std_val_uA:.4f} μA</span></div>
                    <div><b>Max (极大值):</b> {curr_series.max():.6f} mA</div>
                    <div><b>Min (极小值):</b> {curr_series.min():.6f} mA</div>
                    <div><b>P-P (峰峰值跳动):</b> <span style='color:#d9534f;'>{pp_val_uA:.4f} μA</span></div>
                </div>
            </div>
            """

        def plot_histogram_with_fit(data, title, color):
            data_clean = pd.to_numeric(pd.Series(data), errors='coerce').dropna().values
            fig = go.Figure()
            if len(data_clean) < 2: return fig.update_layout(title=title + " (无有效数据)")
            mean_val = np.mean(data_clean)
            std_val = np.std(data_clean, ddof=1)
            fig.add_trace(go.Histogram(x=data_clean, name='实测频数', marker_color=color, opacity=0.6, nbinsx=25))
            if std_val > 0:
                x_range = np.linspace(np.min(data_clean), np.max(data_clean), 200)
                counts, bins = np.histogram(data_clean, bins=25)
                bin_width = bins[1] - bins[0] if len(bins) > 1 else 1
                pdf_scaled = stats.norm.pdf(x_range, mean_val, std_val) * len(data_clean) * bin_width
                fig.add_trace(go.Scatter(x=x_range, y=pdf_scaled, mode='lines', name='高斯理论包络', line=dict(color='black', dash='dash', width=2)))
            fig.update_layout(title=title, barmode='overlay', plot_bgcolor='white', hovermode="x", legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5), margin=dict(t=60, b=60))
            fig.update_xaxes(title_text="实测输出电流 (mA)", showgrid=True, gridcolor='LightGray')
            fig.update_yaxes(title_text="频数 (Count)", showgrid=True, gridcolor='LightGray')
            return fig

        if is_staircase:
            st.markdown(f"### 🎯 设定台阶抽样 - 局部高斯底噪与跳动诊断")
            unique_steps = df_mean[col_v_theo].tolist()
            default_sel = [unique_steps[0], unique_steps[len(unique_steps)//2]] if len(unique_steps) > 2 else unique_steps
            selected_steps = st.multiselect("请点选需要提取动态底噪的设定电压点 (mV)：", options=unique_steps, default=default_sel)
            if selected_steps:
                for step_val in selected_steps:
                    step_data = df_valid[df_valid[col_v_theo] == step_val][col_i_act]
                    if len(step_data) == 0: continue
                    st.markdown(f"#### ⚡ 阶梯定点: DAC 设定 = {step_val} mV")
                    fig_hist = plot_histogram_with_fit(step_data, f"输出电流分布 (DAC={step_val}mV)", '#28a745')
                    stats_html = get_i_stats_html(step_data, '#28a745')
                    st.plotly_chart(fig_hist, use_container_width=True)
                    st.markdown(stats_html, unsafe_allow_html=True)
                    hist_htmls_export += f"<h3 style='color:#444; border-bottom: 1px solid #eee; padding-bottom:5px; margin-top:30px;'>⚡ 阶梯驻留抽样：DAC 设定 = {step_val} mV</h3>"
                    hist_htmls_export += f"<div class='chart-container' style='padding-bottom:5px;'>{fig_hist.to_html(full_html=False, include_plotlyjs=False)}{stats_html}</div>"
        else:
            st.warning("⚠️ 侦测到单次连续扫频或各台阶样本量不足。强行绘制高斯直方图缺乏统计学意义，请上传阶梯驻留多次采样的数据以激活此功能。")
            hist_htmls_export += "<p><em>无阶梯驻留抽样数据，微观统计图表未生成。</em></p>"

    # ==========================================
    # 6. Tab_export: 离线交互式报告与计算数据导出
    # ==========================================
    with tab_export:
        st.info("💡 下载的 HTML 档案将包含所有解耦图表、校准残差图及微观统计，适合留存用于 DOE 或对账。")
        
        df_export = df_valid.copy()
        df_export['Error_from_DAC_Voltage(mV)'] = df_export[col_v_act] - df_export[col_v_theo]
        df_export['Error_from_DAC_Equivalent(uA)'] = (df_export['Error_from_DAC_Voltage(mV)'] / R_set) * 1000
        df_export['Error_from_Howland_Pure(uA)'] = (df_export[col_i_act] - (df_export[col_v_act] / R_set)) * 1000
        df_export['Error_System_Total(uA)'] = (df_export[col_i_act] - df_export[col_i_theo]) * 1000
        df_export['Calibrated_Residual(uA)'] = err_cal_sys_i_all * 1000
        
        trace_html = fig_trace.to_html(full_html=False, include_plotlyjs=True)
        tue_html = fig_tue.to_html(full_html=False, include_plotlyjs=False)
        inl_html = fig_inl.to_html(full_html=False, include_plotlyjs=False)
        cal_html = fig_cal.to_html(full_html=False, include_plotlyjs=False)
        f1_html = fig_f1.to_html(full_html=False, include_plotlyjs=False)
        f2_html = fig_f2.to_html(full_html=False, include_plotlyjs=False)
        
        html_report = f"""
        <!DOCTYPE html><html><head><meta charset="utf-8"><title>Howland 电流源分析报告</title>
        <style>
            * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
            body {{ font-family: 'Segoe UI', Tahoma, Verdana, sans-serif; padding: 30px; color: #2c3e50; line-height: 1.6; background-color: #f4f7f6; }}
            .container {{ max-width: 1200px; margin: auto; background: white; padding: 40px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-radius: 8px; }}
            .print-btn {{ position: fixed; top: 30px; right: 40px; background-color: #d9534f; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; z-index: 1000; }}
            h1 {{ color: #004085; border-bottom: 2px solid #004085; padding-bottom: 10px; text-align: center; }}
            h2 {{ color: #0056b3; margin-top: 40px; border-left: 4px solid #0056b3; padding-left: 10px; }}
            .grid-container {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-top: 20px; }}
            .grid-2col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 10px; }}
            .metric-card {{ background-color: #f8f9fa; border-top: 4px solid #007bff; border-radius: 6px; padding: 20px; border: 1px solid #e9ecef; }}
            .metric-card p {{ margin: 8px 0; font-size: 14px; }}
            .acc-txt {{ color: #d9534f; font-weight: bold; font-family: monospace; font-size: 14px; background: #fff3f3; padding: 4px; border-radius: 4px; }}
            .chart-container {{ border: 1px solid #ddd; padding: 15px; background: #fff; margin-bottom: 20px; border-radius: 5px; }}
            .math-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; background: white; font-size: 14px; }}
            .math-table th {{ background-color: #0056b3; color: white; padding: 12px; text-align: left; border: 1px solid #ddd; }}
            .math-table td {{ padding: 12px; border: 1px solid #ddd; vertical-align: top; }}
            @media print {{ .print-btn {{ display: none !important; }} .chart-container, .metric-card, .math-table {{ page-break-inside: avoid; }} }}
        </style></head><body>
            <button class="print-btn" onclick="window.print()">🖨️ 另存为 PDF</button>
            <div class="container">
                <h1>⚡ Howland 电流源 V-I 信号链分析报告</h1>
                <p style="text-align: center;"><b>测试条件：</b>设定电阻 R_set = <b>{R_set} Ω</b> | 满量程电流 FS_I = <b>{FS_I} mA</b> | 扩展系数 K = <b>{k_factor}</b></p>
                
                <h2>1. 三节点全链路精度解构</h2>
                <div class="grid-container">
                    <div class="metric-card" style="border-top-color: #ffc107;">
                        <h3 style="margin-top:0;">模块 1: 前端 DAC 电压域</h3>
                        <p>实际增益 (k): <b>{k_dac:.6f} V/V</b></p>
                        <p>零点失调 (b): <b>{b_dac:.4f} mV</b></p>
                        <p>R²: <b>{r2_dac:.6f}</b></p>
                        <p class="acc-txt">精度: ±({acc_dac_rdg:.4f}% R + {acc_dac_fs:.4f}% FS)</p>
                    </div>
                    <div class="metric-card" style="border-top-color: #17a2b8;">
                        <h3 style="margin-top:0;">模块 2: Howland 纯转换域</h3>
                        <p>实际跨导 Gm: <b>{k_hw*1000:.4f} mA/V</b></p>
                        <p>偏置电流 (I_os): <b>{b_hw*1000:.4f} μA</b></p>
                        <p>R²: <b>{r2_hw:.6f}</b></p>
                        <p class="acc-txt">精度: ±({acc_hw_rdg:.4f}% R + {acc_hw_fs:.4f}% FS)</p>
                    </div>
                    <div class="metric-card" style="border-top-color: #28a745;">
                        <h3 style="margin-top:0;">模块 3: 系统端到端全链路</h3>
                        <p>系统等效跨导: <b>{k_sys*1000:.4f} mA/V</b></p>
                        <p>总失调电流: <b>{b_sys*1000:.4f} μA</b></p>
                        <p>R²: <b>{r2_sys:.6f}</b></p>
                        <p class="acc-txt">精度: ±({acc_sys_rdg:.4f}% R + {acc_sys_fs:.4f}% FS)</p>
                    </div>
                </div>

                <h2>2. ✨ 系统级线性校准后残差评估</h2>
                <div class="metric-card" style="border-left: 5px solid #28a745; margin-top: 10px;">
                    <div class="grid-2col">
                        <div><p>最大绝对极值极限：<b style="color: #d9534f;">{max_err_cal_sys*1000:.4f} μA</b></p>
                        <p>{lbl_rms}：<b style="color: #28a745;">{rms_sys*1000:.4f} μA</b></p>
                        <p>{lbl_pp}：<b style="color: #d9534f;">{pp_sys*1000:.4f} μA</b></p></div>
                        <div><p>全局 ENOB：<b style="color: #28a745;">{enob_sys}</b></p>
                        <p>全局 NFR (无噪声分辨率)：<b style="color: #28a745;">{nfr_sys}</b></p></div>
                    </div>
                </div>
                <div class="chart-container" style="margin-top: 15px;">{cal_html}</div>

                <h2>3. 🔪 绝对电流误差溯源拆解图</h2><div class="chart-container">{trace_html}</div>
                <h2>4. 系统全链路绝对误差图 (TUE)</h2><div class="chart-container">{tue_html}</div>
                <h2>5. 系统各级积分非线性对比 (INL)</h2><div class="chart-container">{inl_html}</div>
                <h2>6. 硬件传递函数拟合图</h2>
                <div class="grid-2col">
                    <div class="chart-container">{f1_html}</div>
                    <div class="chart-container">{f2_html}</div>
                </div>
                <h2>7. 📊 选定电压点微观统计与底噪直方图</h2>{hist_htmls_export}
                
                <div style="page-break-before: always;"></div>
                <h2>📚 附录：Howland 电流源核心测试计算对账指南</h2>
                <table class="math-table">
                    <tr><th style="width: 15%;">测试项 (Metric)</th><th style="width: 35%;">底层数学计算模型 (Formula)</th><th style="width: 50%;">工程评估意义与对账依据 (Significance)</th></tr>
                    <tr><td><b>实际跨导 (Gm)</b></td><td><code>Gm = ΔI_out_actual / ΔV_dac_actual</code></td><td>提取纯粹的 V-I 转换斜率。理想应等于 1/R_set。该值的偏离由电阻网络(R_gear)的比例失配公差导致。</td></tr>
                    <tr><td><b>失调电流 (I_os)</b></td><td><code>b_hw = I_out_actual - Gm × V_dac_actual</code></td><td>主要由主运放的输入失调电压 (Vos) 在 R_set 上产生的压降，以及偏置电流 (I_bias) 导致。</td></tr>
                    <tr><td><b>校准后残差</b></td><td><code>Residual = I_out_actual - (k_sys × V_dac_theo + b_sys)</code></td><td>模拟 MCU 两点校准后，系统无法通过软件轻易消除的终极残余误差（非线性弯曲 + 动态热噪声）。</td></tr>
                    <tr><td><b>积分非线性 (INL)</b></td><td><code>INL = I_out_actual - (Gm × V_dac_actual + I_os)</code></td><td>强制剥离可通过两点校准轻易消除的线性漂移，暴露出运放交越失真、非对称偏置引起的真实弯曲度。</td></tr>
                    <tr><td><b>局部底噪 (RMS)</b></td><td><code>Std = √[Σ(I_i - Mean)² / (N-1)]</code></td><td>衡量特定台阶下输出电流的离散程度（热噪声均方根）。对恒流源稳定性评估至关重要。</td></tr>
                </table>
            </div>
        </body>
        </html>
        """
        
        b64_html = base64.b64encode(html_report.encode('utf-8')).decode()
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            buffer_export = io.BytesIO()
            df_export.to_excel(buffer_export, index=False)
            st.download_button("📥 导出宽表数据 (Excel, 包含校准残差)", data=buffer_export.getvalue(), file_name="Howland_DC_Analysis_Data.xlsx")
        with col_btn2:
            st.markdown(f'<a href="data:text/html;base64,{b64_html}" download="Howland电流源_分析报告.html" target="_blank"><button style="background-color:#0056b3;color:white;padding:10px 20px;font-weight:bold;border:none;border-radius:5px;cursor:pointer;width:100%;">📊 下载交互式直流信号分析报告 (HTML)</button></a>', unsafe_allow_html=True)
else:
    st.info("👈 请在左侧上传包含设定电压与实际输出电流的扫频测试数据 (如 240.xlsx)。")