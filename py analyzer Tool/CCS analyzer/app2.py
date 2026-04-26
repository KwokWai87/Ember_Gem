import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class HowlandApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Howland 电流源 DC 误差分析工具 (Tkinter 版)")
        self.root.geometry("1200x800")
        
        # 定义 UI 变量
        self.vars = {
            "R_gear": tk.DoubleVar(value=2490.0),
            "R_on": tk.DoubleVar(value=0.1),
            "G1": tk.DoubleVar(value=0.5),
            "beta": tk.DoubleVar(value=0.5),
            "A_OL_dB": tk.DoubleVar(value=120.0),
            "V_ref1": tk.DoubleVar(value=2.5),
            "V_load": tk.DoubleVar(value=5.0),
            "V_inp_min": tk.DoubleVar(value=-10.0),
            "V_inp_max": tk.DoubleVar(value=10.0),
            "err_gain": tk.DoubleVar(value=1e-6),
            "err_offset": tk.DoubleVar(value=5e-7),
            "err_load": tk.DoubleVar(value=2e-6),
            "err_leak": tk.DoubleVar(value=1e-8),
            "err_res": tk.DoubleVar(value=5e-7),
            "err_inl": tk.DoubleVar(value=2e-7),
            "err_drift": tk.DoubleVar(value=3e-7),
            "err_noise": tk.DoubleVar(value=1e-7),
            "target_acc": tk.DoubleVar(value=0.1)
        }
        
        self.setup_ui()
        self.calculate() # 初始计算一次

    def setup_ui(self):
        # 左侧输入面板 (带有滚动条)
        left_frame = ttk.Frame(self.root, width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        canvas = tk.Canvas(left_frame, width=330)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- 创建输入组件 ---
        row = 0
        def add_section(title):
            nonlocal row
            ttk.Label(self.scrollable_frame, text=title, font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, pady=(10, 5), sticky="w")
            row += 1

        def add_input(label_text, var_name):
            nonlocal row
            ttk.Label(self.scrollable_frame, text=label_text).grid(row=row, column=0, sticky="w", pady=2)
            ttk.Entry(self.scrollable_frame, textvariable=self.vars[var_name], width=15).grid(row=row, column=1, sticky="e", pady=2)
            row += 1

        add_section("电阻类参数")
        add_input("R_gear (Ω):", "R_gear")
        add_input("R_on (Ω):", "R_on")
        add_input("增益 G1:", "G1")
        add_input("反馈系数 β:", "beta")
        
        add_section("运放及系统参数")
        add_input("A_OL (dB):", "A_OL_dB")
        add_input("V_ref1 (V):", "V_ref1")
        add_input("V_load (V):", "V_load")
        add_input("V_inp 最小值 (V):", "V_inp_min")
        add_input("V_inp 最大值 (V):", "V_inp_max")
        
        add_section("基础误差预估 (A)")
        add_input("ΔI_gain:", "err_gain")
        add_input("ΔI_offset:", "err_offset")
        add_input("ΔI_load (动态负载):", "err_load")
        add_input("I_leak:", "err_leak")
        add_input("E_DC_Res:", "err_res")
        add_input("ΔI_INL:", "err_inl")
        add_input("ΔI_drift:", "err_drift")
        add_input("I_noise_RMS:", "err_noise")
        
        add_section("系统设定")
        add_input("目标精度 (%):", "target_acc")
        
        ttk.Button(self.scrollable_frame, text="重新计算", command=self.calculate).grid(row=row, column=0, columnspan=2, pady=20, sticky="we")

        # 右侧输出面板
        self.right_frame = ttk.Frame(self.root)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.text_result = tk.Text(self.right_frame, height=6, font=("Arial", 11))
        self.text_result.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 4))
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas_plot.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def calculate(self):
        try:
            # 1. 读取变量
            R_gear = self.vars["R_gear"].get()
            R_on = self.vars["R_on"].get()
            G1 = self.vars["G1"].get()
            beta = self.vars["beta"].get()
            A_OL = 10 ** (self.vars["A_OL_dB"].get() / 20)
            V_ref1 = self.vars["V_ref1"].get()
            V_load = self.vars["V_load"].get()
            
            if G1 == beta:
                messagebox.showerror("参数错误", "G1 不能等于 β，会导致分母为零。")
                return
                
            # 2. 核心数学模型
            R_total = R_gear + R_on
            R_zout = ((R_gear + R_on) * beta) / (G1 - beta)
            A_CL = A_OL / (1 + beta * A_OL)
            
            k = (A_CL * (1 - G1)) / R_total
            b = (A_CL * G1 * V_ref1) / R_total - V_load * (1/R_total + 1/R_zout)
            
            # 3. 误差合成
            errors = {
                "ΔI_gain": self.vars["err_gain"].get(),
                "ΔI_offset": self.vars["err_offset"].get(),
                "ΔI_load": self.vars["err_load"].get(),
                "I_leak": self.vars["err_leak"].get(),
                "E_DC_Res": self.vars["err_res"].get(),
                "ΔI_INL": self.vars["err_inl"].get(),
                "ΔI_drift": self.vars["err_drift"].get(),
                "I_noise_RMS": self.vars["err_noise"].get()
            }
            
            E_DC_Total_sq = sum([val**2 for val in errors.values()])
            E_DC_Total = np.sqrt(E_DC_Total_sq)
            
            weights = {key: (val**2 / E_DC_Total_sq) * 100 for key, val in errors.items()}
            dom_key = max(weights, key=weights.get)
            dom_weight = weights[dom_key]
            
            # 4. 曲线计算
            v_min = self.vars["V_inp_min"].get()
            v_max = self.vars["V_inp_max"].get()
            V_inp_arr = np.linspace(v_min, v_max, 500)
            
            I_out_ideal = (V_inp_arr * (1 - G1) + V_ref1 * G1) / R_gear
            I_out_actual = k * V_inp_arr + b
            
            with np.errstate(divide='ignore', invalid='ignore'):
                rel_err = np.abs((I_out_actual - I_out_ideal) / I_out_ideal) * 100
                max_rel_err = np.nanmax(rel_err[np.abs(I_out_ideal) > 1e-6])
                
            target_acc = self.vars["target_acc"].get()
            is_pass = max_rel_err <= target_acc
            
            # 5. 更新图表
            self.ax1.clear()
            self.ax1.plot(V_inp_arr, I_out_ideal, label="Ideal", linestyle="--")
            self.ax1.plot(V_inp_arr, I_out_actual, label="Actual")
            self.ax1.set_xlabel("V_inp (V)")
            self.ax1.set_ylabel("I_out (A)")
            self.ax1.set_title("V_inp vs I_out")
            self.ax1.legend()
            self.ax1.grid(True)
            
            self.ax2.clear()
            plot_labels = [k for k, v in weights.items() if v > 0.1]
            plot_sizes = [weights[k] for k in plot_labels]
            self.ax2.pie(plot_sizes, labels=plot_labels, autopct='%1.1f%%', startangle=90)
            self.ax2.set_title("Error Contribution")
            
            self.fig.tight_layout()
            self.canvas_plot.draw()
            
            # 6. 更新结论文本
            self.text_result.delete("1.0", tk.END)
            status = "【达标】" if is_pass else "【不达标】"
            result_str = f"设计目标判定: {status} (最大相对误差: {max_rel_err:.4f}%，目标 < {target_acc}%)\n\n"
            
            if round(R_gear, 0) == 2490 and V_load == 5.0 and dom_key == "ΔI_load":
                result_str += f"💡 提示: 当输入 R_gear={R_gear/1000}kΩ, V_load={V_load}V 时，动态负载误差占比 {dom_weight:.0f}%，\n为当前主导误差，建议优先优化电阻匹配度或提高运放 CMRR。"
            else:
                result_str += f"💡 分析: 当前主导误差项为 {dom_key} (占比 {dom_weight:.1f}%)。建议优先针对此项进行优化。"
                
            self.text_result.insert(tk.END, result_str)

        except Exception as e:
            messagebox.showerror("计算错误", f"输入数据有误或计算异常：\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HowlandApp(root)
    root.mainloop()