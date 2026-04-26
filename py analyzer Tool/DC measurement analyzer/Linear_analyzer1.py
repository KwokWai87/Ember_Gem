import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import scipy.stats as stats
import io
import base64

# ==========================================
# 0. 页面配置与全局样式
# ==========================================
st.set_page_config(
    page_title="直流信号分析台", 
    page_icon="🔬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAlert { border-radius: 8px; }
    .metric-sub { font-size: 0.85em; color: #666; margin-top: -10px; margin-bottom: 10px; padding: 8px; background: #f8f9fa; border-radius: 4px; border-left: 4px solid #ccc; line-height: 1.6;}
    .metric-sub-int { border-left-color: #ffc107; }
    .metric-sub-ext { border-left-color: #28a745; }
    .metric-sub-mcu0 { border-left-color: #6f42c1; }
    .metric-sub-mcu1 { border-left-color: #17a2b8; }
    .acc-text { color: #d9534f; font-weight: bold; font-family: monospace; font-size: 1.05em; }
    .formula-ui { background-color: #eef2f5; padding: 12px 15px; border-left: 4px solid #17a2b8; margin-bottom: 15px; font-size: 0.9em; border-radius: 4px;}
    </style>
    """, unsafe_allow_html=True)

def apply_chart_style(fig, title, x_title, y_title):
    fig.update_layout(
        title=title,
        plot_bgcolor='white', 
        paper_bgcolor='white',
        hovermode="x unified",
        margin=dict(l=80, r=40, t=60, b=80), 
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5) 
    )
    fig.update_xaxes(title_text=x_title, automargin=True, showgrid=True, gridwidth=1, gridcolor='LightGray', zeroline=True, zerolinecolor='gray')
    fig.update_yaxes(title_text=y_title, automargin=True, showgrid=True, gridwidth=1, gridcolor='LightGray', zeroline=True, zerolinecolor='gray')
    return fig

# ==========================================
# 1. 侧边栏：导入与配置
# ==========================================
st.sidebar.title("📁 导入与动态补偿")

uploaded_file = st.sidebar.file_uploader("上传扫频测试数据 (CSV/Excel)", type=["csv", "xlsx", "xls"])

use_demo = False
if uploaded_file is None:
    st.sidebar.info("请上传实测数据。或勾选下方使用内置 Demo 体验阶梯扫频闭环。")
    use_demo = st.sidebar.checkbox("使用内置 Demo 数据", value=False)

@st.cache_data
def load_demo_data():
    vins_steps = np.linspace(10, 100, 20)
    vins = np.repeat(vins_steps, 10)
    noise_int = np.random.normal(0, 0.08, len(vins))
    noise_ext = np.random.normal(0, 0.05, len(vins)) + 0.02 * np.sin(np.arange(len(vins)))
    
    df = pd.DataFrame({
        'Num': np.arange(1, len(vins) + 1),
        'SET_VOLT(mV)': vins,
        'DMM_1_VOLT(mV)': vins + np.random.normal(0, 0.01, len(vins)),
        'DMM_2_VOLT(mV)': vins * 16.0 + 0.5 + 2 * np.sin(vins/10),
        'ADS1219_Read_volt_0(mV)': (vins * 16.0 + 0.5 + 2 * np.sin(vins/10)) * 0.998 - 1.2 + noise_int,
        'ADS1219_Read_volt_1(mV)': (vins * 16.0 + 0.5 + 2 * np.sin(vins/10)) * 1.002 + 0.8 + noise_ext,
        'Read_Mcu_ADC_0(mV)': (vins * 16.0 + 0.5 + 2 * np.sin(vins/10)) * 0.992 - 3.5 + noise_int * 2.0, 
        'Read_Mcu_ADC_1(mV)': (vins * 16.0 + 0.5 + 2 * np.sin(vins/10)) * 1.008 + 2.1 + noise_ext * 1.3  
    })
    return df

df_raw = None
if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df_raw = pd.read_csv(uploaded_file)
    else:
        df_raw = pd.read_excel(uploaded_file)
elif use_demo:
    df_raw = load_demo_data()

# ==========================================
# 2. 核心清洗引擎与阶梯解耦算法
# ==========================================
hist_htmls_export = ""
tue_html = ""
inl_html = ""
cal_html = ""
trace_html = ""
sys_ext_fit_html = ""
sys_mcu1_fit_html = ""

if df_raw is not None:
    df_raw.columns = df_raw.columns.str.strip()
    all_columns = df_raw.columns.tolist()
    
    st.sidebar.markdown("### 📊 数据源状态")
    st.sidebar.dataframe(df_raw.head(3), use_container_width=True)
    
    default_idx = 0
    for i, col in enumerate(all_columns):
        if 'SET_VOLT' in col.upper():
            default_idx = i
            break
            
    st.sidebar.markdown("### 🧹 数据清洗与阶梯分组")
    col_set = st.sidebar.selectbox("📐 选择设定电压/分组列 (Step ID)", all_columns, index=default_idx, help="系统将依据此列切分阶梯，提取交流热噪声。")
    
    col_vin = 'DMM_1_VOLT(mV)'
    col_vafe = 'DMM_2_VOLT(mV)'
    col_vadc0 = 'ADS1219_Read_volt_0(mV)'
    col_vadc1 = 'ADS1219_Read_volt_1(mV)'
    col_vadc1_adj = 'ADS1219_Read_volt_1_Adjusted(mV)'
    col_mcu0 = 'Read_Mcu_ADC_0(mV)'
    col_mcu1 = 'Read_Mcu_ADC_1(mV)'
    
    required_cols = [col_set, col_vin, col_vafe, col_vadc0, col_vadc1, col_mcu0, col_mcu1]
    missing_cols = [col for col in required_cols if col not in df_raw.columns and col != col_vadc1_adj]
    
    if missing_cols:
        st.error(f"❌ 数据格式错误！开启四路并联评估缺失关键列: {missing_cols}。")
        st.stop()
    
    for col in required_cols:
        df_raw[col] = pd.to_numeric(df_raw[col].astype(str).str.strip(), errors='coerce')
    
    st.sidebar.markdown("### 🔌 外部基准动态补偿 (仅针对 ADS1219_1)")
    vref_actual = st.sidebar.number_input("外部基准实际电压 (V)", value=2.5000, step=0.0001, format="%.4f")
    vref_scale = vref_actual / 2.5 
    df_raw[col_vadc1_adj] = df_raw[col_vadc1] * vref_scale

    st.sidebar.markdown("### 🧹 直流饱和/过载清洗规则")
    temp_valid = df_raw.dropna(subset=[col_vin])
    if len(temp_valid) == 0:
        st.error("🚨 数据错误：输入的 CSV 文件中未找到有效的数字数据！")
        st.stop()
        
    v_in_min_raw, v_in_max_raw = float(temp_valid[col_vin].min()), float(temp_valid[col_vin].max())
    
    auto_remove_sat = st.sidebar.checkbox("自动剔除 ADC0(ADS) 饱和点", value=True)
    afe_max_limit = st.sidebar.number_input("AFE 合理输出上限 (mV)", value=3000.0, step=100.0)
    
    if v_in_max_raw > v_in_min_raw:
        vin_range = st.sidebar.slider("手动框选 DMM_1 线性评估区间 (mV)", min_value=v_in_min_raw, max_value=v_in_max_raw, value=(v_in_min_raw, v_in_max_raw), step=0.1)
    else:
        vin_range = (v_in_min_raw, v_in_max_raw)
    
    st.sidebar.markdown("### 🔮 系统精度(Accuracy) 与 TUE 设定")
    k_factor = st.sidebar.selectbox("扩展不确定度系数 (K 因子)", [1, 2, 3], index=1)
    fs_input = st.sidebar.number_input("设定绝对满量程 (FS_IN) [mV]", value=5000.0, step=100.0)
    nom_gain_afe = st.sidebar.number_input("系统标称 AFE 增益", value=0.125, format="%.3f")
    nom_gain_adc = st.sidebar.number_input("系统标称 ADC 增益", value=1.000, format="%.3f")
    max_gain_err = st.sidebar.number_input("理论全链路最大增益误差 (%)", value=0.5, step=0.1)
    max_offset = st.sidebar.number_input("理论全链路最大失调极值 (mV)", value=2.0, step=0.1)

    df_valid = df_raw.copy().dropna(subset=[col_set, col_vin, col_vafe, col_vadc0, col_vadc1, col_mcu0, col_mcu1])
    mask_adc_sat = ((df_valid[col_vadc0] >= 2047.9) | (df_valid[col_vadc0] <= -2047.9)) if auto_remove_sat else pd.Series(False, index=df_valid.index)
    mask_afe_err = (df_valid[col_vafe] > afe_max_limit)
    mask_out_of_range = (df_valid[col_vin] < vin_range[0]) | (df_valid[col_vin] > vin_range[1])
    
    mask_invalid = mask_adc_sat | mask_afe_err | mask_out_of_range
    df_clipped = df_valid[mask_invalid].copy()
    df_valid = df_valid[~mask_invalid].copy()
    
    if len(df_valid) < 2:
        st.warning("⚠️ 有效区间内的数据点少于2个，无法执行回归分析。请检查您的数据源或放宽左侧清洗边界。")
        st.stop()
        
    df_valid = df_valid.sort_values(by=col_vin).reset_index(drop=True)
    df_valid['Step_ID'] = df_valid[col_set]
    df_mean = df_valid.groupby('Step_ID', as_index=False).mean().sort_values(by=col_vin).reset_index(drop=True)
    
    df_max = df_valid.groupby('Step_ID', as_index=False).max().sort_values(by=col_vin).reset_index(drop=True)
    df_min = df_valid.groupby('Step_ID', as_index=False).min().sort_values(by=col_vin).reset_index(drop=True)

    if len(df_mean) < 2:
        st.error("🚨 **致命数据错误：** 分组降噪后，独立的有效电压台阶数少于 2 个！无法完成两点以上的直线拟合。")
        st.stop()

    N_avg = len(df_valid) / len(df_mean)
    is_staircase = N_avg >= 1.5  
    suffix_str = "(均值滤波去噪态)" if is_staircase else "(含噪单点态)"

    def calc_r2(y_true, y_pred):
        ss_res = np.sum((y_true - y_pred)**2)
        ss_tot = np.sum((y_true - np.mean(y_true))**2)
        return 1.0 if ss_tot == 0 else 1 - (ss_res / ss_tot)
    
    def calc_acc(x_meas, y_meas, k_ideal, fs_in_val, k_cov):
        k_ep = (np.max(y_meas) - np.min(y_meas)) / (np.max(x_meas) - np.min(x_meas))
        b_ep = np.min(y_meas) - k_ep * np.min(x_meas)
        rmse = np.sqrt(np.mean((y_meas - (k_ep * x_meas + b_ep))**2))
        pct_rdg = (abs(k_ep - k_ideal) / k_ideal) * 100
        pct_fs = ((abs(b_ep) + k_cov * rmse) / (fs_in_val * k_ideal)) * 100
        return pct_rdg, pct_fs

    k_afe, b_afe = np.polyfit(df_mean[col_vin], df_mean[col_vafe], 1)
    fit_afe = k_afe * df_mean[col_vin] + b_afe
    inl_afe = df_mean[col_vafe] - fit_afe
    r2_afe = calc_r2(df_mean[col_vafe], fit_afe)
    acc_afe_rdg, acc_afe_fs = calc_acc(df_mean[col_vin], df_mean[col_vafe], nom_gain_afe, fs_input, k_factor)
    
    k_adc_int, b_adc_int = np.polyfit(df_mean[col_vafe], df_mean[col_vadc0], 1)
    fit_adc_int = k_adc_int * df_mean[col_vafe] + b_adc_int
    r2_adc_int = calc_r2(df_mean[col_vadc0], fit_adc_int)
    acc_adc_int_rdg, acc_adc_int_fs = calc_acc(df_mean[col_vafe], df_mean[col_vadc0], nom_gain_adc, fs_input * nom_gain_afe, k_factor)

    k_adc_ext, b_adc_ext = np.polyfit(df_mean[col_vafe], df_mean[col_vadc1_adj], 1)
    fit_adc_ext = k_adc_ext * df_mean[col_vafe] + b_adc_ext
    r2_adc_ext = calc_r2(df_mean[col_vadc1_adj], fit_adc_ext)
    acc_adc_ext_rdg, acc_adc_ext_fs = calc_acc(df_mean[col_vafe], df_mean[col_vadc1_adj], nom_gain_adc, fs_input * nom_gain_afe, k_factor)

    k_adc_mcu0, b_adc_mcu0 = np.polyfit(df_mean[col_vafe], df_mean[col_mcu0], 1)
    fit_adc_mcu0 = k_adc_mcu0 * df_mean[col_vafe] + b_adc_mcu0
    r2_adc_mcu0 = calc_r2(df_mean[col_mcu0], fit_adc_mcu0)
    acc_adc_mcu0_rdg, acc_adc_mcu0_fs = calc_acc(df_mean[col_vafe], df_mean[col_mcu0], nom_gain_adc, fs_input * nom_gain_afe, k_factor)

    k_adc_mcu1, b_adc_mcu1 = np.polyfit(df_mean[col_vafe], df_mean[col_mcu1], 1)
    fit_adc_mcu1 = k_adc_mcu1 * df_mean[col_vafe] + b_adc_mcu1
    r2_adc_mcu1 = calc_r2(df_mean[col_mcu1], fit_adc_mcu1)
    acc_adc_mcu1_rdg, acc_adc_mcu1_fs = calc_acc(df_mean[col_vafe], df_mean[col_mcu1], nom_gain_adc, fs_input * nom_gain_afe, k_factor)

    k_sys_int, b_sys_int = np.polyfit(df_mean[col_vin], df_mean[col_vadc0], 1)
    fit_sys_int = k_sys_int * df_mean[col_vin] + b_sys_int
    inl_sys_int = df_mean[col_vadc0] - fit_sys_int
    r2_sys_int = calc_r2(df_mean[col_vadc0], fit_sys_int)
    acc_sys_int_rdg, acc_sys_int_fs = calc_acc(df_mean[col_vin], df_mean[col_vadc0], nom_gain_afe*nom_gain_adc, fs_input, k_factor)

    k_sys_ext, b_sys_ext = np.polyfit(df_mean[col_vin], df_mean[col_vadc1_adj], 1)
    fit_sys_ext = k_sys_ext * df_mean[col_vin] + b_sys_ext
    inl_sys_ext = df_mean[col_vadc1_adj] - fit_sys_ext
    r2_sys_ext = calc_r2(df_mean[col_vadc1_adj], fit_sys_ext)
    acc_sys_ext_rdg, acc_sys_ext_fs = calc_acc(df_mean[col_vin], df_mean[col_vadc1_adj], nom_gain_afe*nom_gain_adc, fs_input, k_factor)

    k_sys_mcu0, b_sys_mcu0 = np.polyfit(df_mean[col_vin], df_mean[col_mcu0], 1)
    fit_sys_mcu0 = k_sys_mcu0 * df_mean[col_vin] + b_sys_mcu0
    inl_sys_mcu0 = df_mean[col_mcu0] - fit_sys_mcu0
    r2_sys_mcu0 = calc_r2(df_mean[col_mcu0], fit_sys_mcu0)
    acc_sys_mcu0_rdg, acc_sys_mcu0_fs = calc_acc(df_mean[col_vin], df_mean[col_mcu0], nom_gain_afe*nom_gain_adc, fs_input, k_factor)

    k_sys_mcu1, b_sys_mcu1 = np.polyfit(df_mean[col_vin], df_mean[col_mcu1], 1)
    fit_sys_mcu1 = k_sys_mcu1 * df_mean[col_vin] + b_sys_mcu1
    inl_sys_mcu1 = df_mean[col_mcu1] - fit_sys_mcu1
    r2_sys_mcu1 = calc_r2(df_mean[col_mcu1], fit_sys_mcu1)
    acc_sys_mcu1_rdg, acc_sys_mcu1_fs = calc_acc(df_mean[col_vin], df_mean[col_mcu1], nom_gain_afe*nom_gain_adc, fs_input, k_factor)
    
    v_ideal_sys_out_mean = df_mean[col_vin] * (nom_gain_afe * nom_gain_adc)
    tue_limit = np.abs(v_ideal_sys_out_mean * (max_gain_err / 100)) + max_offset
    err_actual_sys_int_mean = df_mean[col_vadc0] - v_ideal_sys_out_mean
    err_actual_sys_ext_mean = df_mean[col_vadc1_adj] - v_ideal_sys_out_mean
    err_actual_sys_mcu0_mean = df_mean[col_mcu0] - v_ideal_sys_out_mean
    err_actual_sys_mcu1_mean = df_mean[col_mcu1] - v_ideal_sys_out_mean

    err_cal_sys_int_all = ((df_valid[col_vadc0] - b_sys_int) / k_sys_int) - df_valid[col_vin]
    err_cal_sys_ext_all = ((df_valid[col_vadc1_adj] - b_sys_ext) / k_sys_ext) - df_valid[col_vin]
    err_cal_sys_mcu0_all = ((df_valid[col_mcu0] - b_sys_mcu0) / k_sys_mcu0) - df_valid[col_vin]
    err_cal_sys_mcu1_all = ((df_valid[col_mcu1] - b_sys_mcu1) / k_sys_mcu1) - df_valid[col_vin]

    err_cal_sys_int_mean = ((df_mean[col_vadc0] - b_sys_int) / k_sys_int) - df_mean[col_vin]
    err_cal_sys_ext_mean = ((df_mean[col_vadc1_adj] - b_sys_ext) / k_sys_ext) - df_mean[col_vin]
    err_cal_sys_mcu0_mean = ((df_mean[col_mcu0] - b_sys_mcu0) / k_sys_mcu0) - df_mean[col_vin]
    err_cal_sys_mcu1_mean = ((df_mean[col_mcu1] - b_sys_mcu1) / k_sys_mcu1) - df_mean[col_vin]

    max_err_cal_int = np.max(np.abs(err_cal_sys_int_all)) if len(err_cal_sys_int_all) else 0.0
    max_err_cal_ext = np.max(np.abs(err_cal_sys_ext_all)) if len(err_cal_sys_ext_all) else 0.0
    max_err_cal_mcu0 = np.max(np.abs(err_cal_sys_mcu0_all)) if len(err_cal_sys_mcu0_all) else 0.0
    max_err_cal_mcu1 = np.max(np.abs(err_cal_sys_mcu1_all)) if len(err_cal_sys_mcu1_all) else 0.0

    def extract_noise_metrics(noise_array):
        if len(noise_array) < 2: return 0.0, 0.0, "N/A", "N/A"
        rms = np.std(noise_array, ddof=1)
        pp = np.max(noise_array) - np.min(noise_array)
        enob = f"{np.log2(fs_input / rms):.2f} Bits" if rms > 0 else "24.00 Bits"
        nfr = f"{np.log2(fs_input / pp):.2f} Bits" if pp > 0 else "24.00 Bits"
        return rms, pp, enob, nfr

    if is_staircase:
        noise_int_rti = (df_valid[col_vadc0] - df_valid.groupby('Step_ID')[col_vadc0].transform('mean')) / k_sys_int
        noise_ext_rti = (df_valid[col_vadc1_adj] - df_valid.groupby('Step_ID')[col_vadc1_adj].transform('mean')) / k_sys_ext
        noise_mcu0_rti = (df_valid[col_mcu0] - df_valid.groupby('Step_ID')[col_mcu0].transform('mean')) / k_sys_mcu0
        noise_mcu1_rti = (df_valid[col_mcu1] - df_valid.groupby('Step_ID')[col_mcu1].transform('mean')) / k_sys_mcu1
        
        rms_int, pp_int, enob_int_str, nfr_int_str = extract_noise_metrics(noise_int_rti)
        rms_ext, pp_ext, enob_ext_str, nfr_ext_str = extract_noise_metrics(noise_ext_rti)
        rms_mcu0, pp_mcu0, enob_mcu0_str, nfr_mcu0_str = extract_noise_metrics(noise_mcu0_rti)
        rms_mcu1, pp_mcu1, enob_mcu1_str, nfr_mcu1_str = extract_noise_metrics(noise_mcu1_rti)
        
        hist_data = [noise_int_rti, noise_ext_rti, noise_mcu0_rti, noise_mcu1_rti]
    else:
        rms_int, pp_int, _, _ = extract_noise_metrics(err_cal_sys_int_all)
        rms_ext, pp_ext, _, _ = extract_noise_metrics(err_cal_sys_ext_all)
        rms_mcu0, pp_mcu0, _, _ = extract_noise_metrics(err_cal_sys_mcu0_all)
        rms_mcu1, pp_mcu1, _, _ = extract_noise_metrics(err_cal_sys_mcu1_all)
        
        na_str = "<span style='color: #aaa;'>N/A (需阶梯数据)</span>"
        enob_int_str = nfr_int_str = enob_ext_str = nfr_ext_str = na_str
        enob_mcu0_str = nfr_mcu0_str = enob_mcu1_str = nfr_mcu1_str = na_str
        hist_data = [err_cal_sys_int_all, err_cal_sys_ext_all, err_cal_sys_mcu0_all, err_cal_sys_mcu1_all]

    # --- 包络带计算 ---
    if is_staircase:
        err_act_sys_int_max = df_max[col_vadc0] - v_ideal_sys_out_mean
        err_act_sys_int_min = df_min[col_vadc0] - v_ideal_sys_out_mean
        err_act_sys_ext_max = df_max[col_vadc1_adj] - v_ideal_sys_out_mean
        err_act_sys_ext_min = df_min[col_vadc1_adj] - v_ideal_sys_out_mean
        err_act_sys_mcu0_max = df_max[col_mcu0] - v_ideal_sys_out_mean
        err_act_sys_mcu0_min = df_min[col_mcu0] - v_ideal_sys_out_mean
        err_act_sys_mcu1_max = df_max[col_mcu1] - v_ideal_sys_out_mean
        err_act_sys_mcu1_min = df_min[col_mcu1] - v_ideal_sys_out_mean

        inl_sys_int_max = df_max[col_vadc0] - fit_sys_int
        inl_sys_int_min = df_min[col_vadc0] - fit_sys_int
        inl_sys_ext_max = df_max[col_vadc1_adj] - fit_sys_ext
        inl_sys_ext_min = df_min[col_vadc1_adj] - fit_sys_ext
        inl_sys_mcu0_max = df_max[col_mcu0] - fit_sys_mcu0
        inl_sys_mcu0_min = df_min[col_mcu0] - fit_sys_mcu0
        inl_sys_mcu1_max = df_max[col_mcu1] - fit_sys_mcu1
        inl_sys_mcu1_min = df_min[col_mcu1] - fit_sys_mcu1

    err_rti_afe = (df_mean[col_vafe] / nom_gain_afe) - df_mean[col_vin]
    err_rti_adc_int = (df_mean[col_vadc0] / (nom_gain_afe * nom_gain_adc)) - (df_mean[col_vafe] / nom_gain_afe)
    err_rti_adc_ext = (df_mean[col_vadc1_adj] / (nom_gain_afe * nom_gain_adc)) - (df_mean[col_vafe] / nom_gain_afe)
    err_rti_adc_mcu0 = (df_mean[col_mcu0] / (nom_gain_afe * nom_gain_adc)) - (df_mean[col_vafe] / nom_gain_afe)
    err_rti_adc_mcu1 = (df_mean[col_mcu1] / (nom_gain_afe * nom_gain_adc)) - (df_mean[col_vafe] / nom_gain_afe)

    if is_staircase:
        err_rti_afe_max = (df_max[col_vafe] / nom_gain_afe) - df_mean[col_vin]
        err_rti_afe_min = (df_min[col_vafe] / nom_gain_afe) - df_mean[col_vin]
        err_rti_adc_int_max = (df_max[col_vadc0] / (nom_gain_afe * nom_gain_adc)) - (df_mean[col_vafe] / nom_gain_afe)
        err_rti_adc_int_min = (df_min[col_vadc0] / (nom_gain_afe * nom_gain_adc)) - (df_mean[col_vafe] / nom_gain_afe)
        err_rti_adc_ext_max = (df_max[col_vadc1_adj] / (nom_gain_afe * nom_gain_adc)) - (df_mean[col_vafe] / nom_gain_afe)
        err_rti_adc_ext_min = (df_min[col_vadc1_adj] / (nom_gain_afe * nom_gain_adc)) - (df_mean[col_vafe] / nom_gain_afe)
        err_rti_adc_mcu0_max = (df_max[col_mcu0] / (nom_gain_afe * nom_gain_adc)) - (df_mean[col_vafe] / nom_gain_afe)
        err_rti_adc_mcu0_min = (df_min[col_mcu0] / (nom_gain_afe * nom_gain_adc)) - (df_mean[col_vafe] / nom_gain_afe)
        err_rti_adc_mcu1_max = (df_max[col_mcu1] / (nom_gain_afe * nom_gain_adc)) - (df_mean[col_vafe] / nom_gain_afe)
        err_rti_adc_mcu1_min = (df_min[col_mcu1] / (nom_gain_afe * nom_gain_adc)) - (df_mean[col_vafe] / nom_gain_afe)

    # ==========================================
    # 3. 矩阵式诊断 Dashboard
    # ==========================================
    st.title("🔬 直流信号分析报告")
    
    if is_staircase:
        st.success(f"✅ **阶梯降维引擎激活：** 侦测到平均每个电压阶梯 **{N_avg:.1f}** 个采样点，已自动隔离静态弯曲与动态热噪声。")
    else:
        st.info("💡 **当前状态：** 检测为单次扫频。仅展示静态线性误差，真实动态噪声及 ENOB 已被折叠。")

    st.markdown(f"### 🎯 信号链综合测量精度解构 (满量程 FS = {fs_input} mV, K = {k_factor})")
    col_1, col_2, col_3 = st.columns(3)
    with col_1:
        st.info("🛠️ **模块 1: AFE 级性能**")
        st.metric("AFE 实际增益 (k)", f"{k_afe:.6f} V/V")
        st.metric("AFE 最佳拟合失调 (b)", f"{b_afe:.4f} mV")
        st.markdown(f"<div class='metric-sub'><b>R²:</b> {r2_afe:.6f}<br><b>精度:</b> <span class='acc-text'>±({acc_afe_rdg:.4f}% R + {acc_afe_fs:.4f}% FS)</span></div>", unsafe_allow_html=True)
        
    with col_2:
        st.warning("🔌 **模块 2: 各 ADC 本体独立性能**")
        st.markdown(f"""
        <div class='metric-sub metric-sub-int'><b>ADS0 (内基准)</b><br>R²: {r2_adc_int:.6f} | 精度: <span class='acc-text'>±({acc_adc_int_rdg:.4f}% R + {acc_adc_int_fs:.4f}% FS)</span></div>
        <div class='metric-sub metric-sub-ext'><b>ADS1 (外基准)</b><br>R²: {r2_adc_ext:.6f} | 精度: <span class='acc-text'>±({acc_adc_ext_rdg:.4f}% R + {acc_adc_ext_fs:.4f}% FS)</span></div>
        <div style='border-top:1px dashed #ccc; margin:8px 0;'></div>
        <div class='metric-sub metric-sub-mcu0'><b>MCU0 (单端)</b><br>R²: {r2_adc_mcu0:.6f} | 精度: <span class='acc-text'>±({acc_adc_mcu0_rdg:.4f}% R + {acc_adc_mcu0_fs:.4f}% FS)</span></div>
        <div class='metric-sub metric-sub-mcu1'><b>MCU1 (差分)</b><br>R²: {r2_adc_mcu1:.6f} | 精度: <span class='acc-text'>±({acc_adc_mcu1_rdg:.4f}% R + {acc_adc_mcu1_fs:.4f}% FS)</span></div>
        """, unsafe_allow_html=True)
        
    with col_3:
        st.success("🔗 **模块 3: 端到端全链路系统性能**")
        st.markdown(f"""
        <div class='metric-sub metric-sub-int'><b>全链路 ADS0</b><br>R²: {r2_sys_int:.6f} | 精度: <span class='acc-text'>±({acc_sys_int_rdg:.4f}% R + {acc_sys_int_fs:.4f}% FS)</span></div>
        <div class='metric-sub metric-sub-ext'><b>全链路 ADS1</b><br>R²: {r2_sys_ext:.6f} | 精度: <span class='acc-text'>±({acc_sys_ext_rdg:.4f}% R + {acc_sys_ext_fs:.4f}% FS)</span></div>
        <div style='border-top:1px dashed #ccc; margin:8px 0;'></div>
        <div class='metric-sub metric-sub-mcu0'><b>全链路 MCU0</b><br>R²: {r2_sys_mcu0:.6f} | 精度: <span class='acc-text'>±({acc_sys_mcu0_rdg:.4f}% R + {acc_sys_mcu0_fs:.4f}% FS)</span></div>
        <div class='metric-sub metric-sub-mcu1'><b>全链路 MCU1</b><br>R²: {r2_sys_mcu1:.6f} | 精度: <span class='acc-text'>±({acc_sys_mcu1_rdg:.4f}% R + {acc_sys_mcu1_fs:.4f}% FS)</span></div>
        """, unsafe_allow_html=True)

    st.markdown("### ✨ 全链路线性校准后评估 (折算至输入端)")
    lbl_rms = "全局纯底噪 RMS (1σ)" if is_staircase else "综合均方根残差 (RMSE)"
    lbl_pp = "全局 RTI 纯底噪 (Vp-p)" if is_staircase else "综合残差峰峰值 (P-P)"
    def render_residual_card(title, color, max_err, rms, pp, nfr, enob):
        return f"""
        <div style='background: #eef2f5; padding: 15px; border-radius: 5px; border-left: 5px solid {color}; margin-bottom: 15px;'>
            <b>{title}：</b><br>最大绝对极限：<span style='color: #d9534f; font-weight: bold;'>{max_err:.4f} mV</span><br>
            {lbl_rms}：<span style='color: {color}; font-weight: bold;'>{rms:.4f} mV</span><br>
            {lbl_pp}：<span style='color: #d9534f; font-weight: bold;'>{pp:.4f} mV</span><br>
            全局 NFR：<span style='color: {color}; font-weight: bold;'>{nfr}</span><br>全局 ENOB：<span style='color: {color}; font-weight: bold;'>{enob}</span>
        </div>
        """
    col_cal1, col_cal2 = st.columns(2)
    with col_cal1: st.markdown(render_residual_card("全链路 ADS0 (内基准)", "#ffc107", max_err_cal_int, rms_int, pp_int, nfr_int_str, enob_int_str), unsafe_allow_html=True)
    with col_cal2: st.markdown(render_residual_card("全链路 ADS1 (外基准)", "#28a745", max_err_cal_ext, rms_ext, pp_ext, nfr_ext_str, enob_ext_str), unsafe_allow_html=True)
    col_cal3, col_cal4 = st.columns(2)
    with col_cal3: st.markdown(render_residual_card("全链路 MCU0 (单端)", "#6f42c1", max_err_cal_mcu0, rms_mcu0, pp_mcu0, nfr_mcu0_str, enob_mcu0_str), unsafe_allow_html=True)
    with col_cal4: st.markdown(render_residual_card("全链路 MCU1 (差分)", "#17a2b8", max_err_cal_mcu1, rms_mcu1, pp_mcu1, nfr_mcu1_str, enob_mcu1_str), unsafe_allow_html=True)

    st.divider()

    # ==========================================
    # 4. 可视化图表 (Tabs)
    # ==========================================
    tab_tue, tab_inl, tab_cal, tab_hist, tab_trace, tab_fit, tab_export = st.tabs([
        "🔮 绝对误差", "🏹 INL误差", "✨ 校准残差图", "📊 定点微观统计", "🔪 误差溯源拆解", "📉 拟合全景图", "💾 看板导出"
    ])
    
    with tab_tue:
        st.markdown(f"### 全链路绝对误差 vs 输入图 {suffix_str}")
        st.markdown("<div class='formula-ui'><b>📐 公式：</b> 绝对误差 = 实际测量读数 - 理论理想读数<br><b>💡 意义：</b> 暴露未经任何校准时，各链路最原始的宏观偏差偏离度。包含半透明的热噪声 P-P 包络带。</div>", unsafe_allow_html=True)
        fig_tue = go.Figure()
        fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=tue_limit, mode='lines', name='±TUE 理论包络', line=dict(color='red', dash='dash'), legendgroup='TUE'))
        fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=-tue_limit, mode='lines', fill='tonexty', fillcolor='rgba(255,0,0,0.1)', line=dict(color='red', dash='dash'), showlegend=False, legendgroup='TUE'))
        
        if is_staircase:
            fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=err_act_sys_int_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='ADS0'))
            fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=err_act_sys_int_min, mode='lines', fill='tonexty', fillcolor='rgba(255,193,7,0.2)', line=dict(width=0), showlegend=False, legendgroup='ADS0'))
            fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=err_act_sys_ext_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='ADS1'))
            fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=err_act_sys_ext_min, mode='lines', fill='tonexty', fillcolor='rgba(40,167,69,0.2)', line=dict(width=0), showlegend=False, legendgroup='ADS1'))
            fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=err_act_sys_mcu0_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='MCU0'))
            fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=err_act_sys_mcu0_min, mode='lines', fill='tonexty', fillcolor='rgba(111,66,193,0.2)', line=dict(width=0), showlegend=False, legendgroup='MCU0'))
            fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=err_act_sys_mcu1_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='MCU1'))
            fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=err_act_sys_mcu1_min, mode='lines', fill='tonexty', fillcolor='rgba(23,162,184,0.2)', line=dict(width=0), showlegend=False, legendgroup='MCU1'))

        fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=err_actual_sys_int_mean, mode='lines', name='ADS0 (内基准)', line=dict(color='#ffc107', width=2), legendgroup='ADS0'))
        fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=err_actual_sys_ext_mean, mode='lines', name='ADS1 (外基准)', line=dict(color='#28a745', width=2), legendgroup='ADS1'))
        fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=err_actual_sys_mcu0_mean, mode='lines', name='MCU0 (单端)', line=dict(color='#6f42c1', width=2), legendgroup='MCU0'))
        fig_tue.add_trace(go.Scatter(x=df_mean[col_vin], y=err_actual_sys_mcu1_mean, mode='lines', name='MCU1 (差分)', line=dict(color='#17a2b8', width=2), legendgroup='MCU1'))
        st.plotly_chart(apply_chart_style(fig_tue, "", "绝对物理输入 DMM_1_VOLT (mV)", "相对标称输出绝对误差 (mV)"), use_container_width=True)

    with tab_inl:
        st.markdown(f"### 全链路 INL 误差 vs 输入图 {suffix_str}")
        st.markdown("<div class='formula-ui'><b>📐 公式：</b> INL = 实际测量读数 - (拟合斜率k × 物理输入 + 拟合失调b)<br><b>💡 意义：</b> 剥离常规的线性漂移，直接对决外挂 ADC 和内部 MCU ADC 的物理非线性弯曲缺陷。</div>", unsafe_allow_html=True)
        fig_inl = go.Figure()
        
        if is_staircase:
            fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_sys_int_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='ADS0'))
            fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_sys_int_min, mode='lines', fill='tonexty', fillcolor='rgba(255,193,7,0.2)', line=dict(width=0), showlegend=False, legendgroup='ADS0'))
            fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_sys_ext_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='ADS1'))
            fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_sys_ext_min, mode='lines', fill='tonexty', fillcolor='rgba(40,167,69,0.2)', line=dict(width=0), showlegend=False, legendgroup='ADS1'))
            fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_sys_mcu0_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='MCU0'))
            fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_sys_mcu0_min, mode='lines', fill='tonexty', fillcolor='rgba(111,66,193,0.2)', line=dict(width=0), showlegend=False, legendgroup='MCU0'))
            fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_sys_mcu1_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='MCU1'))
            fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_sys_mcu1_min, mode='lines', fill='tonexty', fillcolor='rgba(23,162,184,0.2)', line=dict(width=0), showlegend=False, legendgroup='MCU1'))

        fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_afe, mode='lines', name="AFE 级基底 INL", line=dict(color='gray', width=3)))
        fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_sys_int, mode='lines', name="全链路 ADS0", line=dict(color='#ffc107', width=2), legendgroup='ADS0'))
        fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_sys_ext, mode='lines', name="全链路 ADS1", line=dict(color='#28a745', width=2), legendgroup='ADS1'))
        fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_sys_mcu0, mode='lines', name="全链路 MCU0", line=dict(color='#6f42c1', width=2, dash='dot'), legendgroup='MCU0'))
        fig_inl.add_trace(go.Scatter(x=df_mean[col_vin], y=inl_sys_mcu1, mode='lines', name="全链路 MCU1", line=dict(color='#17a2b8', width=2, dash='dot'), legendgroup='MCU1'))
        st.plotly_chart(apply_chart_style(fig_inl, "", "绝对物理输入 DMM_1_VOLT (mV)", "积分非线性绝对残差 INL (mV)"), use_container_width=True)

    with tab_cal:
        st.markdown("### 系统级线性校准后残差 (评估四路系统的动态底噪包络)")
        fig_cal = go.Figure()
        if is_staircase:
            fig_cal.add_trace(go.Scatter(x=df_valid[col_vin], y=err_cal_sys_int_all, mode='markers', marker=dict(size=3, opacity=0.15, color='#ffc107'), name="ADS0", legendgroup='ADS0'))
            fig_cal.add_trace(go.Scatter(x=df_valid[col_vin], y=err_cal_sys_ext_all, mode='markers', marker=dict(size=3, opacity=0.15, color='#28a745'), name="ADS1", legendgroup='ADS1'))
            fig_cal.add_trace(go.Scatter(x=df_valid[col_vin], y=err_cal_sys_mcu0_all, mode='markers', marker=dict(size=3, opacity=0.15, color='#6f42c1'), name="MCU0", legendgroup='MCU0'))
            fig_cal.add_trace(go.Scatter(x=df_valid[col_vin], y=err_cal_sys_mcu1_all, mode='markers', marker=dict(size=3, opacity=0.15, color='#17a2b8'), name="MCU1", legendgroup='MCU1'))
            
            fig_cal.add_trace(go.Scatter(x=df_mean[col_vin], y=err_cal_sys_int_mean, mode='lines', line=dict(color='#ffc107', width=2), showlegend=False, legendgroup='ADS0'))
            fig_cal.add_trace(go.Scatter(x=df_mean[col_vin], y=err_cal_sys_ext_mean, mode='lines', line=dict(color='#28a745', width=2), showlegend=False, legendgroup='ADS1'))
            fig_cal.add_trace(go.Scatter(x=df_mean[col_vin], y=err_cal_sys_mcu0_mean, mode='lines', line=dict(color='#6f42c1', width=2), showlegend=False, legendgroup='MCU0'))
            fig_cal.add_trace(go.Scatter(x=df_mean[col_vin], y=err_cal_sys_mcu1_mean, mode='lines', line=dict(color='#17a2b8', width=2), showlegend=False, legendgroup='MCU1'))
        else:
            fig_cal.add_trace(go.Scatter(x=df_valid[col_vin], y=err_cal_sys_int_all, mode='lines', line=dict(color='#ffc107', width=1.5), name="ADS0"))
            fig_cal.add_trace(go.Scatter(x=df_valid[col_vin], y=err_cal_sys_ext_all, mode='lines', line=dict(color='#28a745', width=1.5), name="ADS1"))
            fig_cal.add_trace(go.Scatter(x=df_valid[col_vin], y=err_cal_sys_mcu0_all, mode='lines', line=dict(color='#6f42c1', width=1.5), name="MCU0"))
            fig_cal.add_trace(go.Scatter(x=df_valid[col_vin], y=err_cal_sys_mcu1_all, mode='lines', line=dict(color='#17a2b8', width=1.5), name="MCU1"))
        fig_cal.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(apply_chart_style(fig_cal, "", "真实物理输入 DMM_1_VOLT (mV)", "RTI 折算至输入端残差 (mV)"), use_container_width=True)

    hist_htmls_export = ""  
    with tab_hist:
        def get_dmm_stats_html(rti_series, color):
            N = len(rti_series)
            if N < 2: return ""
            mean_val = rti_series.mean()
            std_val = rti_series.std(ddof=1)
            max_val = rti_series.max()
            min_val = rti_series.min()
            pp_val = max_val - min_val
            return f"""
            <div style='background: #f8f9fa; border-left: 4px solid {color}; padding: 12px 15px; margin-top: -20px; margin-bottom: 15px; border-radius: 4px; font-size: 0.88em; color: #333; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
                <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; line-height: 1.5;'>
                    <div><b>N (样本数):</b> {N}</div>
                    <div><b>Mean (均值):</b> {mean_val:.4f} mV</div>
                    <div><b>Std (标准差):</b> {std_val:.4f} mV</div>
                    <div><b>P-P (峰峰值):</b> {pp_val:.4f} mV</div>
                    <div><b>Max (极大值):</b> {max_val:.4f} mV</div>
                    <div><b>Min (极小值):</b> {min_val:.4f} mV</div>
                </div>
            </div>
            """

        def plot_histogram_with_fit(data, title, color, x_label="组内测量电压 (mV)"):
            data_clean = pd.to_numeric(pd.Series(data), errors='coerce').replace([np.inf, -np.inf], np.nan).dropna().values
            fig = go.Figure()
            if len(data_clean) < 2:
                fig.update_layout(title=title + " (无有效数据)")
                return fig
                
            mean_val = np.mean(data_clean)
            std_val = np.std(data_clean, ddof=1)
            
            fig.add_trace(go.Histogram(x=data_clean, name='实测数量', marker_color=color, opacity=0.6, nbinsx=30))
            
            if std_val > 0:
                x_range = np.linspace(np.min(data_clean), np.max(data_clean), 200)
                counts, bins = np.histogram(data_clean, bins=30)
                bin_width = bins[1] - bins[0] if len(bins) > 1 else 1
                pdf_scaled = stats.norm.pdf(x_range, mean_val, std_val) * len(data_clean) * bin_width
                fig.add_trace(go.Scatter(x=x_range, y=pdf_scaled, mode='lines', name='理论高斯包络', line=dict(color='black', dash='dash', width=2)))
                
            fig.update_layout(title=title, barmode='overlay', plot_bgcolor='white', hovermode="x", legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5), margin=dict(t=60, b=60))
            fig.update_xaxes(title_text=x_label, showgrid=True, gridcolor='LightGray')
            fig.update_yaxes(title_text="数量 (Count)", showgrid=True, gridcolor='LightGray')
            return fig

        if is_staircase:
            st.markdown(f"### 🎯 指定设定电压点 ({col_set}) - 局部微观抗干扰诊断")
            st.info("💡 直方图横坐标为您请求的 **绝对测量电压分布 (RTI)**，纵坐标为 **数量 (Count)**；下方 DMM 仪表盘为您提取了本组数据的绝对统计极值。")
            unique_steps_val = df_mean['Step_ID'].tolist()
            default_sel = []
            if len(unique_steps_val) > 0: default_sel.append(unique_steps_val[0])
            if len(unique_steps_val) > 2: default_sel.append(unique_steps_val[len(unique_steps_val)//2])
            
            selected_steps = st.multiselect("请点选需要提取高斯底噪的设定电压点：", options=unique_steps_val, default=default_sel)
            
            if selected_steps:
                for step_target in selected_steps:
                    step_data = df_valid[df_valid['Step_ID'] == step_target]
                    if len(step_data) == 0: continue
                    
                    step_rti_int = (step_data[col_vadc0] - b_sys_int) / k_sys_int
                    step_rti_ext = (step_data[col_vadc1_adj] - b_sys_ext) / k_sys_ext
                    step_rti_mcu0 = (step_data[col_mcu0] - b_sys_mcu0) / k_sys_mcu0
                    step_rti_mcu1 = (step_data[col_mcu1] - b_sys_mcu1) / k_sys_mcu1
                    
                    stats_int = get_dmm_stats_html(step_rti_int, '#ffc107')
                    stats_ext = get_dmm_stats_html(step_rti_ext, '#28a745')
                    stats_mcu0 = get_dmm_stats_html(step_rti_mcu0, '#6f42c1')
                    stats_mcu1 = get_dmm_stats_html(step_rti_mcu1, '#17a2b8')
                    
                    st.markdown(f"#### ⚡ 设定阶梯定点诊断: {step_target}")
                    col_h1, col_h2 = st.columns(2)
                    with col_h1: 
                        fig_int = plot_histogram_with_fit(step_rti_int, f"ADS0 组内测量分布 (设定={step_target})", '#ffc107', "测量电压 (mV)")
                        st.plotly_chart(fig_int, use_container_width=True)
                        st.markdown(stats_int, unsafe_allow_html=True)
                    with col_h2: 
                        fig_ext = plot_histogram_with_fit(step_rti_ext, f"ADS1 组内测量分布 (设定={step_target})", '#28a745', "测量电压 (mV)")
                        st.plotly_chart(fig_ext, use_container_width=True)
                        st.markdown(stats_ext, unsafe_allow_html=True)
                    
                    col_h3, col_h4 = st.columns(2)
                    with col_h3: 
                        fig_mcu0 = plot_histogram_with_fit(step_rti_mcu0, f"MCU0 单端测量分布 (设定={step_target})", '#6f42c1', "测量电压 (mV)")
                        st.plotly_chart(fig_mcu0, use_container_width=True)
                        st.markdown(stats_mcu0, unsafe_allow_html=True)
                    with col_h4: 
                        fig_mcu1 = plot_histogram_with_fit(step_rti_mcu1, f"MCU1 差分测量分布 (设定={step_target})", '#17a2b8', "测量电压 (mV)")
                        st.plotly_chart(fig_mcu1, use_container_width=True)
                        st.markdown(stats_mcu1, unsafe_allow_html=True)
                    
                    hist_htmls_export += f"<h3 style='color:#444; border-bottom: 1px solid #eee; padding-bottom:5px; margin-top:30px;'>⚡ 阶梯驻留抽样：设定点 {step_target}</h3><div class='grid-2col'>"
                    hist_htmls_export += f"<div class='chart-container' style='padding-bottom:5px;'>{fig_int.to_html(full_html=False, include_plotlyjs=False)}{stats_int}</div>"
                    hist_htmls_export += f"<div class='chart-container' style='padding-bottom:5px;'>{fig_ext.to_html(full_html=False, include_plotlyjs=False)}{stats_ext}</div>"
                    hist_htmls_export += f"<div class='chart-container' style='padding-bottom:5px;'>{fig_mcu0.to_html(full_html=False, include_plotlyjs=False)}{stats_mcu0}</div>"
                    hist_htmls_export += f"<div class='chart-container' style='padding-bottom:5px;'>{fig_mcu1.to_html(full_html=False, include_plotlyjs=False)}{stats_mcu1}</div></div>"
        else:
            st.warning("⚠️ 侦测到单次连续扫频或样本量不足。强行绘制高斯直方图不具统计参考价值。")
            col_h1, col_h2 = st.columns(2)
            with col_h1: fig_int = plot_histogram_with_fit(hist_data[0], "ADS0 全量程含噪残差", '#ffc107', "RTI 误差幅度 (mV)"); st.plotly_chart(fig_int, use_container_width=True)
            with col_h2: fig_ext = plot_histogram_with_fit(hist_data[1], "ADS1 全量程含噪残差", '#28a745', "RTI 误差幅度 (mV)"); st.plotly_chart(fig_ext, use_container_width=True)
            col_h3, col_h4 = st.columns(2)
            with col_h3: fig_mcu0 = plot_histogram_with_fit(hist_data[2], "MCU0 全量程含噪残差", '#6f42c1', "RTI 误差幅度 (mV)"); st.plotly_chart(fig_mcu0, use_container_width=True)
            with col_h4: fig_mcu1 = plot_histogram_with_fit(hist_data[3], "MCU1 全量程含噪残差", '#17a2b8', "RTI 误差幅度 (mV)"); st.plotly_chart(fig_mcu1, use_container_width=True)
            
            hist_htmls_export += "<h3 style='color:#444; border-bottom: 1px solid #eee; padding-bottom:5px; margin-top:30px;'>⚠️ 单点全量程混合误差直方图 (参考价值低)</h3><div class='grid-2col'>"
            hist_htmls_export += f"<div class='chart-container'>{fig_int.to_html(full_html=False, include_plotlyjs=False)}</div><div class='chart-container'>{fig_ext.to_html(full_html=False, include_plotlyjs=False)}</div>"
            hist_htmls_export += f"<div class='chart-container'>{fig_mcu0.to_html(full_html=False, include_plotlyjs=False)}</div><div class='chart-container'>{fig_mcu1.to_html(full_html=False, include_plotlyjs=False)}</div></div>"

    with tab_trace:
        st.markdown(f"### 🔪 绝对误差溯源拆解图 {suffix_str}")
        fig_trace = go.Figure()
        
        if is_staircase:
            fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_afe_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='AFE'))
            fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_afe_min, mode='lines', fill='tonexty', fillcolor='rgba(0,0,255,0.15)', line=dict(width=0), showlegend=False, legendgroup='AFE'))
            fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_adc_int_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='ADS0'))
            fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_adc_int_min, mode='lines', fill='tonexty', fillcolor='rgba(255,193,7,0.15)', line=dict(width=0), showlegend=False, legendgroup='ADS0'))
            fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_adc_ext_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='ADS1'))
            fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_adc_ext_min, mode='lines', fill='tonexty', fillcolor='rgba(40,167,69,0.15)', line=dict(width=0), showlegend=False, legendgroup='ADS1'))
            fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_adc_mcu0_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='MCU0'))
            fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_adc_mcu0_min, mode='lines', fill='tonexty', fillcolor='rgba(111,66,193,0.15)', line=dict(width=0), showlegend=False, legendgroup='MCU0'))
            fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_adc_mcu1_max, mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip', legendgroup='MCU1'))
            fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_adc_mcu1_min, mode='lines', fill='tonexty', fillcolor='rgba(23,162,184,0.15)', line=dict(width=0), showlegend=False, legendgroup='MCU1'))

        fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_afe, mode='lines', name='[0] 前端 AFE 本底误差 (RTI)', line=dict(color='blue', width=3), legendgroup='AFE'))
        fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_adc_int, mode='lines', name='[1] ADS0 引入误差 (RTI)', line=dict(color='#ffc107', width=1.5), legendgroup='ADS0'))
        fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_adc_ext, mode='lines', name='[2] ADS1 引入误差 (RTI)', line=dict(color='#28a745', width=1.5), legendgroup='ADS1'))
        fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_adc_mcu0, mode='lines', name='[3] MCU0 引入误差 (RTI)', line=dict(color='#6f42c1', width=1.5, dash='dot'), legendgroup='MCU0'))
        fig_trace.add_trace(go.Scatter(x=df_mean[col_vin], y=err_rti_adc_mcu1, mode='lines', name='[4] MCU1 引入误差 (RTI)', line=dict(color='#17a2b8', width=1.5, dash='dot'), legendgroup='MCU1'))
        fig_trace.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)
        st.plotly_chart(apply_chart_style(fig_trace, "", "真实物理输入 DMM_1_VOLT (mV)", "各级独立 RTI 绝对误差量 (mV)"), use_container_width=True)

    with tab_fit:
        st.markdown("### 硬件传递函数拟合全景图")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fig_sys_ext = go.Figure()
            fig_sys_ext.add_trace(go.Scatter(x=df_valid[col_vin], y=df_valid[col_vadc1_adj], mode='markers', name="ADS1散点", marker=dict(color='#28a745', size=3, opacity=0.7)))
            fig_sys_ext.add_trace(go.Scatter(x=df_mean[col_vin], y=fit_sys_ext, mode='lines', name="ADS1拟合", line=dict(dash='dash', color='black')))
            st.plotly_chart(apply_chart_style(fig_sys_ext, f"ADS1 全链路 | R²={r2_sys_ext:.6f}", "DMM_1_VOLT", "ADS1 Read"), use_container_width=True)
            sys_ext_fit_html = fig_sys_ext.to_html(full_html=False, include_plotlyjs=False)
        with col_f2:
            fig_sys_mcu1 = go.Figure()
            fig_sys_mcu1.add_trace(go.Scatter(x=df_valid[col_vin], y=df_valid[col_mcu1], mode='markers', name="MCU1散点", marker=dict(color='#17a2b8', size=3, opacity=0.7)))
            fig_sys_mcu1.add_trace(go.Scatter(x=df_mean[col_vin], y=fit_sys_mcu1, mode='lines', name="MCU1拟合", line=dict(dash='dash', color='black')))
            st.plotly_chart(apply_chart_style(fig_sys_mcu1, f"MCU1 差分全链路 | R²={r2_sys_mcu1:.6f}", "DMM_1_VOLT", "MCU1 Read"), use_container_width=True)
            sys_mcu1_fit_html = fig_sys_mcu1.to_html(full_html=False, include_plotlyjs=False)

    # ==========================================
    # 5. Tab_export: 增强版交互式离线报告导出
    # ==========================================
    with tab_export:
        st.info("💡 下载的 HTML 档案将包含所有四路 ADC 的全维对比数据。")
        df_export = df_valid.copy()
        df_export['Calibrated_Residual_ADS0_All(mV)'] = err_cal_sys_int_all
        df_export['Calibrated_Residual_ADS1_All(mV)'] = err_cal_sys_ext_all
        df_export['Calibrated_Residual_MCU0_All(mV)'] = err_cal_sys_mcu0_all
        df_export['Calibrated_Residual_MCU1_All(mV)'] = err_cal_sys_mcu1_all
        if is_staircase:
            df_export['Pure_AC_Noise_ADS0(mV)'] = hist_data[0]
            df_export['Pure_AC_Noise_ADS1(mV)'] = hist_data[1]
            df_export['Pure_AC_Noise_MCU0(mV)'] = hist_data[2]
            df_export['Pure_AC_Noise_MCU1(mV)'] = hist_data[3]
        
        tue_html = fig_tue.to_html(full_html=False, include_plotlyjs=True)
        inl_html = fig_inl.to_html(full_html=False, include_plotlyjs=False)
        cal_html = fig_cal.to_html(full_html=False, include_plotlyjs=False)
        trace_html = fig_trace.to_html(full_html=False, include_plotlyjs=False)
        
        html_report = f"""
        <!DOCTYPE html><html><head><meta charset="utf-8"><title>直流信号分析报告</title>
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
                <h1>🔬 直流信号分析报告 (多ADC并联验证)</h1>
                <h2>1. 四路并行测量精度解构 (K={k_factor})</h2>
                <div class="grid-container">
                    <div class="metric-card"><h3 style="margin-top:0;">模块 1: AFE 级性能</h3><p>实际增益 (k): <b>{k_afe:.6f}</b></p><p>最佳失调 (b): <b>{b_afe:.4f} mV</b></p><p>R²: <b>{r2_afe:.6f}</b></p><p class="acc-txt">精度: ±({acc_afe_rdg:.4f}% R + {acc_afe_fs:.4f}% FS)</p></div>
                    <div class="metric-card"><h3 style="margin-top:0; color:#856404;">模块 2: ADC 本体独立对比</h3><p><b>ADS0:</b> R²={r2_adc_int:.6f}</p><p class="acc-txt">精度: ±({acc_adc_int_rdg:.4f}% R + {acc_adc_int_fs:.4f}% FS)</p><p><b>ADS1:</b> R²={r2_adc_ext:.6f}</p><p class="acc-txt">精度: ±({acc_adc_ext_rdg:.4f}% R + {acc_adc_ext_fs:.4f}% FS)</p><hr style="border:0; border-top:1px dashed #ccc;"><p><b>MCU0:</b> R²={r2_adc_mcu0:.6f}</p><p class="acc-txt">精度: ±({acc_adc_mcu0_rdg:.4f}% R + {acc_adc_mcu0_fs:.4f}% FS)</p><p><b>MCU1:</b> R²={r2_adc_mcu1:.6f}</p><p class="acc-txt">精度: ±({acc_adc_mcu1_rdg:.4f}% R + {acc_adc_mcu1_fs:.4f}% FS)</p></div>
                    <div class="metric-card"><h3 style="margin-top:0; color:#155724;">模块 3: 全链路端到端对比</h3><p><b>ADS0:</b> R²={r2_sys_int:.6f}</p><p class="acc-txt">精度: ±({acc_sys_int_rdg:.4f}% R + {acc_sys_int_fs:.4f}% FS)</p><p><b>ADS1:</b> R²={r2_sys_ext:.6f}</p><p class="acc-txt">精度: ±({acc_sys_ext_rdg:.4f}% R + {acc_sys_ext_fs:.4f}% FS)</p><hr style="border:0; border-top:1px dashed #ccc;"><p><b>MCU0:</b> R²={r2_sys_mcu0:.6f}</p><p class="acc-txt">精度: ±({acc_sys_mcu0_rdg:.4f}% R + {acc_sys_mcu0_fs:.4f}% FS)</p><p><b>MCU1:</b> R²={r2_sys_mcu1:.6f}</p><p class="acc-txt">精度: ±({acc_sys_mcu1_rdg:.4f}% R + {acc_sys_mcu1_fs:.4f}% FS)</p></div>
                </div>

                <h2 style="margin-top: 30px;">2. ✨ 全链路线性校准后评估 (折算至输入端)</h2>
                <div class="grid-2col">
                    <div class="metric-card" style="border-left: 5px solid #ffc107;">
                        <h4 style="margin-top:0;">全链路 ADS0 (内基准)</h4>
                        <p>最大绝对极限: <b style="color: #d9534f;">{max_err_cal_int:.4f} mV</b></p>
                        <p>{lbl_rms}: <b style="color: #ffc107;">{rms_int:.4f} mV</b></p>
                        <p>{lbl_pp}: <b style="color: #d9534f;">{pp_int:.4f} mV</b></p>
                        <p>全局 NFR: <b style="color: #ffc107;">{nfr_int_str}</b></p>
                        <p>全局 ENOB: <b style="color: #ffc107;">{enob_int_str}</b></p>
                    </div>
                    <div class="metric-card" style="border-left: 5px solid #28a745;">
                        <h4 style="margin-top:0;">全链路 ADS1 (外基准)</h4>
                        <p>最大绝对极限: <b style="color: #d9534f;">{max_err_cal_ext:.4f} mV</b></p>
                        <p>{lbl_rms}: <b style="color: #28a745;">{rms_ext:.4f} mV</b></p>
                        <p>{lbl_pp}: <b style="color: #d9534f;">{pp_ext:.4f} mV</b></p>
                        <p>全局 NFR: <b style="color: #28a745;">{nfr_ext_str}</b></p>
                        <p>全局 ENOB: <b style="color: #28a745;">{enob_ext_str}</b></p>
                    </div>
                    <div class="metric-card" style="border-left: 5px solid #6f42c1;">
                        <h4 style="margin-top:0;">全链路 MCU0 (单端)</h4>
                        <p>最大绝对极限: <b style="color: #d9534f;">{max_err_cal_mcu0:.4f} mV</b></p>
                        <p>{lbl_rms}: <b style="color: #6f42c1;">{rms_mcu0:.4f} mV</b></p>
                        <p>{lbl_pp}: <b style="color: #d9534f;">{pp_mcu0:.4f} mV</b></p>
                        <p>全局 NFR: <b style="color: #6f42c1;">{nfr_mcu0_str}</b></p>
                        <p>全局 ENOB: <b style="color: #6f42c1;">{enob_mcu0_str}</b></p>
                    </div>
                    <div class="metric-card" style="border-left: 5px solid #17a2b8;">
                        <h4 style="margin-top:0;">全链路 MCU1 (差分)</h4>
                        <p>最大绝对极限: <b style="color: #d9534f;">{max_err_cal_mcu1:.4f} mV</b></p>
                        <p>{lbl_rms}: <b style="color: #17a2b8;">{rms_mcu1:.4f} mV</b></p>
                        <p>{lbl_pp}: <b style="color: #d9534f;">{pp_mcu1:.4f} mV</b></p>
                        <p>全局 NFR: <b style="color: #17a2b8;">{nfr_mcu1_str}</b></p>
                        <p>全局 ENOB: <b style="color: #17a2b8;">{enob_mcu1_str}</b></p>
                    </div>
                </div>

                <h2>3. 全链路绝对误差图 (未校准)</h2><div class="chart-container">{tue_html}</div>
                <h2>4. 🔪 绝对误差溯源拆解图 {suffix_str}</h2><div class="chart-container">{trace_html}</div>
                <h2>5. 全链路 INL 误差对比图 {suffix_str}</h2><div class="chart-container">{inl_html}</div>
                <h2>6. 校准后极限残差 (底噪包络)</h2><div class="chart-container">{cal_html}</div>
                <h2>7. 📊 选定电压点底噪直方图与微观统计</h2>{hist_htmls_export}
                <h2>8. 硬件传递函数拟合度全景图</h2>
                <div class="grid-2col">
                    <div class="chart-container">{sys_ext_fit_html}</div>
                    <div class="chart-container">{sys_mcu1_fit_html}</div>
                </div>
                <div style="page-break-before: always;"></div>
                <h2>9. 📚 附录：核心测试项数学计算模型与对账指南</h2>
                <table class="math-table">
                    <tr><th style="width: 15%;">测试项 (Metric)</th><th style="width: 35%;">底层数学计算模型 (Formula)</th><th style="width: 50%;">工程评估意义与对账依据 (Significance)</th></tr>
                    <tr><td><b>实际增益 (k) 与 失调 (b)</b></td><td>基于最小二乘法 (OLS) 对传递函数求解。</td><td>提取信号链真实的物理放大倍数和零点漂移。<b>固件对账：</b>MCU 利用 <code>V_cal = (V_adc - b) / k</code> 进行两点线性补偿。</td></tr>
                    <tr><td><b>线性度 (R²)</b></td><td><code>R² = 1 - (Σ(y_i - ŷ_i)² / Σ(y_i - ȳ)²)</code></td><td>衡量实际响应曲线与理想直线的贴合程度。</td></tr>
                    <tr><td><b>绝对误差<br>(Absolute Error)</b></td><td><code>Error = V_read_actual - V_ideal</code></td><td>暴露系统未经任何软件修正前最原始的整体偏差。</td></tr>
                    <tr><td><b>积分非线性<br>(INL)</b></td><td><code>INL = V_read_actual - (k_fit * V_in_true + b_fit)</code></td><td>强制剥离可通过两点校准轻易消除的线性误差（k和b），暴露出硬件电路本质的“骨相弯曲”缺陷。</td></tr>
                    <tr><td><b>组内均值<br>(Local Mean)</b></td><td><code>Mean = Σ(x_i) / N</code></td><td>代表特定电压台阶下的平均测量绝对值。多次采样的均值能有效抵消随机热噪声，暴露出系统最纯粹的静态失调。</td></tr>
                    <tr><td><b>全局/局部标准差<br>(RMS Noise)</b></td><td><code>Std = √[Σ(x_i - Mean)² / (N-1)]</code></td><td>衡量数据偏离均值的离散程度，严格等效于交流热噪声均方根值 (RMS Noise)。</td></tr>
                    <tr><td><b>全局/局部峰峰值<br>(Peak-to-Peak)</b></td><td><code>P-P = Max - Min</code></td><td>反映极限噪声边界。它能敏锐地捕捉偶发的异常跳动或工频干扰，决定了系统在对应状态下的无噪声分辨率极限。</td></tr>
                    <tr><td><b>无噪声分辨率<br>(NFR)</b></td><td><code>NFR = log₂( FS_Input / V_peak_to_peak )</code></td><td>代表系统在最坏干扰下，输出数字代码完全不跳动的最保守物理有效位数（Flicker-Free Resolution）。</td></tr>
                    <tr><td><b>动态有效位数<br>(ENOB)</b></td><td><code>DC_ENOB = log₂( FS_Input / RMSE_Noise )</code></td><td>基于系统 1σ 均方根噪声计算的动态信噪比等效位数。</td></tr>
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
            st.download_button("📥 导出宽表数据 (Excel, 包含四路解耦数据)", data=buffer_export.getvalue(), file_name="DOE_Analysis_DC_Data.xlsx")
        with col_btn2:
            st.markdown(f'<a href="data:text/html;base64,{b64_html}" download="实测信号链_直流信号分析报告.html" target="_blank"><button style="background-color:#0056b3;color:white;padding:10px 20px;font-weight:bold;border:none;border-radius:5px;cursor:pointer;width:100%;">📊 下载交互式直流信号分析报告</button></a>', unsafe_allow_html=True)