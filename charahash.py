import hashlib

def hash_string(input_text):
  """
  文字列をSHA-256でハッシュ化し、16進数文字列で返す関数
  """
  # 1. ハッシュオブジェクトを作成 (アルゴリズムを指定)
  sha256 = hashlib.sha256()
  
  # 2. 文字列をバイト型(utf-8)にエンコードしてハッシュ化
  #    ※ハッシュ関数はバイト列を処理するため、文字列(str)はエンコードが必要
  sha256.update(input_text.encode('utf-8'))
  
  # 3. ハッシュ値を16進数の文字列として取得
  return sha256.hexdigest()

# --- プログラムの実行 ---

# ユーザーからの入力を受け取る
text_to_hash = input("ハッシュ化したい文字列を入力してください: ")

# ハッシュ化を実行
hashed_value = hash_string(text_to_hash)

# 結果を表示
print(f"元の文字列: {text_to_hash}")
print(f"SHA-256ハッシュ値: {hashed_value}")

# (実行例)
# 入力: hello
# 出力: 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824