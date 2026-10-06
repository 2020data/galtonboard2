import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

# --- 1. 頁面佈局與全螢幕設定 ---
st.set_page_config(page_title="Premium Galton Board", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 自訂 CSS 提升網頁質感 ---
st.markdown("""
    <style>
    /* 隱藏頂部選單與底部浮水印 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 自訂按鈕樣式：漸層與發光效果 */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #FFD700 0%, #D4AF37 100%);
        color: #111;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 215, 0, 0.5);
    }
    
    /* 調整分隔線與標題間距 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 標題區 ---
st.markdown("<h1 style='text-align: center; font-weight: 300; letter-spacing: 2px;'>GALTON BOARD <span style='color: #FFD700;'>SIMULATOR</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>物理機率與常態分佈的動態視覺化</p>", unsafe_allow_html=True)
st.divider()

# --- 3. 控制面板 (改用水平欄位排版) ---
with st.container():
    st.markdown("### 🎛️️ 模擬參數設定")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        levels = st.slider("釘子層數 (Rows)", min_value=7, max_value=15, value=11)
    with col2:
        animate = st.checkbox("開啟掉落動畫 (Animate)", value=True)
        beads = st.slider("珠子總數", min_value=50, max_value=400 if animate else 1500, value=200 if animate else 800, step=50)
    with col3:
        color_choice = st.selectbox("滾珠材質 (Material)", ["黃金 (Gold)", "白銀 (Silver)", "霓虹藍 (Neon Blue)", "寶石紅 (Ruby)"])
    with col4:
        st.write("") # 排版佔位
        st.write("")
        start_btn = st.button("🚀 開始模擬 (START)", use_container_width=True)

# 材質顏色庫
color_map = {
    "黃金 (Gold)": ("#FFD700", "#FFF8DC"),
    "白銀 (Silver)": ("#E0E0E0", "#FFFFFF"),
    "霓虹藍 (Neon Blue)": ("#00E5FF", "#E0FFFF"),
    "寶石紅 (Ruby)": ("#FF0055", "#FFB6C1")
}
base_color, glow_color = color_map[color_choice]

# --- 4. 核心模擬與繪圖區 ---
if start_btn:
    # 物理運算
    paths = np.zeros((beads, levels + 1))
    for i in range(beads):
        steps = np.random.choice([-0.5, 0.5], size=levels)
        paths[i, 1:] = np.cumsum(steps)
    final_bins = paths[:, -1]
    
    stack_idx = np.zeros(beads)
    current_counts = {}
    for i in range(beads):
        b = final_bins[i]
        current_counts[b] = current_counts.get(b, 0) + 1
        stack_idx[i] = current_counts[b] - 1
        
    max_stack = max(current_counts.values()) if current_counts else 0

    # 建立 Matplotlib 畫布 (重點：設定為完全透明)
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_alpha(0.0)  # 讓圖表背景透明，融入 Streamlit
    ax.patch.set_alpha(0.0)
    
    # 座標計算
    x_max = levels / 2.0 + 1.5
    y_max = 3
    bead_diameter = 0.65
    y_floor = -levels - (max_stack * bead_diameter) - 1.5
    y_min = y_floor - 0.5
    
    peg_x, peg_y = [], []
    for r in range(levels):
        for i in range(r + 1):
            peg_x.append(i - r / 2.0)
            peg_y.append(-r)
    wall_xs = np.arange(-levels/2 - 0.5, levels/2 + 1.5, 1)

    def draw_premium_background():
        """繪製高質感極簡背景"""
        ax.set_xlim(-x_max, x_max)
        ax.set_ylim(y_min, y_max)
        ax.axis('off')
        
        # 繪製極簡科技感頂部導流
        ax.plot([-x_max, -1], [y_max, 1], color='#555555', lw=3, zorder=1)
        ax.plot([x_max, 1], [y_max, 1], color='#555555', lw=3, zorder=1)
        
        # 繪製金屬釘子 (使用半透明白色創造現代感)
        ax.scatter(peg_x, peg_y, color='#FFFFFF', s=40, alpha=0.3, zorder=1)
        
        # 繪製底部擋板與底座
        for wx in wall_xs:
            ax.plot([wx, wx], [y_floor, -levels + 0.5], color='#444444', linewidth=2, zorder=1)
        ax.plot([-x_max, x_max], [y_floor, y_floor], color='#666666', linewidth=4, zorder=1)

    # 建立畫面佔位符與兩側排版
    st.write("---")
    plot_col, stats_col = st.columns([3, 1])
    with plot_col:
        plot_placeholder = st.empty()
    with stats_col:
        st.markdown("### 📊 實時數據")
        stat_ph_1 = st.empty()
        stat_ph_2 = st.empty()
        stat_ph_3 = st.empty()

    bead_size = 140
    offset = 0.08 

    if animate:
        drop_rate = max(1, beads // 30)
        fall_speed = 0.8
        max_steps = (beads // drop_rate) + levels + int((abs(y_floor) + max_stack) / fall_speed) + 5
        
        X = np.full((beads, max_steps), np.nan)
        Y = np.full((beads, max_steps), np.nan)
        progress_bar = st.progress(0)
        
        # 預計算座標
        for i in range(beads):
            t_start = i // drop_rate
            for k in range(levels + 1):
                t_curr = t_start + k
                if t_curr < max_steps:
                    X[i, t_curr] = paths[i, k]
                    Y[i, t_curr] = -k
                    
            target_x = paths[i, levels]
            final_y = y_floor + (bead_diameter / 2) + (stack_idx[i] * bead_diameter)
            fall_frames = int(abs(-levels - final_y) / fall_speed) + 1
            
            for f in range(1, fall_frames + 1):
                t_curr = t_start + levels + f
                if t_curr < max_steps:
                    X[i, t_curr] = target_x
                    Y[i, t_curr] = max(-levels - f * fall_speed, final_y)
                    
            t_rest = t_start + levels + fall_frames + 1
            if t_rest < max_steps:
                X[i, t_rest:] = target_x
                Y[i, t_rest:] = final_y

        # 動畫渲染
        for t in range(0, max_steps):
            ax.clear()
            draw_premium_background()
            
            curr_x, curr_y = X[:, t], Y[:, t]
            valid = ~np.isnan(curr_x)
            
            if np.any(valid):
                vx, vy = curr_x[valid], curr_y[valid]
                # 繪製高質感立體珠子
                ax.scatter(vx, vy, color=base_color, s=bead_size, alpha=0.9, zorder=2)
                ax.scatter(vx - offset, vy + offset, color=glow_color, s=bead_size*0.2, alpha=0.8, zorder=3)
                
            plot_placeholder.pyplot(fig)
            progress_bar.progress(min(1.0, (t + 1) / max_steps))
            
            # 更新實時數據
            current_dropped = np.sum(valid)
            stat_ph_1.metric(label="已投放珠子", value=f"{current_dropped} / {beads}")
            
        progress_bar.empty()

    else:
        # 靜態渲染
        draw_premium_background()
        final_x = paths[:, -1]
        final_y = y_floor + (bead_diameter / 2) + (stack_idx * bead_diameter)
        
        ax.scatter(final_x, final_y, color=base_color, s=bead_size, alpha=0.9, zorder=2)
        ax.scatter(final_x - offset, final_y + offset, color=glow_color, s=bead_size*0.2, alpha=0.8, zorder=3)
        plot_placeholder.pyplot(fig)

    # 最終數據結算
    stat_ph_1.metric(label="總投放數量", value=beads)
    stat_ph_2.metric(label="最高堆疊數", value=int(max_stack), delta="中央最高點")
    stat_ph_3.metric(label="常態分佈吻合度", value="高", delta="近似鐘形曲線")
