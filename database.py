# ==============================================================================
# database.py (診断用パッチ適用済み)
# ==============================================================================
import streamlit as st
from pyairtable import Api
#from pyairtable.api.errors import Exception # <--- 新しくインポート
import os

# --- Airtableとの接続設定 ---
# Streamlit CloudのSecretsから情報を取得
API_KEY = st.secrets.get("AIRTABLE_API_KEY")
BASE_ID = st.secrets.get("AIRTABLE_BASE_ID")

# Secretsが設定されていない場合のフォールバック（ローカル開発用）
if not API_KEY or not BASE_ID:
    st.error("Airtableの接続情報がSecretsに設定されていません。")
    st.stop()

api = Api(API_KEY)
# 各テーブルへの接続
products_table = api.table(BASE_ID, "Products")
users_table = api.table(BASE_ID, "Users")
qrcodes_table = api.table(BASE_ID, "QRCodes")

# --- ユーザー管理用の関数 ---
def get_user(username):
    """ユーザー名でユーザー情報を取得する"""
    try:
        records = users_table.all(formula=f"{{Username}} = '{username}'")
        if records:
            return records[0]['fields']
        return None
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")
        return None
    '''
    except Exception as e: # 認証エラーなどのAPIエラーを補足
        st.error(f"APIエラー: {e}")
        return None
    '''
    

def add_user(name, username, hashed_password):
    """新しいユーザーを登録する"""
    try:
        users_table.create({
            "Name": name,
            "Username": username,
            "HashedPassword": hashed_password,
            "Role": "User"  # デフォルトは一般ユーザー
        })
    except Exception as e: # <--- ここで具体的なAPIエラーをキャッチ
        st.error("🚨 ユーザー登録がデータベースに拒否されました。以下の詳細を確認してください:")
        st.code(str(e)) # <--- 拒否された具体的な理由（どのフィールドがダメか）が表示されます。
        st.stop() # 処理を止めてエラーを確実に表示させる
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")

# --- (以下、get_all_products以降の関数は変更なし) ---
def get_all_products():
    """すべての商品情報を取得する"""
    try:
        all_records = products_table.all()
        # Airtableのレスポンス形式に合わせて'fields'キーからデータを抽出
        return [record['fields'] for record in all_records]
    except Exception as e:
        st.error(f"APIエラー: {e}")
        return []
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")
        return []

# （中略：以降の関数は省略しますが、上記のコードで全て上書きしてください）

def get_product_by_tag(product_tag):
    """ProductTagで商品情報を取得する"""
    try:
        records = products_table.all(formula=f"{{ProductTag}} = '{product_tag}'")
        if records:
            # IDも一緒に返すように変更
            return {'id': records[0]['id'], 'fields': records[0]['fields']}
        return None
    except Exception as e:
        st.error(f"APIエラー: {e}")
        return None
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")
        return None

def update_stock(record_id, quantity_change):
    """在庫数を更新する (record_idで指定)"""
    try:
        current_record = products_table.get(record_id)
        current_stock = current_record['fields'].get('CurrentStock', 0)
        new_stock = current_stock + quantity_change
        products_table.update(record_id, {"CurrentStock": new_stock})
    except Exception as e:
        st.error(f"APIエラー: {e}")
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")

# --- QRコード管理用の関数 (新規追加) ---
def get_qrcode_data(qrcode_id):
    """QRCodeIDでQRコードの情報を取得する"""
    try:
        records = qrcodes_table.all(formula=f"{{QRCodeID}} = '{qrcode_id}'")
        if records:
            # レコードIDとフィールドデータを両方返す
            return {'id': records[0]['id'], 'fields': records[0]['fields']}
        return None
    except Exception as e:
        st.error(f"APIエラー: {e}")
        return None
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")
        return None

def create_new_qrcode(product_record_id, product_tag):
    """新しいQRコードを作成し、DBに登録する"""
    try:
        # 該当商品の最新番号を取得して+1する
        product_record = products_table.get(product_record_id)
        latest_num = product_record['fields'].get('LatestQRCodeNum', 0)
        new_num = latest_num + 1
        
        # 新しいQRCodeIDを作成
        new_qrcode_id = f"{product_tag}_{new_num}"
        
        # QRCodesテーブルに新しいレコードを追加
        qrcodes_table.create({
            "QRCodeID": new_qrcode_id,
            "Product": [product_record_id],  # 連携レコードはリストでIDを指定
            "Status": "未使用"
        })
        
        # Productsテーブルの最新番号を更新
        products_table.update(product_record_id, {"LatestQRCodeNum": new_num})
        
        return new_qrcode_id
    except Exception as e:
        st.error(f"APIエラー: {e}")
        return None
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")
        return None

def mark_qrcode_as_used(qrcode_record_id):
    """QRコードの状態を「使用済み」に更新する"""
    try:
        qrcodes_table.update(qrcode_record_id, {"Status": "使用済み"})
    except Exception as e:
        st.error(f"APIエラー: {e}")
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")