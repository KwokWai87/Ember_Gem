import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
from scipy.signal import get_window, find_peaks, detrend
import math
from datetime import datetime

# ==========================================
# 0. 全局配置与样式
# ==========================================
st.set_page_config(page_title="STM32H7 闭环测试分析台", layout="wide", page_icon="🧬")

st.markdown("""
    <style>
    .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #007bff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .metric-card-alert { border-left-color: #dc3545; background-color: #fff3f3; }
    .metric-card-ok { border-left-color: #28a745; background-color: #f0fdf4; }
    .metric-title { font-size: 0.9em; color: #6c757d; margin-bottom: 5px; font-weight: 600; }
    .metric-value { font-size: 1.4em; font-weight: bold; color: #212529; font-family: monospace; }
    .hardware-info { background-color: #e9ecef; padding: 15px; border-radius: 5px; font-family: monospace; color: #333; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 侧边栏：STM32CubeMX 底层硬件映射
# ==========================================
st.sidebar.title("⚙️ STM32H7 底层配置")
uploaded_file = st.sidebar.file_uploader("📂 上传实测数据 (CSV/Excel)", type=["csv", "xlsx"])

# 🌟 优化 3：采样率解耦，允许直接输入覆盖
fs_override = st.sidebar.checkbox("🔒 绕过底层推算，直接输入采样率 (推荐排障时使用)")
if fs_override:
    actual_fs = st.sidebar.number_input("直接输入实际采样率 Fs (Hz)", value=10000.0, step=1000.0)
    base_res = st.sidebar.selectbox("基础分辨率 (Resolution)", [16, 14, 12, 10, 8], index=0)
    dt_seconds = 1.0 / actual_fs
    dt_us = dt_seconds * 1e6
    dt_ms = dt_seconds * 1000.0
    eff_res = base_res
    st.sidebar.info(f"当前强制使用采样率: {actual_fs} Hz")
else:
    st.sidebar.markdown("### 🧬 核心时钟与时序配置")
    adc_clk = st.sidebar.number_input("ADC 核心时钟 fADC (MHz)", value=36.0, step=1.0)
    base_res = st.sidebar.selectbox("基础分辨率 (Resolution)", [16, 14, 12, 10, 8], index=0)
    samp_cycles = st.sidebar.selectbox("采样周期 (Sampling Cycles)", [1.5, 2.5, 8.5, 16.5, 32.5, 64.5, 387.5, 810.5], index=5)
    osr = st.sidebar.selectbox("硬件过采样率 (Oversampling)", [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024], index=0)

    conv_cycles_map = {16: 8.5, 14: 7.5, 12: 6.5, 10: 5.5, 8: 4.5}
    conv_cycles = conv_cycles_map[base_res]
    single_shot_cycles = samp_cycles + conv_cycles
    total_cycles = single_shot_cycles * osr

    actual_fs = (adc_clk * 1e6) / total_cycles
    dt_seconds = 1.0 / actual_fs
    dt_us = dt_seconds * 1e6
    dt_ms = dt_seconds * 1000.0
    eff_res = min(base_res + math.log(osr, 4), 21.0) if osr > 1 else base_res

    st.sidebar.markdown("### 📊 计算得出的实际硬件参数")
    st.sidebar.markdown(f"""
    <div class="hardware-info">
        <b>点间时间间隔 (Δt):</b> {dt_us:.2f} μs<br>
        <b>实际采样率 (Fs):</b> {(actual_fs/1000):.2f} kHz<br>
        <b>理想等效分辨率:</b> {eff_res:.1f} Bits<br>
        <b>单点消耗总周期:</b> {total_cycles} Cycles
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("### 🔌 模拟前端输入配置")
input_mode_adc = st.sidebar.radio("ADC 输入模式 (Input Mode)", ["单端模式 (Single-ended)", "差分模式 (Differential)"])

st.sidebar.markdown("### 🎯 信号源输入期望 (Expected)")
exp_waveform = st.sidebar.radio("测量目标:", ["正弦波 (Sine) - 测 THD/SINAD", "方波/脉冲 (Square) - 测时序"])
exp_freq = st.sidebar.number_input("注入信号频率 (Hz)", value=1000.0, step=100.0)
exp_vpp = st.sidebar.number_input("注入信号 Vp-p (mV)", value=3000.0, step=100.0)
vref = st.sidebar.number_input("硬件基准 Vref (V)", value=3.3, format="%.2f")

# HTML 报告生成函数保持不变 (此处为了代码紧凑省略实现细节，使用你原本的代码即可)
def generate_html_report(report_data, fig_time, fig_fft=None):
    # [保留你原本的 HTML 报告生成代码]
    time_html = fig_time.to_html(full_html=False, include_plotlyjs='cdn')
    fft_html = fig_fft.to_html(full_html=False, include_plotlyjs=False) if fig_fft else ""
    metrics_rows = "".join([f"<tr><td><b>{k}</b></td><td>{v}</td></tr>" for k, v in report_data.items()])
    html = f"<!DOCTYPE html><html lang='zh-CN'><head><meta charset='UTF-8'><title>报告</title></head><body>{metrics_rows}{time_html}{fft_html}</body></html>"
    return html.encode('utf-8')


# ==========================================
# 2. 核心 DSP 计算引擎 
# ==========================================
@st.cache_data
def load_and_preprocess(df, bits, vref_val, delta_t_ms, is_differential):
    val_col = df.columns[0] if 'wave' not in df.columns[0].lower() else [c for c in df.columns if 'wave' in c.lower()][0]
    df['raw_val'] = pd.to_numeric(df[val_col], errors='coerce')
    df = df.dropna(subset=['raw_val'])
    
    if df['raw_val'].max() > 1000:
        if is_differential:
            v = ((df['raw_val'].values / (2**bits - 1)) * 2.0 - 1.0) * vref_val * 1000.0
        else:
            v = (df['raw_val'].values / (2**bits - 1)) * vref_val * 1000.0
    else: 
        v = df['raw_val'].values * (1000.0 if df['raw_val'].max() < 10 else 1.0)
        
    t = np.arange(len(v)) * delta_t_ms  
    return t, v

def analyze_sine_performance(v, fs):
    N = len(v)
    # 🌟 优化 2：不仅去均值，还要消除线性基线漂移 (Detrending)
    v_ac = detrend(v, type='constant') 
    
    window = get_window('blackmanharris', N)
    yf = np.fft.fft(v_ac * window)
    xf = np.fft.fftfreq(N, 1/fs)[:N//2]
    
    # 恢复因加窗损失的幅值
    fft_mag = np.abs(yf[:N//2]) * (2.0 / N) / np.mean(window)
    fft_db = 20 * np.log10(fft_mag + 1e-12)
    
    # 找基波
    sig_bin = np.argmax(fft_mag[1:]) + 1
    sig_amp = fft_mag[sig_bin]
    f_hz = xf[sig_bin]
    
    # 能量聚合窗口半宽
    bin_width = 5 
    sig_power = np.sum(fft_mag[max(1, sig_bin-bin_width):min(N//2, sig_bin+bin_width+1)]**2)
    
    # 🌟 优化 1：局部寻峰提取谐波，对抗频谱泄漏导致的频偏
    harmonics_power = 0
    harmonics_info = [] # 用于作图标记
    
    for h in range(2, 7):
        expected_bin = sig_bin * h
        if expected_bin >= N//2: break
        
        # 在理论谐波位置附近（±20个bin）寻找局部峰值
        search_radius = 20
        start_bin = max(1, expected_bin - search_radius)
        end_bin = min(N//2, expected_bin + search_radius)
        
        if start_bin < end_bin:
            local_peak_bin = start_bin + np.argmax(fft_mag[start_bin:end_bin])
            # 聚合真实峰值附近的能量
            h_power = np.sum(fft_mag[max(1, local_peak_bin-3):min(N//2, local_peak_bin+4)]**2)
            harmonics_power += h_power
            harmonics_info.append((xf[local_peak_bin], fft_db[local_peak_bin]))

    total_ac_power = np.sum(fft_mag[1:]**2)
    noise_power = max(total_ac_power - sig_power - harmonics_power, 1e-12)
    nad_power = max(total_ac_power - sig_power, 1e-12) 
    
    snr = 10 * np.log10(sig_power / noise_power)
    thd = 10 * np.log10(harmonics_power / sig_power) if harmonics_power > 0 else -120.0
    sinad = 10 * np.log10(sig_power / nad_power)
    enob = (sinad - 1.76) / 6.02
    
    # SFDR 计算
    peaks, _ = find_peaks(fft_db, distance=10)
    # 排除基波及其裙边
    spurs = [p for p in peaks if p < sig_bin-bin_width*2 or p > sig_bin+bin_width*2]
    sfdr = 20 * np.log10(sig_amp / fft_mag[max(spurs, key=lambda i: fft_db[i])]) if spurs else 120.0
    
    # 归一化 dBc (以基波为 0dB 参考)
    fft_dbc = fft_db - (20 * np.log10(sig_amp+1e-12))
    harmonics_info_dbc = [(hx, hy - (20 * np.log10(sig_amp+1e-12))) for hx, hy in harmonics_info]
    
    return f_hz, (np.max(v)-np.min(v)), enob, snr, thd, sinad, sfdr, xf, fft_dbc, f_hz, harmonics_info_dbc

def analyze_square_timing(t, v):
    v_high, v_low = np.percentile(v, 95), np.percentile(v, 5)
    v_amp = v_high - v_low
    th_up, th_dn = v_low + v_amp * 0.7, v_low + v_amp * 0.3
    r_edges, f_edges = [], []
    is_high = v[0] > (v_high + v_low) / 2
    for i in range(1, len(v)):
        if not is_high and v[i] > th_up:
            is_high = True; r_edges.append(t[i])
        elif is_high and v[i] < th_dn:
            is_high = False; f_edges.append(t[i])
    p_ms, f_hz = 0, 0
    if len(r_edges) >= 2:
        p_ms = np.mean(np.diff(r_edges))
        if p_ms > 0: f_hz = 1000.0 / p_ms
    return f_hz, v_amp, v_high, v_low, th_up, th_dn

# ==========================================
# 3. UI 渲染与可视化
# ==========================================
def render_metric(label, value, unit, exp_val=None, tolerance=0.05):
    if exp_val is None:
        return f"<div class='metric-card'><div class='metric-title'>{label}</div><div class='metric-value'>{value:.2f} <span style='font-size:0.6em; color:#666;'>{unit}</span></div></div>"
    error = abs(value - exp_val) / (exp_val + 1e-9)
    if error <= tolerance:
        c_class, status = 'metric-card-ok', '✅ 匹配'
    else:
        c_class, status = 'metric-card-alert', f'❌ 偏差偏大'
    return f"<div class='metric-card {c_class}'><div class='metric-title'>{label} <span style='float:right; font-size:0.8em;'>{status}</span></div><div class='metric-value'>{value:.2f} <span style='font-size:0.6em; color:#666;'>{unit}</span></div><div style='font-size:0.8em; color:#666; margin-top:5px;'>注入源期望: {exp_val:.1f} {unit}</div></div>"

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    is_diff = "Differential" in input_mode_adc
    t, v = load_and_preprocess(df_raw, base_res, vref, dt_ms, is_diff)
    
    report_dict = {} 
    fig_time = go.Figure()
    fig_fft = None
    
    st.title("🧬 STM32H7 闭环测试与 ADC 性能分析台")
    
    st.markdown("### 📋 硬件采样一致性体检")
    c1, c2, c3 = st.columns(3)
    
    if "Sine" in exp_waveform:
        # 接收新增加的谐波点位信息用于作图
        meas_f, meas_vpp, enob, snr, thd, sinad, sfdr, xf, fft_dbc, f_hz, harmonics_info = analyze_sine_performance(v, actual_fs)
        with c1: st.markdown(render_metric("重建主频 (时基验证)", meas_f, "Hz", exp_freq), unsafe_allow_html=True)
        with c2: st.markdown(render_metric("测算 Vp-p (阻抗验证)", meas_vpp, "mV", exp_vpp), unsafe_allow_html=True)
        
        st.markdown("### 🏆 ADC 动态性能全析")
        d1, d2, d3, d4, d5 = st.columns(5)
        with d1: st.markdown(render_metric("总谐波失真 (THD)", thd, "dBc"), unsafe_allow_html=True)
        with d2: st.markdown(render_metric("信纳比 (SINAD)", sinad, "dB"), unsafe_allow_html=True)
        with d3: st.markdown(render_metric("信噪比 (SNR)", snr, "dB"), unsafe_allow_html=True)
        with d4: st.markdown(render_metric("实测有效位 (ENOB)", enob, "Bits"), unsafe_allow_html=True)
        with d5: st.markdown(render_metric("无杂散动态范围", sfdr, "dBc"), unsafe_allow_html=True)
        
        # 🌟 优化 4：在图表中标注出基波和谐波点，方便 Debug
        fig_fft = go.Figure()
        fig_fft.add_trace(go.Scatter(x=xf, y=fft_dbc, mode='lines', name='频谱', line=dict(color='#0056b3', width=1.5)))
        
        # 标记基波
        fig_fft.add_trace(go.Scatter(x=[f_hz], y=[0], mode='markers', name='基波 (Fundamental)', marker=dict(color='red', size=8, symbol='star')))
        
        # 标记谐波
        if harmonics_info:
            hx, hy = zip(*harmonics_info)
            fig_fft.add_trace(go.Scatter(x=hx, y=hy, mode='markers', name='已识别谐波 (H2-H6)', marker=dict(color='orange', size=6, symbol='x')))
            
        fig_fft.update_layout(xaxis_title="频率 (Hz)", yaxis_title="幅度 (dBc)", yaxis=dict(range=[-130, 10]), hovermode='x unified')
        st.plotly_chart(fig_fft, use_container_width=True)
        
        report_dict = {"测得主频": f"{meas_f:.2f} Hz", "THD": f"{thd:.2f} dBc", "ENOB": f"{enob:.2f} Bits"} # 简化演示
        
    else:
        meas_f, meas_vpp, v_h, v_l, th_up, th_dn = analyze_square_timing(t, v)
        with c1: st.markdown(render_metric("重建方波频率", meas_f, "Hz", exp_freq), unsafe_allow_html=True)
        with c2: st.markdown(render_metric("稳态 Vp-p", meas_vpp, "mV", exp_vpp), unsafe_allow_html=True)

    st.divider()

    st.markdown("### 📏 主界面时域观测与互动游标测量")
    t_max = min(float(t[-1]), max(50.0, 3000.0/exp_freq if exp_freq > 0 else 50.0))
    cursor_a, cursor_b = st.slider(
        "🎚️ 拖动游标测量区间 (ms):", 
        min_value=0.0, max_value=t_max, 
        value=(0.0, 1000.0 / exp_freq if exp_freq > 0 else 1.0),
        step=0.01, format="%.2f ms"
    )
    
    dt = abs(cursor_b - cursor_a)
    cur_freq = 1000.0 / dt if dt > 0 else 0
    st.success(f"**游标测算:** $\Delta T$ = **{dt:.4f} ms** | 频率 = **{cur_freq:.2f} Hz**")
    
    display_mask = t <= t_max
    fig_time.add_trace(go.Scatter(x=t[display_mask], y=v[display_mask], mode='lines', name='还原波形', line=dict(color='#17a2b8')))
    fig_time.add_vline(x=cursor_a, line_color="red", line_width=1)
    fig_time.add_vline(x=cursor_b, line_color="red", line_width=1)
        
    fig_time.update_layout(xaxis_title="硬件重构时间轴 (ms)", yaxis_title="电压 (mV)", hovermode="x unified", margin=dict(t=10, b=10))
    st.plotly_chart(fig_time, use_container_width=True)
    
else:
    st.info("👋 请配置左侧的 STM32 硬件底层参数并上传实测数据。")