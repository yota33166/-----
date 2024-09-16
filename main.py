import customtkinter as ctk
import tkinter as tk
import sqlite3

class NumberDisplayApp:
    def __init__(self, master):
        self.master = master
        self.master.title("操作画面")

        self.max_number = 10
        self.is_auto = tk.BooleanVar(value=False)

        # データベース接続
        self.conn = sqlite3.connect('orders.db')
        self.create_table()

        # 現在選択中番号のラベル
        self.current_label = ctk.CTkLabel(self.master, text="選択中の番号: ", font=("Arial", 18))
        self.current_label.grid(row=0, column=0, columnspan=2, pady=10)

        # スクロール可能なフレームを作成し、番号リストを表示する
        self.scrollable_frame = ctk.CTkScrollableFrame(self.master, width=150, height=200)
        self.scrollable_frame.grid(row=1, column=0, rowspan=4, padx=10, pady=10)

        # 番号を選択するボタンをスクロール可能なフレームに作成
        self.number_buttons = []
        for i in range(1, self.max_number + 1):
            button = ctk.CTkButton(self.scrollable_frame, text=str(i), font=("Arial", 18), command=lambda num=i: self.select_number(num))
            button.pack(pady=5)
            self.number_buttons.append(button)

        # マウスホイールのスクロール速度をカスタマイズ
        self.scrollable_frame.bind("<MouseWheel>", self.on_mouse_wheel)

        # autoボタン
        self.auto_button = ctk.CTkSwitch(self.master, variable=self.is_auto, text="オートモード")
        self.auto_button.grid(row=1, column=1, padx=10, pady=10)

        # 調理中ボタン
        self.cooking_button = ctk.CTkButton(self.master, text="調理中にする", font=("Arial", 18), command=self.cooking_number)
        self.cooking_button.grid(row=2, column=1, padx=10, pady=10)

        # 提供可能にするためのボタン
        self.provide_button = ctk.CTkButton(self.master, text="提供可能にする", font=("Arial", 18), command=self.provide_number)
        self.provide_button.grid(row=3, column=1, padx=10, pady=10)

        # 提供完了した番号を削除するためのボタン
        self.complete_button = ctk.CTkButton(self.master, text="提供完了にする", font=("Arial", 18), command=self.complete_provide)
        self.complete_button.grid(row=4, column=1, padx=10, pady=10)

        # 表示モニターのウィンドウ (別ウィンドウ)
        self.display_window = ctk.CTkToplevel(self.master)
        self.display_window.title("表示モニター")

        # 調理中と提供可能の番号を表示する欄
        self.cooking_label = ctk.CTkLabel(self.display_window, text="調理中番号: ", font=("Arial", 24))
        self.cooking_label.pack(pady=20)

        self.provide_label = ctk.CTkLabel(self.display_window, text="提供可能番号: ", font=("Arial", 24))
        self.provide_label.pack(pady=20)

        self.selected_number = None  # 現在選択中の番号を保存
        self.update_display()

    def create_table(self):
        """データベーステーブルを作成"""
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                          id INTEGER PRIMARY KEY,
                          number INTEGER NOT NULL,
                          status TEXT NOT NULL)''')
        self.conn.commit()

    def add_number(self, number, status):
        """番号をデータベースに追加"""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO orders (number, status) VALUES (?, ?)", (number, status))
        self.conn.commit()

    def update_number_status(self, number, new_status):
        """番号のステータスを更新"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE orders SET status = ? WHERE number = ?", (new_status, number))
        self.conn.commit()

    def delete_number(self, number):
        """番号をデータベースから削除"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM orders WHERE number = ?", (number,))
        self.conn.commit()

    def get_numbers_by_status(self, status):
        """特定のステータスの番号を取得"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT number FROM orders WHERE status = ?", (status,))
        return [row[0] for row in cursor.fetchall()]

    def select_number(self, num):
        """番号を選択する"""
        self.selected_number = num
        self.update_display()

    def handle_auto_add(self):
        # 'cooking' および 'providing' ステータスの番号を取得
        using_numbers = self.get_numbers_by_status('cooking') + self.get_numbers_by_status('providing')
        
        # 1からself.max_numberまでの全ての番号の集合を作成
        available_numbers = set(range(1, self.max_number + 1))
        
        # 使用中の番号を集合から除外
        unused_numbers = available_numbers - set(using_numbers)
        
        if unused_numbers:
            # 未使用の番号の中で最小の番号を取得
            next_number = min(unused_numbers)
            # 次の番号を 'cooking' ステータスで追加
            self.add_number(next_number, 'cooking')
            self.update_display()
        else:
            # 使用可能な番号がない場合のエラーメッセージ
            print("無効な番号または既に呼び出し中です。")

    def handle_auto_transfer(self, from_status, to_status=None):
        """from_statusの番号をto_statusに移す"""
        from_numbers = self.get_numbers_by_status(from_status)
        if from_numbers:
            target_num = from_numbers[0]  # 最初の番号を取得
            if to_status:
                self.update_number_status(target_num, to_status)
            else:
                self.update_number_status(target_num, "served")
            self.update_display()

    def cooking_number(self):
        """選択した番号を調理中リストに追加"""
        if self.is_auto.get():
            self.handle_auto_add()
        elif self.selected_number is not None:
            if (1 <= self.selected_number <= self.max_number) and (self.selected_number not in self.get_numbers_by_status('cooking')):
                self.add_number(self.selected_number, 'cooking')
                self.update_display()
            else:
                print("無効な番号または既に呼び出し中です。")
        else:
            print("番号が選択されていません。")

    def provide_number(self):
        """選択した番号を提供可能リストに移動"""
        if self.is_auto.get():
            self.handle_auto_transfer('cooking', 'providing')
        elif self.selected_number is not None:
            if self.selected_number in self.get_numbers_by_status('cooking'):
                self.update_number_status(self.selected_number, 'providing')
                self.update_display()
            else:
                print("呼び出し中に存在しない番号です。")
        else:
            print("番号が選択されていません。")

    def complete_provide(self):
        """提供可能リストから番号を削除"""
        if self.is_auto.get():
            self.handle_auto_transfer('providing')
        elif self.selected_number is not None:
            if self.selected_number in self.get_numbers_by_status('providing'):
                self.update_number_status(self.selected_number, "served")
                self.update_display()
            else:
                print("提供可能リストに存在しない番号です。")
        else:
            print("番号が選択されていません。")

    def update_display(self):
        """呼び出し中と提供可能な番号を画面に更新"""
        cooking_numbers = self.get_numbers_by_status('cooking')
        provide_numbers = self.get_numbers_by_status('providing')
        self.current_label.configure(text=f"選択中の番号: {self.selected_number}", font=("Arial", 18))
        self.cooking_label.configure(text="調理中番号: " + ", ".join(map(str, cooking_numbers)))
        self.provide_label.configure(text="提供可能番号: " + ", ".join(map(str, provide_numbers)))

    def on_mouse_wheel(self, event):
        """スクロール速度をカスタマイズ"""
        self.scrollable_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / abs(event.delta)) * 100), "units")


# メインウィンドウの作成
if __name__ == "__main__":
    ctk.set_appearance_mode("Light")  # "Dark" や "Light" に設定可能
    ctk.set_default_color_theme("dark-blue")  # テーマのカラー設定

    root = ctk.CTk()  # customTkinterのTkウィンドウ
    app = NumberDisplayApp(root)
    root.mainloop()
