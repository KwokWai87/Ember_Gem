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
    page_title="外部ADC精度分析台", 
    page_icon="🔬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .metric-sub { font-size: 0.85em; color: #666; margin-top: -10px; margin-bottom: 10px; padding: 8px; background: #f8f9fa; border-radius: 4px; border-left: 4px solid #ccc; line-height: 1.6;}
    .metric-sub-afe { border-left-color: #007bff; }
    .metric-sub-ext { border-left-color: #28a745; }
    .acc-text { color: #d9534f; font-weight: bold; font-family: monospace; font-size: 1.05em; }
    .step-box { background-color: #f0f7ff; padding: 12px 15px; border-radius: 5px; border-left: 4px solid #0056b3; margin-bottom: 15px; font-size: 0.95em;}
    </style>
    """, unsafe_allow_html=True)

def apply_chart_style(fig, title, x_title, y_title):
    fig.update_layout(
        title=title, plot_bgcolor='white', paper_bgcolor='white', hovermode="x unified",
        margin=dict(l=80, r=40, t=60, b=80), 
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5) 
    )
    fig.update_xaxes(title_text=x_title, showgrid=True, gridwidth=1, gridcolor='LightGray', zeroline=True, zerolinecolor='gray')
    fig.update_yaxes(title_text=y_title, showgrid=True, gridwidth=1, gridcolor='LightGray', zeroline=True, zerolinecolor='gray')
    return fig

# ==========================================
# 1. 数据导入与初始化
# ==========================================
st.sidebar.title("📁 数据导入与分析配置")
uploaded_file = st.sidebar.file_uploader("上传测试数据 (CSV/Excel)", type=["csv", "xlsx", "xls"])

@st.cache_data
def load_demo_data():
    vins_steps = np.linspace(10, 5000, 19) 
    vins = np.repeat(vins_steps, 50) 
    noise_afe = np.random.normal(0, 0.15, len(vins))
    noise_adc = np.random.normal(0, 0.08, len(vins))
    df = pd.DataFrame({
        'Num': np.arange(1, len(vins) + 1),
        'Target': vins,
        'DMM_1_VOLT(mV)': vins + np.random.normal(0, 0.01, len(vins)),
        'DMM_2_VOLT(mV)': vins * 0.125 + 0.5 + noise_afe,
        'ADS1219_Read_volt_1(mV)': (vins * 0.125 + 0.5 + noise_afe) * 1.002 + 0.2 + noise_adc
    })
    return df

df_raw = pd.read_csv(uploaded_file) if uploaded_file else load_demo_data()

# ==========================================
# 2. 核心计算引擎与动态列绑定
# ==========================================
if df_raw is not None:
    df_raw.columns = df_raw.columns.str.strip()
    df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()]
    all_columns = df_raw.columns.tolist()

    # 智能查找默认列索引
    def get_col_idx(kw_list):
        return next((i for i, c in enumerate(all_columns) if any(kw.upper() in c.upper() for kw in kw_list)), 0)

    st.sidebar.markdown("### 🗂️ 核心数据列绑定")
    col_set = st.sidebar.selectbox("🎯 目标台阶列 (Target)", all_columns, index=get_col_idx(['TARGET', 'SET']))
    col_vin = st.sidebar.selectbox("1️⃣ DMM1 列 (输入源基准)", all_columns, index=get_col_idx(['DMM_1', 'VIN', 'DMM1']))
    col_vafe = st.sidebar.selectbox("2️⃣ DMM2 列 (AFE输出)", all_columns, index=get_col_idx(['DMM_2', 'VAFE', 'DMM2']))
    col_vadc_ext = st.sidebar.selectbox("3️⃣ ADC 测量值列", all_columns, index=get_col_idx(['ADS1219', 'ADC']))
    
    col_vadc_ext_adj = col_vadc_ext + '_Adjusted(mV)'
    
    for col in [col_set, col_vin, col_vafe, col_vadc_ext]:
        if col in df_raw.columns:
            df_raw[col] = pd.to_numeric(df_raw[col].astype(str).str.strip(), errors='coerce')
    df_valid = df_raw.dropna(subset=[col_set, col_vin, col_vafe, col_vadc_ext]).copy()

    if len(df_valid) < 2:
        st.error("🚨 致命数据错误：清洗后有效数据少于 2 行！请检查绑定的列是否包含有效数值。")
        st.stop()
    
    st.sidebar.markdown("### 🔌 硬件参数设定")
    vref_actual = st.sidebar.number_input("外部基准实际电压 (V)", value=2.5000, step=0.0001, format="%.4f")
    df_valid[col_vadc_ext_adj] = df_valid[col_vadc_ext] * (vref_actual / 2.5)

    k_factor = st.sidebar.selectbox("扩展不确定度 (K 因子)", [1, 2, 3], index=1)
    fs_input = st.sidebar.number_input("设定绝对满量程 (FS_IN) [mV]", value=5000.0, step=100.0)
    nom_gain_afe = st.sidebar.number_input("系统标称 AFE 增益", value=0.125, format="%.3f")
    nom_gain_adc = st.sidebar.number_input("系统标称 ADC 增益", value=1.000, format="%.3f")

    st.sidebar.markdown("### 🧮 误差折算参考面")
    err_mode = st.sidebar.radio("选择误差指标的基准节点：", ["折算至输入端 (RTI) - 推荐", "直接测量输出端 (RTO)"], index=0)
    is_rti = err_mode.startswith("折算")
    unit_str = "RTI" if is_rti else "RTO"

    # --- 台阶识别与强制对齐 ---
    df_valid['Step_ID'] = df_valid[col_set]
    step_stats = df_valid.groupby(col_set).size().reset_index(name='Width (Samples)')
    step_stats = step_stats.rename(columns={col_set: 'Target Level (mV)'})
    total_steps, avg_width = len(step_stats), step_stats['Width (Samples)'].mean()
    
    st.sidebar.info(f"✅ 识别 {total_steps} 个台阶，平均宽度 {avg_width:.1f}")

    df_valid = df_valid.sort_values(by=col_vin).reset_index(drop=True)
    df_mean = df_valid.groupby('Step_ID', as_index=False).mean().sort_values(by='Step_ID').reset_index(drop=True)
    df_max = df_valid.groupby('Step_ID', as_index=False).max().sort_values(by='Step_ID').reset_index(drop=True)
    df_min = df_valid.groupby('Step_ID', as_index=False).min().sort_values(by='Step_ID').reset_index(drop=True)

    # --- 数学引擎 ---
    def get_fit_metrics(x_arr, y_arr):
        k, b = np.polyfit(x_arr, y_arr, 1)
        fit_y = k * x_arr + b
        r2 = 1 - (np.sum((y_arr - fit_y)**2) / np.sum((y_arr - np.mean(y_arr))**2)) if np.sum((y_arr - np.mean(y_arr))**2) != 0 else 1.0
        return k, b, r2, fit_y

    def calc_acc(x_arr, y_arr, k_ideal, fs_in_val, k_cov):
        k_ep = (np.max(y_arr) - np.min(y_arr)) / (np.max(x_arr) - np.min(x_arr))
        b_ep = np.min(y_arr) - k_ep * np.min(x_arr)
        rmse = np.sqrt(np.mean((y_arr - (k_ep * x_arr + b_ep))**2))
        pct_rdg = (abs(k_ep - k_ideal) / k_ideal) * 100
        pct_fs = ((abs(b_ep) + k_cov * rmse) / (fs_in_val * k_ideal)) * 100
        return pct_rdg, pct_fs

    v_in = np.ravel(df_mean[col_vin])
    v_afe = np.ravel(df_mean[col_vafe])
    v_adc = np.ravel(df_mean[col_vadc_ext_adj])
    v_afe_max = np.ravel(df_max[col_vafe])
    v_afe_min = np.ravel(df_min[col_vafe])
    v_adc_max = np.ravel(df_max[col_vadc_ext_adj])
    v_adc_min = np.ravel(df_min[col_vadc_ext_adj])

    k_afe, b_afe, r2_afe, fit_afe = get_fit_metrics(v_in, v_afe)
    k_sys, b_sys, r2_sys, fit_sys = get_fit_metrics(v_in, v_adc)
    
    acc_afe_rdg, acc_afe_fs = calc_acc(v_in, v_afe, nom_gain_afe, fs_input, k_factor)
    acc_sys_rdg, acc_sys_fs = calc_acc(v_in, v_adc, nom_gain_afe*nom_gain_adc, fs_input, k_factor)

    g_afe_ideal = nom_gain_afe
    g_sys_ideal = nom_gain_afe * nom_gain_adc

    # TUE 包络矩阵 (绝对误差，除以理想增益进行输入折算)
    err_afe_mean = (v_afe - v_in * g_afe_ideal) / (g_afe_ideal if is_rti else 1.0)
    err_afe_max = (v_afe_max - v_in * g_afe_ideal) / (g_afe_ideal if is_rti else 1.0)
    err_afe_min = (v_afe_min - v_in * g_afe_ideal) / (g_afe_ideal if is_rti else 1.0)

    err_sys_mean = (v_adc - v_in * g_sys_ideal) / (g_sys_ideal if is_rti else 1.0)
    err_sys_max = (v_adc_max - v_in * g_sys_ideal) / (g_sys_ideal if is_rti else 1.0)
    err_sys_min = (v_adc_min - v_in * g_sys_ideal) / (g_sys_ideal if is_rti else 1.0)
    
    # INL 骨架：转换为 %FS
    inl_afe_mv = (v_afe - fit_afe) / (k_afe if is_rti else 1.0)
    inl_sys_mv = (v_adc - fit_sys) / (k_sys if is_rti else 1.0)

    fs_afe_ref = fs_input if is_rti else (fs_input * g_afe_ideal)
    fs_sys_ref = fs_input if is_rti else (fs_input * g_sys_ideal)

    inl_afe_fs = (inl_afe_mv / fs_afe_ref) * 100
    inl_sys_fs = (inl_sys_mv / fs_sys_ref) * 100

    # 全样本动态特性解析
    val_vin_all = np.ravel(df_valid[col_vin])
    val_adc_all = np.ravel(df_valid[col_vadc_ext_adj])
    val_adc_mean_all = np.ravel(df_valid.groupby('Step_ID')[col_vadc_ext_adj].transform('mean'))
    
    if is_rti:
        err_cal_sys_all = (val_adc_all - b_sys) / k_sys - val_vin_all
        noise_ext = (val_adc_all - val_adc_mean_all) / k_sys
        fs_noise = fs_input
    else:
        err_cal_sys_all = val_adc_all - (val_vin_all * k_sys + b_sys)
        noise_ext = val_adc_all - val_adc_mean_all
        fs_noise = fs_input * g_sys_ideal

    rms_ext = np.std(noise_ext, ddof=1) if len(noise_ext) > 1 else 0.0
    pp_ext = np.max(noise_ext) - np.min(noise_ext) if len(noise_ext) > 1 else 0.0
    enob_ext_str = f"{np.log2(fs_noise / rms_ext):.2f} Bits" if rms_ext > 0 else "N/A"
    nfr_ext_str = f"{np.log2(fs_noise / pp_ext):.2f} Bits" if pp_ext > 0 else "N/A"

    # ==========================================
    # 3. 矩阵式诊断 Dashboard
    # ==========================================
    st.title("🔬 外部 ADC 单路高精度分析台")
    st.markdown(f"<div class='step-box'><b>🎯 测控台阶概况：</b> 目标列 <code>{col_set}</code> | 共识别 <b>{total_steps}</b> 个台阶 | 平均采样宽度 <b>{avg_width:.1f}</b> 点。<br><b>🧮 当前分析视角：</b> <span style='color:#d9534f;font-weight:bold;'>{err_mode}</span></div>", unsafe_allow_html=True)

    col_1, col_2, col_3 = st.columns(3)
    with col_1:
        st.info("🛠️ **模块 1: 前端 AFE 本底性能**")
        st.metric("实际增益 (k)", f"{k_afe:.6f} V/V")
        st.metric("最佳失调 (b)", f"{b_afe:.4f} mV")
        st.markdown(f"<div class='metric-sub metric-sub-afe'><b>R²:</b> {r2_afe:.6f}<br><b>精度:</b> <span class='acc-text'>±({acc_afe_rdg:.4f}% R + {acc_afe_fs:.4f}% FS)</span></div>", unsafe_allow_html=True)
        
    with col_2:
        st.success("🔗 **模块 2: 全链路 (AFE + ADC) 性能**")
        st.metric("实际系统增益 (k)", f"{k_sys:.6f}")
        st.metric("最佳系统失调 (b)", f"{b_sys:.4f} mV")
        st.markdown(f"<div class='metric-sub metric-sub-ext'><b>R²:</b> {r2_sys:.6f}<br><b>精度:</b> <span class='acc-text'>±({acc_sys_rdg:.4f}% R + {acc_sys_fs:.4f}% FS)</span></div>", unsafe_allow_html=True)
        
    with col_3:
        st.warning(f"✨ **模块 3: 动态特征 ({unit_str})**")
        st.metric("底噪 RMS (1σ)", f"{rms_ext:.4f} mV")
        st.metric("极限跳动 (P-P)", f"{pp_ext:.4f} mV")
        st.markdown(f"<div class='metric-sub' style='border-left-color: #ffc107;'><b>有效位数 (ENOB):</b> {enob_ext_str}<br><b>无噪声分辨率 (NFR):</b> {nfr_ext_str}</div>", unsafe_allow_html=True)

    st.divider()

    # ==========================================
    # 4. 核心图表构建
    # ==========================================
    fig_tue = go.Figure()
    fig_tue.add_trace(go.Scatter(x=v_in, y=err_sys_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'))
    fig_tue.add_trace(go.Scatter(x=v_in, y=err_sys_min, mode='lines', fill='tonexty', fillcolor='rgba(40,167,69,0.2)', line=dict(width=0), showlegend=False))
    fig_tue.add_trace(go.Scatter(x=v_in, y=err_sys_mean, mode='lines+markers', name='全链路 TUE', line=dict(color='#28a745', width=2)))
    apply_chart_style(fig_tue, f"系统级绝对误差追踪 [{unit_str}]", "物理输入 (mV)", f"TUE 误差 (mV, {unit_str})")

    # 更新 INL 图表为 %FS
    fig_inl = go.Figure()
    fig_inl.add_trace(go.Scatter(x=v_in, y=inl_afe_fs, mode='lines', name="AFE 基底 INL", line=dict(color='gray', width=2, dash='dot')))
    fig_inl.add_trace(go.Scatter(x=v_in, y=inl_sys_fs, mode='lines+markers', name="全链路 INL", line=dict(color='#28a745', width=2)))
    apply_chart_style(fig_inl, f"静态非线性骨架分析 (INL) [%FS]", "物理输入 (mV)", f"INL 残差 (%FS)")

    fig_trace = go.Figure()
    fig_trace.add_trace(go.Scatter(x=v_in, y=err_afe_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'))
    fig_trace.add_trace(go.Scatter(x=v_in, y=err_afe_min, mode='lines', fill='tonexty', fillcolor='rgba(0,123,255,0.15)', line=dict(width=0), name='AFE 波动带'))
    fig_trace.add_trace(go.Scatter(x=v_in, y=err_afe_mean, mode='lines', name=f'[阶段1] AFE 误差 ({unit_str})', line=dict(color='#007bff', width=2.5)))
    fig_trace.add_trace(go.Scatter(x=v_in, y=err_sys_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'))
    fig_trace.add_trace(go.Scatter(x=v_in, y=err_sys_min, mode='lines', fill='tonexty', fillcolor='rgba(40,167,69,0.15)', line=dict(width=0), name='全链路波动带'))
    fig_trace.add_trace(go.Scatter(x=v_in, y=err_sys_mean, mode='lines', name=f'[综合] 全链路误差 ({unit_str})', line=dict(color='#28a745', width=2.5, dash='dot')))
    apply_chart_style(fig_trace, f"级联包络误差溯源 [{unit_str}]", "物理输入 (mV)", f"误差幅度 (mV, {unit_str})")

    fig_cal = go.Figure()
    fig_cal.add_trace(go.Scatter(x=val_vin_all, y=err_cal_sys_all, mode='markers', marker=dict(size=4, opacity=0.3, color='#28a745'), name="动态残差"))
    fig_cal.add_hline(y=0, line_dash="dash", line_color="black")
    apply_chart_style(fig_cal, f"校准后极限残差 (动态宽带噪声) [{unit_str}]", "物理输入 (mV)", f"动态残差 (mV, {unit_str})")

    # ==========================================
    # 5. UI 渲染与 HTML 报告导出
    # ==========================================
    tab_tue, tab_inl, tab_trace, tab_cal, tab_hist, tab_export = st.tabs([
        "🔮 绝对误差 (TUE)", "🏹 积分非线性 (INL %FS)", "🔪 级联包络拆解", "✨ 校准后极限残差", "📊 阶梯微观统计", "💾 离线报告导出"
    ])

    with tab_tue: st.plotly_chart(fig_tue, use_container_width=True)
    with tab_inl: st.plotly_chart(fig_inl, use_container_width=True)
    with tab_trace: 
        st.markdown(f"### 🔪 AFE 与 全链路硬件波动独立对比 ({unit_str} 模式)")
        st.plotly_chart(fig_trace, use_container_width=True)
    with tab_cal: st.plotly_chart(fig_cal, use_container_width=True)

    hist_htmls_export = ""
    with tab_hist:
        st.markdown(f"### 🎯 指定设定电压点 - 局部微观抗干扰诊断")
        st.info("💡 评估各节点测试底噪是否为纯净的“高斯热噪声”。如果输入源 (DMM1) 本身跳动极大，全链路的跳动就不一定是 ADC 的问题。")

        # 增加数据源切换 Radio
        ana_obj = st.radio("🔍 选择当前图表分析对象：", ["ADC 最终输出", "DMM1 (输入源纯净度)", "DMM2 (AFE 级输出)"], horizontal=True)

        unique_steps = df_valid['Step_ID'].unique().tolist()
        default_sel = [unique_steps[len(unique_steps)//2]] if unique_steps else []
        selected_steps = st.multiselect("请点选需要提取高斯底噪的设定电压台阶：", options=unique_steps, default=default_sel)

        def get_dmm_stats_html(series, color):
            N = len(series)
            if N < 2: return ""
            mean_val, std_val = series.mean(), series.std(ddof=1)
            max_val, min_val = series.max(), series.min()
            return f"""
            <div style='background: #f8f9fa; border-left: 4px solid {color}; padding: 12px 15px; margin-top: 15px; margin-bottom: 15px; border-radius: 4px; font-size: 0.9em; color: #333;'>
                <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; line-height: 1.5;'>
                    <div><b>N (样本数):</b> {N}</div>
                    <div><b>Mean (均值):</b> {mean_val:.4f} mV</div>
                    <div><b>Std/RMS:</b> {std_val:.4f} mV</div>
                    <div><b>P-P (峰峰值):</b> {max_val - min_val:.4f} mV</div>
                    <div><b>Max:</b> {max_val:.4f} mV</div>
                    <div><b>Min:</b> {min_val:.4f} mV</div>
                </div>
            </div>
            """

        def plot_histogram_with_fit(data, title, color):
            data_clean = pd.to_numeric(pd.Series(data), errors='coerce').dropna().values
            fig = go.Figure()
            N = len(data_clean)
            if N < 2: return fig
            
            mean_val, std_val = np.mean(data_clean), np.std(data_clean, ddof=1)
            optimal_bins = max(5, int(np.sqrt(N)))
            counts, bins = np.histogram(data_clean, bins=optimal_bins)
            bin_centers = 0.5 * (bins[:-1] + bins[1:])
            bin_width = bins[1] - bins[0] if len(bins) > 1 else 1
            
            fig.add_trace(go.Bar(
                x=bin_centers, y=counts, width=bin_width, name='实测数量', 
                marker_color=color, opacity=0.6
            ))
            
            if std_val > 0:
                x_range = np.linspace(np.min(data_clean) - bin_width, np.max(data_clean) + bin_width, 200)
                pdf_scaled = stats.norm.pdf(x_range, mean_val, std_val) * N * bin_width
                fig.add_trace(go.Scatter(
                    x=x_range, y=pdf_scaled, mode='lines', name='理论高斯包络', 
                    line=dict(color='black', dash='dash', width=2.5)
                ))
            
            fig.update_layout(
                title=title, barmode='overlay', plot_bgcolor='white', hovermode="x", bargap=0,
                margin=dict(t=40, b=40, l=40, r=40), legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5)
            )
            fig.update_xaxes(title_text=f"测量电压 (mV)", showgrid=True, gridcolor='LightGray')
            fig.update_yaxes(title_text="数量 (Count)", showgrid=True, gridcolor='LightGray')
            return fig

        if selected_steps:
            for step_target in selected_steps:
                step_data = df_valid[df_valid['Step_ID'] == step_target]
                if len(step_data) == 0: continue
                
                # 动态分配给 UI 界面显示的数据
                if ana_obj.startswith("ADC"):
                    ui_vals = (step_data[col_vadc_ext_adj] - b_sys) / k_sys if is_rti else step_data[col_vadc_ext_adj]
                    c_color, c_title = '#28a745', f"台阶 {step_target} mV: ADC 分布 [{unit_str}]"
                elif ana_obj.startswith("DMM1"):
                    ui_vals = step_data[col_vin]
                    c_color, c_title = '#6c757d', f"台阶 {step_target} mV: DMM1 分布 [源头绝对输入]"
                else:
                    ui_vals = (step_data[col_vafe] - b_afe) / k_afe if is_rti else step_data[col_vafe]
                    c_color, c_title = '#007bff', f"台阶 {step_target} mV: DMM2 分布 [{unit_str}]"

                fig_hist_ui = plot_histogram_with_fit(ui_vals, c_title, c_color)
                stats_html_ui = get_dmm_stats_html(ui_vals, c_color)

                st.markdown(f"#### ⚡ {c_title}")
                st.plotly_chart(fig_hist_ui, use_container_width=True)
                st.markdown(stats_html_ui, unsafe_allow_html=True)
                st.divider()

                # ==== 为 HTML 报告隐式生成三列全景数据 ====
                vals_dmm1 = step_data[col_vin]
                vals_dmm2 = (step_data[col_vafe] - b_afe) / k_afe if is_rti else step_data[col_vafe]
                vals_adc  = (step_data[col_vadc_ext_adj] - b_sys) / k_sys if is_rti else step_data[col_vadc_ext_adj]

                fig_1 = plot_histogram_with_fit(vals_dmm1, "1. 源头基准 (DMM1)", '#6c757d')
                fig_2 = plot_histogram_with_fit(vals_dmm2, "2. AFE输出 (DMM2)", '#007bff')
                fig_3 = plot_histogram_with_fit(vals_adc, "3. ADC最终输出", '#28a745')

                hist_htmls_export += f"<h3 style='color:#444; border-bottom: 1px solid #eee; padding-bottom:5px; margin-top:30px;'>⚡ 设定点 {step_target} mV : 链路噪声传播全景图</h3>"
                hist_htmls_export += "<div class='grid-3col' style='gap: 15px; margin-top: 10px;'>"
                hist_htmls_export += f"<div class='chart-box' style='padding: 10px;'>{fig_1.to_html(full_html=False, include_plotlyjs=False)}{get_dmm_stats_html(vals_dmm1, '#6c757d')}</div>"
                hist_htmls_export += f"<div class='chart-box' style='padding: 10px;'>{fig_2.to_html(full_html=False, include_plotlyjs=False)}{get_dmm_stats_html(vals_dmm2, '#007bff')}</div>"
                hist_htmls_export += f"<div class='chart-box' style='padding: 10px;'>{fig_3.to_html(full_html=False, include_plotlyjs=False)}{get_dmm_stats_html(vals_adc, '#28a745')}</div>"
                hist_htmls_export += "</div>"

    with tab_export:
        st.info(f"💡 当前导出报告将采用 **{err_mode}** 视角，INL 将以 **%FS** 呈现。统计图表将自动输出 DMM1、DMM2、ADC 的三列横向对比视图。")
        
        step_html_table = step_stats.to_html(index=False, classes="math-table", border=0)
        trace_html = fig_trace.to_html(full_html=False, include_plotlyjs=True)
        tue_html = fig_tue.to_html(full_html=False, include_plotlyjs=False)
        inl_html = fig_inl.to_html(full_html=False, include_plotlyjs=False)
        cal_html = fig_cal.to_html(full_html=False, include_plotlyjs=False)
        
        html_report = f"""
        <!DOCTYPE html><html><head><meta charset="utf-8"><title>ADC单路精度诊断报告</title>
        <style>
            * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; padding: 30px; color: #2c3e50; background: #f4f7f6; line-height: 1.6; }}
            .container {{ max-width: 1400px; margin: auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            h1 {{ color: #004085; border-bottom: 2px solid #004085; padding-bottom: 10px; text-align: center; }}
            h2 {{ color: #0056b3; margin-top: 40px; border-left: 4px solid #0056b3; padding-left: 10px; }}
            .grid-3col {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 20px; }}
            .metric-card {{ background: #f8f9fa; border-top: 4px solid #007bff; border-radius: 6px; padding: 20px; border: 1px solid #e9ecef; }}
            .acc-txt {{ color: #d9534f; font-weight: bold; font-family: monospace; font-size: 14px; background: #fff3f3; padding: 4px; border-radius: 4px; display: inline-block; margin-top: 5px;}}
            .chart-box {{ border: 1px solid #ddd; padding: 15px; background: #fff; margin-bottom: 20px; border-radius: 5px; page-break-inside: avoid; overflow: hidden; }}
            .math-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; text-align: left; font-size: 14px; }}
            .math-table th {{ background: #f0f7ff; color: #0056b3; padding: 12px; border: 1px solid #ddd; }}
            .math-table td {{ padding: 12px; border: 1px solid #ddd; }}
        </style></head><body>
            <div class="container">
                <h1>🔬 外部 ADC 单路高精度分析报告</h1>
                <p style="text-align:center; color:#666;">置信区间 K = {k_factor} | 设定 FS = {fs_input} mV | 视角 = {err_mode}</p>
                
                <h2>1. 🎯 测控台阶自动识别统计</h2>
                <p>扫描列 <code>{col_set}</code> 共提取到 <b>{total_steps}</b> 个台阶，平均采样宽度 <b>{avg_width:.1f}</b> 点。</p>
                <div style="max-height: 250px; overflow-y: auto; border: 1px solid #ddd; text-align: center;">{step_html_table}</div>

                <h2>2. ⚙️ 全链路核心精度诊断</h2>
                <div class="grid-3col">
                    <div class="metric-card">
                        <h3 style="margin-top:0; color:#0056b3;">[级联 1] AFE 本底性能</h3>
                        <p>实际增益: <b>{k_afe:.6f}</b></p>
                        <p>静态线性度: <b>{r2_afe:.6f}</b></p>
                        <div class="acc-txt">精度: ±({acc_afe_rdg:.4f}% R + {acc_afe_fs:.4f}% FS)</div>
                    </div>
                    <div class="metric-card" style="border-top-color: #28a745;">
                        <h3 style="margin-top:0; color:#155724;">[综合] 全链路系统性能</h3>
                        <p>实际增益: <b>{k_sys:.6f}</b></p>
                        <p>静态线性度: <b>{r2_sys:.6f}</b></p>
                        <div class="acc-txt">精度: ±({acc_sys_rdg:.4f}% R + {acc_sys_fs:.4f}% FS)</div>
                    </div>
                    <div class="metric-card" style="border-top-color: #ffc107;">
                        <h3 style="margin-top:0; color:#856404;">✨ 动态特征 ({unit_str})</h3>
                        <p>热噪声 RMS (1σ): <b>{rms_ext:.4f} mV</b></p>
                        <p>极限跳动 (P-P): <b>{pp_ext:.4f} mV</b></p>
                        <p>有效位数 (ENOB): <b>{enob_ext_str}</b></p>
                    </div>
                </div>

                <h2>3. 🔪 级联包络拆解 (AFE 蓝 vs 全链路 绿) [{unit_str}]</h2><div class="chart-box">{trace_html}</div>
                <h2>4. 🔮 系统绝对误差包络 (TUE) [{unit_str}]</h2><div class="chart-box">{tue_html}</div>
                <h2>5. 🏹 静态非线性骨架 (INL) [%FS]</h2><div class="chart-box">{inl_html}</div>
                <h2>6. ✨ 校准后极限残差 (动态底噪) [{unit_str}]</h2><div class="chart-box">{cal_html}</div>
                
                <h2>7. 📊 链路噪声传播全景分析 (定点微观抽样)</h2>
                {hist_htmls_export}

                <h2>8. 📖 关键指标物理意义与计算公式定义</h2>
                <table class="math-table">
                    <tr><th width="20%">指标名称</th><th width="35%">数学定义 / 公式</th><th width="45%">工程物理意义</th></tr>
                    <tr><td><b>绝对误差 (TUE)</b></td><td><code>TUE = V_meas - V_ideal</code></td><td>反映系统端到端的绝对偏差，包含增益、失调和非线性综合表现。</td></tr>
                    <tr><td><b>积分非线性 (INL %FS)</b></td><td><code>INL_(%FS) = [V_meas - (k×V_in + b)] / FS_IN × 100</code></td><td>剥离线性误差后的固有弯曲误差，相对于系统设定满量程的百分比。</td></tr>
                    <tr><td><b>全局/局部标准差 (RMS)</b></td><td><code>Std = √[Σ(x_i - Mean)² / (N-1)]</code></td><td>衡量数据离散程度，等效于交流热噪声均方根值 (1σ)。</td></tr>
                    <tr><td><b>峰峰值噪声 (P-P)</b></td><td><code>P-P = Max - Min</code></td><td>极限噪声边界。能捕捉偶发异常跳动或外部工频干扰。</td></tr>
                    <tr><td><b>无噪声分辨率 (NFR)</b></td><td><code>NFR = log₂( FS_Input / P-P_Noise )</code></td><td>系统在最坏干扰下，输出数字代码完全不跳动的最保守有效位数。</td></tr>
                </table>
            </div>
        </body></html>
        """
        b64_html = base64.b64encode(html_report.encode('utf-8')).decode()
        
        df_export = df_valid.copy()
        df_export['Calibrated_Residual(mV)'] = err_cal_sys_all
        buffer_export = io.BytesIO()
        df_export.to_excel(buffer_export, index=False)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.download_button("📥 导出清洗数据宽表 (Excel)", data=buffer_export.getvalue(), file_name="ADC_Clean_Data.xlsx")
        with col_btn2:
            st.markdown(f'<a href="data:text/html;base64,{b64_html}" download="ADC精度分析报告_{unit_str}.html" target="_blank"><button style="background-color:#0056b3;color:white;padding:10px 20px;font-weight:bold;border:none;border-radius:5px;cursor:pointer;width:100%;">📊 下载深度诊断 HTML 报告 ({unit_str} | %FS)</button></a>', unsafe_allow_html=True)