import os

# 対象のフォルダパス
#folder_path = 'C:\\Users\\Ohta2\\OneDrive\\デスクトップ\\工大祭2024\\レジアプリ\\sound'

# ナンバリングの開始値
start_number = 1

# フォルダ内のファイルを取得
files = os.listdir(folder_path)

# ファイルの拡張子を維持しつつ、ナンバリングでリネーム
for index, file_name in enumerate(files, start=start_number):
    # ファイルのフルパスを取得
    old_file_path = os.path.join(folder_path, file_name)
    
    # ディレクトリや隠しファイルはスキップ
    if os.path.isfile(old_file_path):
        # 拡張子を取得
        file_extension = os.path.splitext(file_name)[1]
        
        # 新しいファイル名 (例: 1.txt, 2.pngなど)
        new_file_name = f"metan{index+5}{file_extension}"
        new_file_path = os.path.join(folder_path, new_file_name)
        
        # ファイル名を変更
        os.rename(old_file_path, new_file_path)
        print(f"{old_file_path} を {new_file_path} に変更しました")
