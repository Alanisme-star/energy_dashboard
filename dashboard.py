import streamlit as st
import pandas as pd
import requests

API_BASE_URL = "https://energy-ocpp.onrender.com"

st.set_page_config(page_title="能源用電視覺分析 Dashboard")
st.title("⚡ 能源用電視覺分析 Dashboard")
st.caption("分析充電樁交易、耗電量、分時行為與趨勢")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    with st.form("login_form"):
        username = st.text_input("帳號")
        password = st.text_input("密碼", type="password")
        submit = st.form_submit_button("登入")
        if submit:
            if username == "admin" and password == "1234":
                st.session_state.logged_in = True
            else:
                st.error("登入失敗，請確認帳號密碼")

if not st.session_state.logged_in:
    login()
    st.stop()

if st.button("📕 登出"):
    st.session_state.logged_in = False
    st.rerun()

def get_charge_points():
    try:
        res = requests.get(f"{API_BASE_URL}/api/charge_points")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.warning(f"無法取得充電樁列表：{e}")
    return []

def fetch_transaction_data():
    try:
        res = requests.get(f"{API_BASE_URL}/api/transactions")
        if res.status_code == 200:
            return pd.DataFrame(res.json())
    except Exception as e:
        st.error(f"無法取得交易資料：{e}")
    return pd.DataFrame()

# 資料抓取
cp_info_list = get_charge_points()
df = fetch_transaction_data()

# 交易過的 cp_id 集合
cp_ids_with_data = set(df["cp_id"].unique()) if not df.empty else set()

# 依照是否有交易紀錄分類
with_data, without_data = [], []
for cp in cp_info_list:
    display = f"{cp['id']} ✅" if cp["status"] == "online" else f"{cp['id']} ❌"
    if cp["id"] in cp_ids_with_data:
        with_data.append((display, cp["id"]))
    else:
        without_data.append((display, cp["id"]))

# 建構下拉選單項目
dropdown_options = ["全部"]
dropdown_options += ["─── 📊 有交易紀錄 ───"] + [d[0] for d in with_data]
dropdown_options += ["─── 💤 僅註冊未交易 ───"] + [d[0] for d in without_data]

selected_display = st.selectbox("選擇充電樁", options=dropdown_options)

# 對應 ID
selected_cp = None
for label, cp_id in with_data + without_data:
    if selected_display == label:
        selected_cp = cp_id
        break

# 無交易則直接提示
if df.empty or "meter_start" not in df.columns or "meter_stop" not in df.columns:
    st.warning("目前沒有完整的交易資料（含 meter_start 和 meter_stop）")
    st.markdown("📊 資料來源：後端 OCPP REST API")
    st.stop()

# 篩選指定充電樁
if selected_cp:
    df = df[df["cp_id"] == selected_cp]

# 計算每筆交易用電量
df["used_kwh"] = (df["meter_stop"] - df["meter_start"]) / 1000

# 分析視覺化
st.subheader("📈 每日用電量趨勢")
df["start_time"] = pd.to_datetime(df["start_time"])
kwh_by_date = df.groupby(df["start_time"].dt.date)["used_kwh"].sum()
st.line_chart(kwh_by_date)

st.subheader("⚡ 各樁使用次數")
usage_counts = df["cp_id"].value_counts()
st.bar_chart(usage_counts)

st.markdown("📊 資料來源：後端 OCPP REST API")
