# -*- coding: utf-8 -*-
# ==============================================================================
# app.py (Airtable Version)
# 消耗品管理システムのStreamlitアプリケーションのメインファイルです。
# データベースとしてAirtableを使用するように改修されています。
# ==============================================================================

# --- 必要なライブラリのインポート ---
import streamlit as st
import database  # Airtable版のdatabase.pyをインポート
import pandas as pd
import qrcode
import io
import bcrypt
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import cv2
from urllib.parse import urlparse, parse_qs
import av

# --- ページ設定 ---
# ページのタイトルとレイアウトを最初に設定します。
st.set_page_config(page_title="研究室 消耗品管理システム", layout="wide")

# --- グローバルな設定 ---
# アプリのベースURL。QRコード生成時に使用します。
# Streamlit Cloudにデプロイした後のURLに書き換えてください。
APP_BASE_URL = "https://your-app-name.streamlit.app"


# ==============================================================================
# 認証とログイン状態の管理
# ==============================================================================

# --- 管理者パスワードをSecretsから安全に読み込む ---
# Streamlit CloudのSecrets機能を使うことで、パスワードをコード内に直接書かなくて済みます。
ADMIN_HASHED_PASSWORD = st.secrets.get("admin_password")
MASTER_PIN_HASH = st.secrets.get("master_pin_hash")

# --- セッション状態の初期化 ---
# st.session_stateは、ページのリロードをまたいで情報を記憶するための変数です。
# ログイン状態などをここに保存します。
if 'authentication_status' not in st.session_state:
    st.session_state.authentication_status = None
if 'name' not in st.session_state:
    st.session_state.name = None
if 'admin_unlocked' not in st.session_state:
    st.session_state.admin_unlocked = False

# --- 登録成功時のメッセージ表示 ---
# 新規登録直後に一度だけメッセージを表示するための仕組みです。
if st.session_state.get("just_registered"):
    st.toast('ユーザー登録が完了しました！')
    # メッセージを表示したら、記憶を消して次回は表示しないようにします。
    del st.session_state["just_registered"]


# ==============================================================================
# メインのアプリケーションロジック
# ==============================================================================

# --- ログイン後の画面 ---
if st.session_state["authentication_status"]:
    # ログインしたユーザーの名前をセッションから取得
    name = st.session_state["name"]

    # --- サイドバーの表示 ---
    st.sidebar.write(f'ようこそ、{name}さん！')
    if st.sidebar.button('ログアウト'):
        # ログアウトボタンが押されたら、セッション情報を全てクリアしてリロードします。
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.sidebar.divider()

    # --- 管理者メニューの表示 ---
    # まず、管理者メニューがロック解除されているか確認します。
    if st.session_state.admin_unlocked:
        # --- ▼▼▼ 管理者ページ ▼▼▼ ---
        st.title('管理者メニュー')

        # タブを使って各機能を切り替えられるようにします。
        tab1, tab2, tab3 = st.tabs(["在庫状況", "使用履歴", "QRコード生成"])

        with tab1:
            st.subheader('現在の在庫一覧')
            all_products_list = database.get_all_products()
            if all_products_list:
                # pandasのDataFrameを使って見やすい表形式で表示します。
                df_products = pd.DataFrame(all_products_list)
                # 表示に必要な列だけを選んで、列名を日本語にします。
                df_display = df_products[['ProductTag', 'ProductName', 'CurrentStock', 'Unit']]
                df_display.columns = ['商品タグ', '品目名', '現在庫数', '単位']
                st.dataframe(df_display, use_container_width=True)
            else:
                st.write('商品はまだ登録されていません。')

            st.divider()
            st.subheader('データベース本体')
            st.info("在庫数の手動更新（入荷、棚卸しなど）は、下のボタンからAirtableを開いて直接編集してください。")
            st.link_button("Airtableで在庫を直接編集する", f"https://airtable.com/{st.secrets.get('AIRTABLE_BASE_ID')}")


        with tab2:
            st.subheader('使用履歴')
            st.info("この機能は現在開発中です。")
            # TODO: 使用履歴機能の実装。QRCodesテーブルの情報を元に表示する必要があります。


        with tab3:
            st.subheader('QRコード生成')
            all_products_list = database.get_all_products()
            if all_products_list:
                # 商品名をプルダウンメニューで選択できるようにします。
                product_options = {p['ProductName']: p for p in all_products_list}
                selected_product_name = st.selectbox(
                    label="QRコードを生成する備品を選択",
                    options=list(product_options.keys()),
                    index=None,
                    placeholder="備品を選択してください..."
                )

                if selected_product_name:
                    selected_product = product_options[selected_product_name]
                    # 選択された商品のレコードIDとタグを取得
                    product_record_id = selected_product.get('id') # get_all_productsはidを返さないので注意
                    # get_product_by_tagでidを取得する必要がある
                    product_data_with_id = database.get_product_by_tag(selected_product['ProductTag'])
                    
                    if product_data_with_id:
                        product_record_id = product_data_with_id['id']

                        if st.button("新しいQRコードを1つ生成する", type="primary"):
                            # database.pyの関数を呼び出して、新しいユニークなQRコードIDを作成します。
                            new_qrcode_id = database.create_new_qrcode(product_record_id, selected_product['ProductTag'])
                            if new_qrcode_id:
                                # 生成されたユニークIDを含むURLを作成
                                url_to_encode = f"{APP_BASE_URL}?qrcode={new_qrcode_id}"

                                st.success(f"新しいQRコードを生成しました: {new_qrcode_id}")
                                st.write("生成されたURL:")
                                st.code(url_to_encode)

                                # URLを元にQRコード画像を生成して表示
                                qr_img = qrcode.make(url_to_encode)
                                buf = io.BytesIO()
                                qr_img.save(buf, format='PNG')
                                img_bytes = buf.getvalue()
                                st.image(img_bytes, caption=f"{selected_product_name} のQRコード", width=200)
                                st.info("この画像を右クリックして保存し、印刷して使用してください。")
                            else:
                                st.error("QRコードの生成に失敗しました。")
                    else:
                        st.error("商品のIDが取得できませんでした。")


    else:
        # --- ▼▼▼ 通常ユーザーページ ▼▼▼ ---
        # 管理者メニューがロックされている場合は、通常ユーザー向けの画面を表示します。

        # --- 管理者メニューへの入り口 ---
        st.sidebar.subheader("管理者用")
        admin_password_input = st.sidebar.text_input("管理者パスワードを入力", type="password", key="admin_pass")
        if st.sidebar.button("認証"):
            # 入力されたパスワードが、Secretsに保存されているハッシュ値と一致するかチェックします。
            if ADMIN_HASHED_PASSWORD and bcrypt.checkpw(admin_password_input.encode('utf-8'), ADMIN_HASHED_PASSWORD.encode('utf-8')):
                st.session_state.admin_unlocked = True
                st.rerun() # ページをリロードして管理者画面を表示
            else:
                st.sidebar.error("パスワードが違います。")

        # --- メインコンテンツ ---
        st.title('研究室　消耗品管理システム')
        st.header('使用登録')

        # --- QRコードスキャナー ---
        # streamlit-webrtcを使ってカメラ映像を表示し、QRコードをリアルタイムで検出します。
        # 検出したQRコードのデータはst.session_stateに保存されます。
        if 'scanned_code' not in st.session_state:
            st.session_state.scanned_code = None

        def qr_code_callback(frame: av.VideoFrame) -> av.VideoFrame:
            """カメラの各フレームで実行される関数"""
            img = frame.to_ndarray(format="bgr24")
            qr_detector = cv2.QRCodeDetector()
            data, _, _ = qr_detector.detectAndDecode(img)
            if data:
                try:
                    # 読み取ったデータ（URL）から 'qrcode' パラメータを抜き出します。
                    parsed_url = urlparse(data)
                    query_params = parse_qs(parsed_url.query)
                    if 'qrcode' in query_params:
                        # セッションにスキャン結果を保存
                        st.session_state.scanned_code = query_params['qrcode'][0]
                except Exception:
                    pass # URL形式でない場合は無視
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        webrtc_streamer(
            key="qr-scanner",
            mode=WebRtcMode.SENDONLY,
            video_frame_callback=qr_code_callback,
            media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False},
            async_processing=True,
        )

        st.markdown("---")

        # --- スキャン後の処理 ---
        # URLクエリパラメータか、カメラのスキャン結果を取得します。
        active_qrcode_id = st.session_state.get("scanned_code") or st.query_params.get("qrcode")

        if active_qrcode_id:
            # QRコードのデータをAirtableから取得
            qrcode_data = database.get_qrcode_data(active_qrcode_id)

            if not qrcode_data:
                st.error(f"QRコード '{active_qrcode_id}' がデータベースに見つかりません。")
            elif qrcode_data['fields'].get('Status') == '使用済み':
                st.error(f"このQRコード ({active_qrcode_id}) は既に使用されています。")
            else:
                # QRコードに紐づく商品情報を取得
                product_record_id = qrcode_data['fields'].get('Product', [None])[0]
                if product_record_id:
                    # TODO: get_product_by_record_id のような関数が database.py に必要
                    # 現状は全商品から探すことで代替
                    all_prods = database.get_all_products()
                    product = next((p for p in all_prods if p.get('id') == product_record_id), None)
                    product_data_with_id = database.get_product_by_tag(product['ProductTag'])
                    
                    if not product:
                        st.error("QRコードに紐づく商品が見つかりませんでした。")
                    else:
                        current_stock = int(product.get('CurrentStock', 0))

                        st.subheader(f"品目名: {product['ProductName']}")
                        st.metric(label="現在の在庫数", value=f"{current_stock} {product.get('Unit', '')}")

                        if current_stock > 0:
                            if st.button(f"「{product['ProductName']}」を1つ使用する", type="primary", use_container_width=True):
                                # 在庫を1つ減らす
                                database.update_stock(product_data_with_id['id'], -1)
                                # QRコードを「使用済み」にする
                                database.mark_qrcode_as_used(qrcode_data['id'])

                                # 処理が終わったら、スキャン状態をリセット
                                st.session_state.scanned_code = None
                                if "qrcode" in st.query_params:
                                    st.query_params.clear()
                                
                                st.success(f"「{product['ProductName']}」の使用を記録しました。")
                                st.balloons()
                                # 画面をリフレッシュして最新の状態を再表示
                                st.rerun()
                        else:
                            st.error(f"「{product['ProductName']}」の在庫がありません。")

        else:
            st.info("上のカメラでQRコードをスキャンしてください。")


# --- ログイン前の画面 ---
else:
    st.title('研究室　消耗品管理システム')
    # タブでログインと新規登録を切り替えます。
    login_tab, register_tab = st.tabs(["ログイン", "新規登録"])

    # --- ログインタブ ---
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("ユーザーネーム")
            password = st.text_input("パスワード", type="password")
            submitted = st.form_submit_button("ログイン")
            if submitted:
                # database.pyの関数を使ってユーザー情報を取得
                user = database.get_user(username)
                # パスワードがハッシュ値と一致するかチェック
                if user and bcrypt.checkpw(password.encode('utf-8'), user['HashedPassword'].encode('utf-8')):
                    # ログイン成功なら、セッションに状態を保存してリロード
                    st.session_state.authentication_status = True
                    st.session_state.name = user['Name']
                    st.rerun()
                else:
                    st.error("ユーザーネームまたはパスワードが間違っています。")

    # --- 新規登録タブ ---
    with register_tab:
        st.info('アカウントを登録してください。')
        with st.form("registration_form", clear_on_submit=True):
            name_reg = st.text_input("氏名")
            username_reg = st.text_input("ユーザーネーム (ログインID)", help="半角英数字で入力してください。")
            password_reg = st.text_input("パスワード", type="password")
            password_rep = st.text_input("パスワード（確認用）", type="password")
            pin_reg = st.text_input("共通ピンコード", type="password", max_chars=4)
            reg_submitted = st.form_submit_button("登録する")

            if reg_submitted:
                # 入力値のバリデーション（チェック）
                pin_ok = MASTER_PIN_HASH and bcrypt.checkpw(pin_reg.encode('utf-8'), MASTER_PIN_HASH.encode('utf-8'))

                if not pin_ok:
                    st.error("共通ピンコードが違います。")
                elif not (name_reg and username_reg and password_reg and password_rep):
                    st.warning("すべての項目を入力してください。")
                elif password_reg != password_rep:
                    st.error("パスワードが一致しません。")
                elif database.get_user(username_reg):
                    st.error("このユーザーネームは既に使用されています。")
                else:
                    # パスワードをハッシュ化
                    hashed_password = bcrypt.hashpw(password_reg.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    # データベースに新しいユーザーを追加
                    database.add_user(name_reg, username_reg, hashed_password)
                    # 登録成功のフラグを立ててリロード
                    st.session_state.just_registered = True
                    st.rerun()