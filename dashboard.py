import streamlit as st
import pandas as pd
import altair as alt
import sqlite3
from config import USERS

# ✅ Streamlit 設定必須在最前面
st.set_page_config(
    page_title="能源用電 Dashboard",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ✅ 登入機制與登出功能
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 登入驗證")
    username = st.text_input("帳號")
    password = st.text_input("密碼", type="password")
    if st.button("登入"):
        if username in USERS and password == USERS[username]:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("帳號或密碼錯誤")
    st.stop()

# ✅ 登入成功後才執行主畫面
# ------------------------------------------------------------

# 移除 Streamlit 預設 footer 與 menu
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ✅ 顯示登出按鈕（右上角）
with st.sidebar:
    if st.button("🚪 登出"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

# --- 頁首 ---
st.markdown("""
<h1 style='text-align: center; color: #00AEEF;'>⚡ 能源用電視覺分析 Dashboard</h1>
<p style='text-align: center; color: gray;'>分析充電樁交易、耗電量、分時行為與趨勢</p>
<hr>
""", unsafe_allow_html=True)

# 從資料庫讀取
conn = sqlite3.connect("energy_ocpp.db")
df = pd.read_sql_query("""
    
    SELECT id, cp_id, transaction_id, id_tag, start_time, stop_time, meter_start, meter_stop,
           (meter_stop - meter_start) AS used_kwh

    FROM transactions
    WHERE meter_start IS NOT NULL AND meter_stop IS NOT NULL
    ORDER BY id DESC
""", conn)
conn.close()

if df.empty:
    st.warning("目前沒有完整的交易資料（含 meter_start 和 meter_stop）")
else:
    # 篩選條件
    st.sidebar.header("🔎 篩選條件")
    cp_options = ["全部"] + sorted(df["cp_id"].unique())
    selected_cp = st.sidebar.selectbox("選擇充電樁", cp_options)

    search_tag = st.sidebar.text_input("搜尋使用者帳號 (id_tag)")

    df['datetime'] = pd.to_datetime(df['start_time'])
    min_date = df['datetime'].min().date()
    max_date = df['datetime'].max().date()
    start_date, end_date = st.sidebar.date_input(
        "選擇日期範圍",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    df = df[(df['datetime'].dt.date >= start_date) & (df['datetime'].dt.date <=     end_date)]

    if selected_cp != "全部":
        df = df[df["cp_id"] == selected_cp]

    if search_tag:
        df = df[df["id_tag"].str.contains(search_tag, case=False, na=False)]


    # 📈 每日用電量趨勢
    with st.container():
        st.subheader("📈 每日用電量趨勢")
        df['date'] = df['datetime'].dt.date
        daily_summary = df.groupby('date')['used_kwh'].sum().reset_index()

        line_chart = alt.Chart(daily_summary).mark_line(point=True, color="#1f77b4").encode(
            x=alt.X("date:T", title="日期"),
            y=alt.Y("used_kwh:Q", title="總耗電量 (kWh)"),
            tooltip=["date", "used_kwh"]
        ).properties(width=700, height=400)
        st.altair_chart(line_chart, use_container_width=True)

        # 📊 每日交易數量
        daily_count = df.groupby('date')['transaction_id'].nunique().reset_index()
        daily_count_chart = alt.Chart(daily_count).mark_bar(color="#ff7f0e").encode(
            x=alt.X("date:T", title="日期"),
            y=alt.Y("transaction_id:Q", title="交易次數"),
            tooltip=["date", "transaction_id"]
        ).properties(width=700, height=300)
        st.altair_chart(daily_count_chart, use_container_width=True)

    # ⏰ 尖離峰分析
    with st.container():
        st.subheader("⏰ 尖離峰時段耗電統計")
        df['hour'] = df['datetime'].dt.hour

        def classify_time(hour):
            if 17 <= hour <= 21:
                return "尖峰時段"
            elif 10 <= hour <= 16:
                return "平時時段"
            else:
                return "離峰時段"

        df['period'] = df['hour'].apply(classify_time)
        period_summary = df.groupby('period')['used_kwh'].sum().reset_index()

        period_chart = alt.Chart(period_summary).mark_bar().encode(
            x=alt.X("period:N", title="時段"),
            y=alt.Y("used_kwh:Q", title="總耗電量 (kWh)"),
            color=alt.Color("period:N", scale=alt.Scale(scheme='blues')),
            tooltip=["period", "used_kwh"]
        ).properties(width=600, height=400)
        st.altair_chart(period_chart, use_container_width=True)

    # 🥧 用電佔比
    with st.container():
        st.subheader("🥧 各充電樁用電佔比（所有資料）")
        full_df = df.copy()
        full_df['cp_id'] = full_df['cp_id'].fillna("未知")
        cp_summary = full_df.groupby('cp_id')['used_kwh'].sum().reset_index()

        pie_chart = alt.Chart(cp_summary).mark_arc(innerRadius=50).encode(
            theta="used_kwh:Q",
            color="cp_id:N",
            tooltip=["cp_id", "used_kwh"]
        ).properties(width=500, height=400)
        st.altair_chart(pie_chart, use_container_width=False)

    # 🔹 單筆交易圖表
    with st.container():
        st.subheader("🔹 每筆交易耗電量")
        bar_chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("transaction_id:O", title="交易 ID"),
            y=alt.Y("used_kwh:Q", title="耗電量 (kWh)"),
            color=alt.value("#1f77b4"),
            tooltip=["cp_id", "id_tag", "used_kwh"]
        ).properties(width=700, height=400)
        st.altair_chart(bar_chart, use_container_width=True)

    # 🕒 每筆充電時間分析
    df['end_time'] = pd.to_datetime(df['start_time']) + pd.to_timedelta(df['used_kwh'] / 7.2, unit='h')
    df['charge_duration'] = (df['end_time'] - df['datetime']).dt.total_seconds() / 60

    with st.container():
        st.subheader("🕒 每筆充電時間分析（分鐘）")
        duration_chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("transaction_id:O", title="交易 ID"),
            y=alt.Y("charge_duration:Q", title="充電時間（分鐘）"),
            color=alt.value("#2ca02c"),
            tooltip=["cp_id", "id_tag", "charge_duration"]
        ).properties(width=700, height=300)
        st.altair_chart(duration_chart, use_container_width=True)

        avg_duration = df['charge_duration'].mean()
        st.info(f"📌 平均充電時間：約 {avg_duration:.1f} 分鐘")


    # 📋 資料表（含備註、狀態、費率）
    with st.container():
        st.subheader("📋 交易資料表（含備註/狀態/費率）")
        display_df = df.copy()

        # 先檢查欄位存在再依序顯示
        base_cols = [
            "id", "cp_id", "transaction_id", "id_tag",
            "start_time", "stop_time", "meter_start", "meter_stop",
            "used_kwh"
        ]
        optional_cols = [col for col in ["remark", "status", "rate_type"] if col in display_df.columns]
        st.dataframe(display_df[base_cols + optional_cols])



    # 📤 匯出資料功能
    st.subheader("📤 匯出目前篩選結果")
    export_as = st.radio("匯出格式", ["CSV", "Excel"], horizontal=True)

    if export_as == "CSV":
        st.download_button(
            label="📥 下載 CSV",
            data=df.to_csv(index=False).encode('utf-8-sig'),
            file_name="filtered_data.csv",
            mime="text/csv"
        )
    else:
        import io
        from pandas import ExcelWriter
        output = io.BytesIO()
        with ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        st.download_button(
            label="📥 下載 Excel",
            data=output.getvalue(),
            file_name="filtered_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# 資料來源
st.caption("📊 資料來源：energy_ocpp.db → transactions 表")
