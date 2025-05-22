import requests

# 設定你的後端 API base URL（請視情況調整為正式網址）
BACKEND_API_URL = "https://your-ocpp-backend.onrender.com"

def get_charge_point_groups():
    """
    從 OCPP 後端的 REST API 查詢分組充電樁清單
    """
    try:
        resp = requests.get(f"{BACKEND_API_URL}/api/charge-points", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ 查詢 /api/charge-points 失敗：{e}")
        return {
            "with_data": [],
            "registered_only": []
        }

def get_all_transactions():
    """
    從 OCPP 後端的 REST API 查詢所有交易紀錄
    """
    try:
        resp = requests.get(f"{BACKEND_API_URL}/api/transactions", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ 查詢 /api/transactions 失敗：{e}")
        return []
