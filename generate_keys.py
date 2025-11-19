import bcrypt
import getpass
import sys
import os

def hash_password_interactively():
    """
    ユーザーからの入力を受け付け、bcryptでハッシュ化して表示する関数。
    """
    print("-" * 40)
    print("🤖 bcrypt パスワードハッシュ生成ツール 🤖")
    print("-" * 40)
    
    # getpass.getpass() を使用して、入力時に文字が表示されないようにします (パスワード入力向け)
    # Windowsでは正常に動作しない場合があるため、その場合のフォールバックも考慮
    try:
        # パスワード入力時、ターミナルに文字が表示されない（セキュリティ強化）
        if os.name == 'nt': # Windowsの場合
            print("注意: Windows環境では入力時に文字が表示されません。")
            text_to_hash = getpass.getpass("ハッシュ化したい文字列を入力してください: ")
        else: # Windows以外の場合
            text_to_hash = getpass.getpass("ハッシュ化したい文字列を入力してください: ")
            
    except EOFError:
        # 入力がないまま終了した場合の処理
        print("\n入力が検出されませんでした。プログラムを終了します。")
        sys.exit()

    if not text_to_hash:
        print("警告: 空の文字列はハッシュ化できません。")
        sys.exit()

    try:
        # --- bcryptライブラリを使ってパスワードを安全に変換 ---
        
        # 1. パスワードをバイト形式に変換
        password_bytes = text_to_hash.encode('utf-8')

        # 2. ハッシュを生成 (bcrypt.gensalt()でランダムなソルトを自動生成)
        hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

        # 3. ハッシュを私たちが使える文字列形式に変換
        hashed_password_str = hashed_bytes.decode('utf-8')

        # --- 結果の表示 ---
        print("-" * 40)
        print("✅ ハッシュ化完了！ Secrets/config に貼り付けてください:")
        print(f"元の文字列: {text_to_hash}")
        print("----------------------------------------")
        print(hashed_password_str)
        print("----------------------------------------")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("bcryptの処理中に問題が発生しました。ライブラリが正しくインストールされているか確認してください。")

if __name__ == "__main__":
    hash_password_interactively()