import customtkinter as ctk

class ThreeOptionDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="選択肢", message="どれを選びますか？", options=None):
        super().__init__(parent)

        self.title(title)
        self.geometry("400x250")
        self.result = None

        # モーダルにして親ウィンドウを無効化
        self.grab_set()

        # グリッドの設定
        self.columnconfigure(0, weight=2)  # 3列のグリッドを設定

        # メッセージラベル
        self.label = ctk.CTkLabel(self, text=message)
        self.label.grid(row=0, column=0, columnspan=3, padx=20, pady=10)

        # オプションリストが与えられていない場合のデフォルト設定
        if options is None:
            options = ["Option 1", "Option 2", "Option 3"]

        # オプションボタンの作成
        for idx, option in enumerate(options):
            col = (idx // 3)  # ボタンの行番号を計算（3列ごとに新しい行に）
            row = idx % 3 + 1  # ボタンの列番号を計算
            button = ctk.CTkButton(self, text=option, command=lambda opt=option: self.choose_option(opt))
            button.grid(row=row, column=col, padx=10, pady=10, sticky="nesw")


    def choose_option(self, option):
        """選択されたオプションを設定し、ダイアログを閉じる"""
        self.result = option
        self.close_dialog()

    def close_dialog(self):
        """ダイアログを閉じる処理"""
        if self.winfo_exists():
            self.grab_release()
            self.destroy()


def open_dialog(root):
    """ダイアログを開く処理"""
    options = ["はちみつ", "チョコソース", "ケチャップ＆マスタード", "ケチャップのみ", "マスタードのみ", "プレーン"]

    dialog = ThreeOptionDialog(root, message="どのソースを選びますか？", options=options)
    root.wait_window(dialog)  # ダイアログが閉じるまで待機
    
    return dialog.result


if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry("400x300")
    # ダイアログを開くボタン
    open_button = ctk.CTkButton(root, text="Open Dialog", command=lambda: open_dialog(root))
    open_button.pack(pady=100)

    root.mainloop()