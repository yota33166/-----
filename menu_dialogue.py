import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

class ThreeOptionDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="選択肢", message="どれを選びますか？", options=None):
        super().__init__(parent)

        self.title(title)

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
            button = ctk.CTkButton(self, text=option, command=lambda opt=option: self.add_to_order(opt))
            button.grid(row=row, column=col, padx=10, pady=10, sticky="nesw")
        
        self.confirm_button = ctk.CTkButton(self, fg_color="green", text="決定", command=self.confirm_order)
        self.confirm_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        # 注文内容のツリービュー
        self.tree = ttk.Treeview(self, columns=('topping', 'order_count'), show='headings')
        
        self.tree.heading('topping', text='トッピング')
        self.tree.heading('order_count', text='注文数')

        # 各列の幅を設定
        self.tree.column('order_count', width=100, anchor=tk.CENTER, stretch=False)

        self.tree.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.order_dict = {}

    def add_to_order(self, option):
        """選択されたオプションを注文に追加し、ツリービューを更新"""
        if option in self.order_dict:
            self.order_dict[option] += 1
        else:
            self.order_dict[option] = 1

        # ツリービューの更新
        self.update_tree()

    def update_tree(self):
        """ツリービューを注文の内容で更新"""
        # 既存のアイテムをクリア
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 新しい注文内容を表示
        for topping, count in self.order_dict.items():
            self.tree.insert('', 'end', values=(topping, count))

    def confirm_order(self):
        """全ての注文を返し、ダイアログを閉じる"""
        self.result = [(topping, count) for topping, count in self.order_dict.items()]
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
    open_button.grid(row=0, column=0)

    root.mainloop()