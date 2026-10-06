import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

# --- 頁面設定 ---
st.set_page_config(page_title="高爾頓板 (Galton Board) 模擬器", layout="centered")

st.title("高爾頓板 (Galton Board) 動態模擬")
st.markdown("""
**高爾頓板（Galton board）**是由一塊帶有交錯排列釘子的直立板塊所構成。當裝置保持水平時，從頂部丟下珠子，珠子在撞擊釘子時會隨機向左或向右彈跳。最終它們會收集在底部的凹槽中，累積在凹槽裡的珠子圓柱高度會近似於**鐘形曲線（常態分佈）**。

將**帕斯卡三角形（Pascal's triangle）**疊加在釘子上，可以顯示出到達每個凹槽的不同路徑數量。
""")
st.divider()

# --- 側邊欄控制 ---
st.sidebar.header("控制面板")
levels = st.sidebar.slider("釘子層數 (Rows of pegs)", min_value=7, max_value=15, value=11, step=1)

animate = st.sidebar.checkbox("開啟掉落動畫 (較耗效能)", value=True)
if animate:
    beads = st.sidebar.slider("珠子總數", min_value=50, max_value=300, value=150, step=10)
    st.sidebar.caption("💡 提示：開啟動畫時，為確保流暢度，珠子數量上限設為 300。")
else:
    beads = st.sidebar.slider("珠子總數", min_value=100, max_value=1500, value=500, step=100)

color_choice = st.sidebar.selectbox(
    "滾珠款式 (金屬質感)", 
    ["白銀 (Silver)", "黃金 (Gold)", "青銅 (Bronze)", "紅寶石 (Ruby)", "藍寶石 (Sapphire)", "翡翠 (Emerald)"]
)

# 顏色對應表
color_map = {
    "白銀 (Silver)": "#E0E0E0",
    "黃金 (Gold)": "#FFD700",
    "青銅 (Bronze)": "#CD7F32",
    "紅寶石 (Ruby)": "#E52B50",
    "藍寶石 (Sapphire)": "#0F52BA",
    "翡翠 (Emerald)": "#50C878"
}
base_color = color_map[color_choice]

if st.button("🚀 開始投放滾珠"):
    # --- 1. 物理路徑計算 ---
    # 記錄每顆珠子的路徑：起始在 x=0，每層隨機向左(-0.5)或向右(+0.5)
    paths = np.zeros((beads, levels + 1))
    for i in range(beads):
        steps = np.random.choice([-0.5, 0.5], size=levels)
        paths[i, 1:] = np.cumsum(steps)
        
    final_bins = paths[:, -1]
    
    # 計算堆疊高度：模擬真實珠子疊加在分區中的高度
    stack_idx = np.zeros(beads)
    current_counts = {}
    for i in range(beads):
        b = final_bins[i]
        if b not in current_counts:
            current_counts[b] = 0
        stack_idx[i] = current_counts[b]
        current_counts[b] += 1
        
    max_stack = max(current_counts.values()) if current_counts else 0

    # --- 2. 畫布與背景設置 ---
    # 參考 Galton_box.jpg，設定木質色系背景
    fig, ax = plt.subplots(figsize=(8, 10))
    wood_color = '#A67B5B'
    fig.patch.set_facecolor('#111111') # 外框背景
    ax.set_facecolor(wood_color)       # 木板背景
    
    # 座標邊界計算
    x_max = levels / 2.0 + 1.5
    y_max = 3
    bead_diameter = 0.6  # 珠子垂直堆疊的高度間距
    y_floor = -levels - (max_stack * bead_diameter) - 1.5
    y_min = y_floor - 0.5
    
    # 釘子座標
    peg_x, peg_y = [], []
    for r in range(levels):
        for i in range(r + 1):
            peg_x.append(i - r / 2.0)
            peg_y.append(-r)
            
    # 分區擋板座標
    wall_xs = np.arange(-levels/2 - 0.5, levels/2 + 1.5, 1)

    def draw_background():
        """繪製背景：頂部導流板、釘子、分區擋板"""
        ax.set_xlim(-x_max, x_max)
        ax.set_ylim(y_min, y_max)
        ax.axis('off')
        
        # 繪製頂部 V 型導流木塊 (還原圖片視覺)
        ax.fill([-x_max, -1, -x_max], [y_max, 1, 1], color='#C19A6B', edgecolor='#5C4033', lw=2)
        ax.fill([x_max, 1, x_max], [y_max, 1, 1], color='#C19A6B', edgecolor='#5C4033', lw=2)
        
        # 繪製金屬釘子
        ax.scatter(peg_x, peg_y, color='#B0C4DE', s=60, edgecolors='#333333', linewidth=1.5, zorder=1)
        
        # 繪製垂直分區擋板
        for wx in wall_xs:
            ax.plot([wx, wx], [y_floor, -levels + 0.5], color='#D2B48C', linewidth=4, zorder=1)
        # 繪製底板
        ax.plot([-x_max, x_max], [y_floor, y_floor], color='#D2B48C', linewidth=6, zorder=1)

    plot_placeholder = st.empty()

    # 珠子視覺參數：大小與金屬高光偏移量
    bead_size = 120
    highlight_size = 25
    offset = 0.08 
    
    if animate:
        # --- 3. 動態掉落動畫 ---
        drop_rate = max(1, beads // 30)
        fall_speed = 0.7 
        max_steps = (beads // drop_rate) + levels + int((abs(y_floor) + max_stack) / fall_speed) + 5
        
        # 預先分配記憶體
        X = np.full((beads, max_steps), np.nan)
        Y = np.full((beads, max_steps), np.nan)
        
        progress_bar = st.progress(0)
        
        for i in range(beads):
            t_start = i // drop_rate
            
            # 第一階段：在釘子間穿梭
            for k in range(levels + 1):
                t_curr = t_start + k
                if t_curr < max_steps:
                    X[i, t_curr] = paths[i, k]
                    Y[i, t_curr] = -k
                    
            # 第二階段：筆直落下到凹槽
            target_x = paths[i, levels]
            final_y = y_floor + (bead_diameter / 2) + (stack_idx[i] * bead_diameter)
            
            fall_dist = abs(-levels - final_y)
            fall_frames = int(fall_dist / fall_speed) + 1
            
            for f in range(1, fall_frames + 1):
                t_curr = t_start + levels + f
                if t_curr < max_steps:
                    X[i, t_curr] = target_x
                    Y[i, t_curr] = max(-levels - f * fall_speed, final_y)
                    
            # 第三階段：靜止在堆疊位置
            t_rest = t_start + levels + fall_frames + 1
            if t_rest < max_steps:
                X[i, t_rest:] = target_x
                Y[i, t_rest:] = final_y

        # 逐格渲染
        for t in range(0, max_steps):
            ax.clear()
            draw_background()
            
            curr_x = X[:, t]
            curr_y = Y[:, t]
            valid = ~np.isnan(curr_x)
            
            if np.any(valid):
                vx = curr_x[valid]
                vy = curr_y[valid]
                
                # 繪製主體與立體高光
                ax.scatter(vx, vy, color=base_color, s=bead_size, edgecolors='#222222', linewidth=1, zorder=2)
                ax.scatter(vx - offset, vy + offset, color='white', s=highlight_size, alpha=0.8, zorder=3)
                
            plot_placeholder.pyplot(fig)
            progress_bar.progress(min(1.0, (t + 1) / max_steps))
            
        progress_bar.empty()

    else:
        # --- 4. 靜態結果直接顯示 ---
        draw_background()
        
        # 最終座標
        final_x = paths[:, -1]
        final_y = y_floor + (bead_diameter / 2) + (stack_idx * bead_diameter)
        
        ax.scatter(final_x, final_y, color=base_color, s=bead_size, edgecolors='#222222', linewidth=1, zorder=2)
        ax.scatter(final_x - offset, final_y + offset, color='white', s=highlight_size, alpha=0.8, zorder=3)
        
        plot_placeholder.pyplot(fig)

    st.success("🎉 模擬完成！")
