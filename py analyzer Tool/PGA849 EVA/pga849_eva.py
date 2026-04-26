# ==============================================================================
# [分析工具] PGA84x + ADS1219 全信号链直流总误差与不确定度 (TUE & U) 评估系统 V11.1
# 核心更新: 1. 将 Tab 2 的双容差波形图无缝嵌入到脱机 HTML 工程报告中。
#           2. HTML 报告中的波形图保留了 Plotly 的交互性 (缩放、悬停查看具体数值)。
# ==============================================================================

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import base64
import io

# 页面基础设置
st.set_page_config(page_title="全信号链数字孪生与不确定度评估", layout="wide")

# ==============================================================================
# 0. CSV 模板与数据预处理
# ==============================================================================
DEFAULT_CSV_CONTENT = """Module,Parameter,Typ,Min,Max,Unit,Description
SYS,Cal_Residual_Offset,0,-10,10,uV,两点校准后的残余失调截距(RTO)
SYS,Delta_Temp,40,40,40,C,极端工作温度变化量
SYS,R_IN,100,100,100,Ohm,输入端低通滤波电阻
SYS,Delta_R_IN_pct,1,1,1,pct,两颗滤波电阻的公差失配
SYS,V_CM_spec,2.5,2.5,2.5,V,数据手册测试CMRR时的参考共模电压
SYS,Delta_V_PSRR,0.1,0.1,0.1,V,电源波动的偏离量
PGA,V_OSI,10,-50,50,uV,输入级失调电压
PGA,Gain_Error,10,-50,50,ppm,初始增益误差
PGA,INL,0.5,-2,2,ppm,增益非线性度
PGA,TCVos,0.2,-1,1,uV/C,失调温漂系数
PGA,Gain_Drift,1,-5,5,ppm/C,增益温漂系数
PGA,Noise_pp,2,2,2,uV,0.1~10Hz峰峰值低频噪声
PGA,CMRR,110,100,100,dB,共模抑制比
PGA,PSRR,120,110,110,dB,电源抑制比
PGA,I_B,0.5,-1,1,nA,输入偏置电流
PGA,I_OS,0.1,-0.5,0.5,nA,输入失调电流
ADC,V_OS,1,-4,4,uV,ADC初始失调
ADC,Gain_Error,0.005,-0.01,0.01,pct,ADC初始增益误差(%)
ADC,INL,1,-4,4,ppm,ADC非线性度(of FSR)
ADC,TCVos,0.01,-0.02,0.02,uV/C,ADC失调温漂
ADC,Gain_Drift,0.1,-0.3,0.3,ppm/C,ADC增益温漂
ADC,Noise_pp,10,19.7,19.7,uV,ADC低频噪声
VREF,VREF_ADC,2.5,2.495,2.505,V,ADC主基准电压 (决定FSR与LSB)
VREF,VREF_PGA,1.25,1.24,1.26,V,PGA输出共模偏置电压
VREF,Initial_Error,0.05,-0.15,0.15,pct,主基准初始精度误差(%)
VREF,Drift,2,-5,5,ppm/C,主基准温漂"""

@st.cache_data
def load_default_df():
    return pd.read_csv(io.StringIO(DEFAULT_CSV_CONTENT))

def get_param(df, module, param, value_type='MaxAbs'):
    row = df.loc[(df['Module'] == module) & (df['Parameter'] == param)]
    if row.empty: return 0.0
    if value_type == 'Typ': return float(row['Typ'].values[0])
    elif value_type == 'MaxAbs': return max(abs(float(row['Min'].values[0])), abs(float(row['Max'].values[0])))
    return 0.0

# ==============================================================================
# 1. 核心物理与数学计算模型
# ==============================================================================
@st.cache_data
def simulate_signal_chain(gain, condition, v_in_diff_array, v_cm_actual_array, df_config, k_factor):
    max_vin_diff = np.max(np.abs(v_in_diff_array))
    actual_fs_v = max_vin_diff * gain if max_vin_diff > 0 else 1.0
    
    ref_vref_adc = get_param(df_config, 'VREF', 'VREF_ADC', 'Typ')
    ref_vref_pga = get_param(df_config, 'VREF', 'VREF_PGA', 'Typ')
    
    fsr = 2 * ref_vref_adc if condition == "Mode-0 (全差分偏置)" else ref_vref_adc
    lsb_weight = (2 * ref_vref_adc) / (2 ** 24) if condition == "Mode-0 (全差分偏置)" else ref_vref_adc / (2 ** 23)
    
    delta_t = get_param(df_config, 'SYS', 'Delta_Temp', 'MaxAbs')
    r_in = get_param(df_config, 'SYS', 'R_IN', 'Typ')
    delta_r_in_pct = get_param(df_config, 'SYS', 'Delta_R_IN_pct', 'Typ')
    v_cm_spec = get_param(df_config, 'SYS', 'V_CM_spec', 'Typ')
    delta_v_psrr = get_param(df_config, 'SYS', 'Delta_V_PSRR', 'Typ')
    cal_residual = get_param(df_config, 'SYS', 'Cal_Residual_Offset', 'MaxAbs') * 1e-6
    
    to_u_b = lambda x: x / np.sqrt(3)
    to_u_n = lambda x: x / 6.6

    def calc_module_metrics(typ_dict, max_dict, module_name):
        typ_dyn = sum(v**2 for k, v in typ_dict.items() if 'dyn' in k)
        max_dyn = sum(v**2 for k, v in max_dict.items() if 'dyn' in k)
        u_dyn = sum(to_u_b(v)**2 if 'noise' not in k else to_u_n(v)**2 for k, v in max_dict.items() if 'dyn' in k)
        
        cal_res_typ_sq = typ_dict.get('cal_res_dyn', 0)**2
        cal_res_max_sq = max_dict.get('cal_res_dyn', 0)**2
        cal_res_u_sq = to_u_b(max_dict.get('cal_res_dyn', 0))**2

        breakdown = []
        name_map = {'inl_dyn': 'INL (非线性)', 'tcvos_dyn': 'TCVos (失调温漂)', 'gcdrift_dyn': 'Gain Drift (增益温漂)', 
                    'noise_dyn': 'Noise_pp (低频噪声)', 'cal_res_dyn': 'Cal_Residual (校准残余)', 'drift_dyn': 'VREF Drift (基准温漂)'}
        for k, v in max_dict.items():
            if 'dyn' in k or 'cal_res' in k:
                ai = v
                ui = to_u_n(v) if 'noise' in k else to_u_b(v)
                breakdown.append({
                    "模块": module_name, "误差项": name_map.get(k, k),
                    "极限限值 a_i (µV)": ai * 1e6, "标准不确定度 u_i (µV)": ui * 1e6, "方差贡献 (µV²)": (ui * 1e6)**2
                })

        return {
            "Typ_TUE_Cal": np.sqrt(cal_res_typ_sq + typ_dyn),
            "Max_TUE_Cal": np.sqrt(cal_res_max_sq + max_dyn),
            "U_Cal": np.sqrt(cal_res_u_sq + u_dyn),
            "breakdown": breakdown
        }

    def build_pga_dict(val_type):
        return {
            'inl_dyn': actual_fs_v * (get_param(df_config, 'PGA', 'INL', val_type) / 1e6),
            'tcvos_dyn': delta_t * (get_param(df_config, 'PGA', 'TCVos', val_type) * 1e-6) * gain,
            'gcdrift_dyn': delta_t * (get_param(df_config, 'PGA', 'Gain_Drift', val_type) / 1e6) * actual_fs_v,
            'noise_dyn': (get_param(df_config, 'PGA', 'Noise_pp', val_type) * 1e-6) * gain,
            'cal_res_dyn': cal_residual
        }
    pga_metrics = calc_module_metrics(build_pga_dict('Typ'), build_pga_dict('MaxAbs'), "PGA 前端")

    def build_adc_dict(val_type):
        return {
            'inl_dyn': fsr * (get_param(df_config, 'ADC', 'INL', val_type) / 1e6),
            'tcvos_dyn': delta_t * (get_param(df_config, 'ADC', 'TCVos', val_type) * 1e-6),
            'gcdrift_dyn': delta_t * (get_param(df_config, 'ADC', 'Gain_Drift', val_type) / 1e6) * actual_fs_v,
            'noise_dyn': get_param(df_config, 'ADC', 'Noise_pp', val_type) * 1e-6
        }
    adc_metrics = calc_module_metrics(build_adc_dict('Typ'), build_adc_dict('MaxAbs'), "ADC 本体")

    def build_ref_dict(val_type):
        return {'drift_dyn': delta_t * (get_param(df_config, 'VREF', 'Drift', val_type) / 1e6) * actual_fs_v}
    ref_metrics = calc_module_metrics(build_ref_dict('Typ'), build_ref_dict('MaxAbs'), "VREF 基准源")

    all_breakdown = pga_metrics['breakdown'] + adc_metrics['breakdown'] + ref_metrics['breakdown']
    sys_var_total = sum(row["方差贡献 (µV²)"] for row in all_breakdown)
    for row in all_breakdown:
        row["系统总方差占比 (%)"] = (row["方差贡献 (µV²)"] / sys_var_total * 100) if sys_var_total > 0 else 0
    df_breakdown = pd.DataFrame(all_breakdown).sort_values("系统总方差占比 (%)", ascending=False)

    sys_max_cal = np.sqrt(pga_metrics['Max_TUE_Cal']**2 + adc_metrics['Max_TUE_Cal']**2 + ref_metrics['Max_TUE_Cal']**2)
    sys_U_expanded = k_factor * np.sqrt(pga_metrics['U_Cal']**2 + adc_metrics['U_Cal']**2 + ref_metrics['U_Cal']**2)

    pga_a_ge_drift = delta_t * (get_param(df_config, 'PGA', 'Gain_Drift', 'MaxAbs') / 1e6) * np.abs(v_in_diff_array) * gain
    adc_a_ge_drift = delta_t * (get_param(df_config, 'ADC', 'Gain_Drift', 'MaxAbs') / 1e6) * np.abs(v_in_diff_array) * gain
    ref_a_drift = delta_t * (get_param(df_config, 'VREF', 'Drift', 'MaxAbs') / 1e6) * np.abs(v_in_diff_array) * gain
    
    pga_inl_a = actual_fs_v * (get_param(df_config, 'PGA', 'INL', 'MaxAbs') / 1e6)
    pga_tcvos_a = delta_t * (get_param(df_config, 'PGA', 'TCVos', 'MaxAbs') * 1e-6) * gain
    pga_noise_a = (get_param(df_config, 'PGA', 'Noise_pp', 'MaxAbs') * 1e-6) * gain
    adc_inl_a = fsr * (get_param(df_config, 'ADC', 'INL', 'MaxAbs') / 1e6)
    adc_tcvos_a = delta_t * (get_param(df_config, 'ADC', 'TCVos', 'MaxAbs') * 1e-6)
    adc_noise_a = get_param(df_config, 'ADC', 'Noise_pp', 'MaxAbs') * 1e-6

    dynamic_tue_sq = (
        (cal_residual**2 + pga_inl_a**2 + pga_tcvos_a**2 + pga_a_ge_drift**2 + pga_noise_a**2) +
        (adc_inl_a**2 + adc_tcvos_a**2 + adc_a_ge_drift**2 + adc_noise_a**2) + (ref_a_drift**2)
    )
    dynamic_tue_envelope = np.sqrt(dynamic_tue_sq)

    dynamic_u_c_sq = (
        (to_u_b(cal_residual)**2 + to_u_b(pga_inl_a)**2 + to_u_b(pga_tcvos_a)**2 + to_u_b(pga_a_ge_drift)**2 + to_u_n(pga_noise_a)**2) +
        (to_u_b(adc_inl_a)**2 + to_u_b(adc_tcvos_a)**2 + to_u_b(adc_a_ge_drift)**2 + to_u_n(adc_noise_a)**2) + (to_u_b(ref_a_drift)**2)
    )
    dynamic_u_envelope = np.sqrt(dynamic_u_c_sq) * k_factor

    typ_ge_pct = get_param(df_config, 'PGA', 'Gain_Error', 'Typ') / 1e6
    typ_v_osi_rto = (get_param(df_config, 'PGA', 'V_OSI', 'Typ') * 1e-6) * gain
    v_out_diff_actual = (gain * (1 + typ_ge_pct)) * v_in_diff_array + typ_v_osi_rto

    if condition == "Mode-0 (全差分偏置)":
        v_out_p_actual = ref_vref_pga + v_out_diff_actual / 2
        v_out_n_actual = ref_vref_pga - v_out_diff_actual / 2
    else:  
        v_out_p_actual = v_out_diff_actual
        v_out_n_actual = np.zeros_like(v_out_diff_actual)

    return {
        "sys_max_cal": sys_max_cal, "sys_U_expanded": sys_U_expanded,
        "lsb_weight": lsb_weight, "fsr": fsr, "df_breakdown": df_breakdown,
        "dynamic_tue_envelope": dynamic_tue_envelope, "dynamic_u_envelope": dynamic_u_envelope,
        "v_out_p_actual": v_out_p_actual, "v_out_n_actual": v_out_n_actual,
        "ref_adc": ref_vref_adc, "ref_pga": ref_vref_pga
    }

# ==============================================================================
# HTML 报告生成逻辑
# ==============================================================================
def generate_html_report(df_config, df_breakdown, res, k_factor, condition, gain, fig_diff):
    # 将 Plotly 图表转换为包含 JS CDN 的独立 HTML 块
    chart_html = fig_diff.to_html(full_html=False, include_plotlyjs='cdn')
    
    html = f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>信号链评估报告</title>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6; max-width: 1000px; margin: auto; padding: 20px; }}
        h1, h2, h3 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #fcfcfc; }}
        .highlight {{ background-color: #e8f4f8; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0; border-radius: 3px; }}
        .formula-box {{ background-color: #fdfdfd; border: 1px dashed #ccc; padding: 20px; border-radius: 5px; }}
        .chart-container {{ margin: 30px 0; border: 1px solid #eaeaea; padding: 10px; border-radius: 5px; background: #fff; }}
    </style></head><body>
    <h1>全信号链直流误差评估报告 (PGA + ADC + VREF)</h1>
    <div class="highlight">
        <p><strong>驱动工况:</strong> {condition} &nbsp;&nbsp; | &nbsp;&nbsp; <strong>PGA增益:</strong> {gain} V/V</p>
        <p><strong>ADC满量程 (FSR):</strong> {res['fsr']:.4f} V &nbsp;&nbsp; | &nbsp;&nbsp; <strong>1 LSB:</strong> {res['lsb_weight']*1e6:.2f} µV</p>
        <p><strong>Worst-Case TUE (物理极限边界):</strong> <span style="color:#d62728; font-weight:bold;">{res['sys_max_cal']*1e6:.2f} µV</span> ({res['sys_max_cal']/res['lsb_weight']:.1f} LSB)</p>
        <p><strong>U_Expanded (计量级扩展不确定度 k={k_factor}):</strong> <span style="color:#2ca02c; font-weight:bold;">{res['sys_U_expanded']*1e6:.2f} µV</span> ({res['sys_U_expanded']/res['lsb_weight']:.1f} LSB)</p>
    </div>
    
    <h2>1. 动态等效差分输出与双容差包络带</h2>
    <p><em>(注：下图保留了交互能力，可悬停查看各信号幅度下的极限 TUE 与不确定度 U_Expanded 偏差边界)</em></p>
    <div class="chart-container">
        {chart_html}
    </div>

    <h2>2. 误差项对账明细表 (两点校准后残余)</h2>
    {df_breakdown.to_html(index=False, float_format="%.2f")}
    
    <h2>3. 原始输入配置参数 (CSV)</h2>
    {df_config.to_html(index=False)}
    
    <h2>4. 核心计算公式与计量学说明</h2>
    <div class="formula-box">
        <p><strong>1. 常规限值降额 (B类不确定度-均匀分布):</strong><br>
        $$u_i = \\frac{{a_i}}{{\\sqrt{{3}}}}$$ <br> 
        <em>说明: 芯片手册给出的最大误差限值 $a_i$ (如失调、INL、温漂)，假定在其区间内服从均匀分布。</em></p>
        <p><strong>2. 低频噪声降额 (正态分布):</strong><br>
        $$u_{{noise}} = \\frac{{V_{{p-p}}}}{{6.6}}$$ <br>
        <em>说明: $0.1\\sim10\\text{{Hz}}$ 的峰峰值噪声覆盖约 99.9% 的置信区间 ($6.6\\sigma$)，除以 6.6 转化为标准差(RMS)。</em></p>
        <p><strong>3. 扩展不确定度合成 (RSS):</strong><br>
        $$U_{{Expanded}} = k \\cdot \\sqrt{{\\sum u_i^2}}$$ <br>
        <em>说明: 将各降额后的独立标准不确定度进行均方根合并，再乘以包含因子 $k$ ($k=2$ 对应约 95% 置信区间)。</em></p>
    </div></body></html>
    """
    return base64.b64encode(html.encode('utf-8')).decode('utf-8')

# ==============================================================================
# 2. UI 侧边栏与配置输入
# ==============================================================================
st.sidebar.title("🛠️ 全信号链评估配置")

uploaded_file = st.sidebar.file_uploader("📁 上传 CSV 配置文件", type=['csv'])
if uploaded_file is not None:
    df_config = pd.read_csv(uploaded_file)
    st.sidebar.success("CSV 覆盖成功！")
else:
    df_config = load_default_df()
    st.sidebar.info("当前使用默认配置。")

csv_string = df_config.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 下载标准配置模板", data=csv_string, file_name="template.csv", mime="text/csv")

st.sidebar.markdown("---")
st.sidebar.header("2. 扫描条件与工况")
input_type = st.sidebar.radio("输入类型", ["Single-Ended", "Differential"])
condition = st.sidebar.radio("ADC 驱动模式", ["Mode-0 (全差分偏置)", "Mode-1 (单端偏置)"])
gain = st.sidebar.number_input("PGA 增益 (G)", min_value=0.1, max_value=100.0, value=1.0)
k_factor = st.sidebar.selectbox("扩展不确定度包含因子 (k)", [1, 2, 3], index=1)

v_n_fixed = v_p_min = v_p_max = v_cm = diff_min = diff_max = 0
steps = 1000
if input_type == "Single-Ended":
    v_n_fixed = st.sidebar.number_input("Vn 固定偏置 (V)", value=0.0)
    v_p_min, v_p_max = st.sidebar.number_input("Vp 扫描极小值 (V)", value=0.0), st.sidebar.number_input("Vp 扫描极大值 (V)", value=1.25)
    V_n = np.full(steps, v_n_fixed)
    V_p = np.linspace(v_p_min, v_p_max, steps)
else:
    v_cm = st.sidebar.number_input("共模 Vcm (V)", value=1.25)
    diff_min, diff_max = st.sidebar.number_input("摆幅扫描极小值 (V)", value=-2.5), st.sidebar.number_input("摆幅扫描极大值 (V)", value=2.5)
    half_diff = np.linspace(diff_min, diff_max, steps) / 2
    V_p = v_cm + half_diff
    V_n = v_cm - half_diff

V_in_diff = V_p - V_n
V_cm_actual = (V_p + V_n) / 2

# 执行核心计算
res = simulate_signal_chain(gain, condition, V_in_diff, V_cm_actual, df_config, k_factor)

# ==============================================================================
# 3. 提前生成复用图表 (供 UI 和 HTML 报告调用)
# ==============================================================================
fig_diff = go.Figure()
y_ideal_diff = V_in_diff * gain
tue_band = res["dynamic_tue_envelope"]
u_band = res["dynamic_u_envelope"]

# 画理想线
fig_diff.add_trace(go.Scatter(x=V_in_diff, y=y_ideal_diff, mode='lines', name='理想差分输出', line=dict(color='black', width=2)))
# 画 TUE (最外层红带)
fig_diff.add_trace(go.Scatter(x=V_in_diff, y=y_ideal_diff + tue_band, mode='lines', line=dict(width=0), showlegend=False))
fig_diff.add_trace(go.Scatter(x=V_in_diff, y=y_ideal_diff - tue_band, mode='lines', name='± Max TUE (物理极限)', fill='tonexty', fillcolor='rgba(255, 0, 0, 0.1)', line=dict(width=0)))
# 画 U_Expanded (内层绿带)
fig_diff.add_trace(go.Scatter(x=V_in_diff, y=y_ideal_diff + u_band, mode='lines', line=dict(width=0), showlegend=False))
fig_diff.add_trace(go.Scatter(x=V_in_diff, y=y_ideal_diff - u_band, mode='lines', name=f'± U_Expanded (k={k_factor})', fill='tonexty', fillcolor='rgba(0, 128, 0, 0.2)', line=dict(width=0)))

fig_diff.update_layout(
    xaxis_title="输入端差分电压 V_in_diff (V)", 
    yaxis_title="差分等效输出电压 (V)", 
    height=450, 
    template="plotly_white", 
    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5)
)

st.sidebar.markdown("---")
# 注入包含波形图的 HTML 报告
html_b64 = generate_html_report(df_config, res['df_breakdown'], res, k_factor, condition, gain, fig_diff)
href = f'<a href="data:text/html;base64,{html_b64}" download="Signal_Chain_Report.html" style="text-decoration:none;"><button style="width:100%; padding:10px; background-color:#1E90FF; color:white; border:none; border-radius:5px; cursor:pointer;">📄 导出 HTML 详细报告</button></a>'
st.sidebar.markdown(href, unsafe_allow_html=True)

# ==============================================================================
# 4. UI 渲染逻辑
# ==============================================================================
st.title("系统级信号链数字孪生与不确定度评定")
st.caption(f"当前系统基准配置: ADC 主基准 = {res['ref_adc']}V | PGA 偏置基准 = {res['ref_pga']}V")

tab1, tab2, tab3 = st.tabs(["📋 1. 规格对标与对账明细", "📈 2. 物理节点与双容差波形", "⚙️ 3. 输入参数预览"])

with tab1:
    col1, col2, col3 = st.columns(3)
    lsb_uv = res['lsb_weight'] * 1e6
    impact_max = (res['sys_max_cal'] * 1e6) / lsb_uv
    impact_u = (res['sys_U_expanded'] * 1e6) / lsb_uv

    with col1:
        st.info("📐 **ADC 物理量纲 (Baseline)**")
        st.metric("满量程 (FSR)", f"{res['fsr']:.3f} V")
        st.metric("1 LSB 权重", f"{lsb_uv:.3f} µV")
    with col2:
        st.error("⚠️ **物理极限残余 (Max TUE)**")
        st.metric("全链路绝对总误差", f"{res['sys_max_cal']*1e6:.2f} µV")
        st.metric("占用 LSB 当量", f"{impact_max:.1f} LSB")
    with col3:
        st.success(f"✅ **扩展不确定度 (U_Expanded, k={k_factor})**")
        st.metric("计量级置信区间带", f"{res['sys_U_expanded']*1e6:.2f} µV")
        st.metric("占用 LSB 当量", f"{impact_u:.1f} LSB")
        
    st.markdown("---")
    st.markdown("### 误差项计算对账明细 (按方差贡献率排序)")
    st.dataframe(res['df_breakdown'].style.format({
        "极限限值 a_i (µV)": "{:.2f}",
        "标准不确定度 u_i (µV)": "{:.2f}",
        "方差贡献 (µV²)": "{:.2f}",
        "系统总方差占比 (%)": "{:.2f}%"
    }), use_container_width=True)

with tab2:
    st.markdown("### 1. 物理单端节点电压 (Vout_p & Vout_n)")
    fig_nodes = go.Figure()
    fig_nodes.add_trace(go.Scatter(x=V_in_diff, y=res['v_out_p_actual'], mode='lines', name='Vout_p (实际含偏置)', line=dict(color='#ff7f0e', width=2)))
    fig_nodes.add_trace(go.Scatter(x=V_in_diff, y=res['v_out_n_actual'], mode='lines', name='Vout_n (实际含偏置)', line=dict(color='#9467bd', width=2)))
    fig_nodes.update_layout(xaxis_title="输入端差分电压 V_in_diff (V)", yaxis_title="单端绝对电压 (V)", height=350, template="plotly_white", margin=dict(t=30, b=10))
    st.plotly_chart(fig_nodes, use_container_width=True)

    st.markdown("### 2. 等效差分输出与双容差包络带")
    st.info("💡 **红带 (外层):** 最恶劣物理条件下的 100% TUE 极限边界。 **绿带 (内层):** 具有统计意义的计量级置信区间。")
    # 直接渲染前面提前生成的 fig_diff 图表对象
    st.plotly_chart(fig_diff, use_container_width=True)

with tab3:
    st.markdown("### 当前注入的底层配置字典 (CSV)")
    st.dataframe(df_config, use_container_width=True)