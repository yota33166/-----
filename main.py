import customtkinter as ctk
import tkinter as tk
import sqlite3
import play_sound
import pygame

class DatabaseManager:
    def __init__(self, db_name='orders.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        """データベーステーブルを作成"""
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                            id INTEGER PRIMARY KEY,
                            number INTEGER NOT NULL,
                            status TEXT NOT NULL,
                            accepted_at TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP, '+9 hours'))
                        )''')
        self.conn.commit()

    def add_number(self, number, status):
        """番号をデータベースに追加"""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO orders (number, status) VALUES (?, ?)", (number, status))
        self.conn.commit()

    def update_number_status(self, number, new_status):
        """番号のステータスを更新"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE orders SET status = ? WHERE number = ? AND status != 'served'", (new_status, number))
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


class HistoryManager:
    def __init__(self, db_name='history.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        """履歴テーブルを作成"""
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                            id INTEGER PRIMARY KEY,
                            number INTEGER NOT NULL,
                            used_at TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP, '+9 hours'))
                        )''')
        self.conn.commit()

    def add_number_to_history(self, number):
        """整理番号を履歴に追加"""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO history (number) VALUES (?)", (number,))
        self.conn.commit()

    def get_used_numbers(self):
        """使用された番号をすべて取得"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT number FROM history")
        return [row[0] for row in cursor.fetchall()]

    def reset_history(self):
        """履歴をリセット"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM history")
        self.conn.commit()


class NumberDisplayApp:
    def __init__(self, master):
        self.master = master
        self.master.title("操作画面")

        # グリッドレイアウトの設定
        self.configure_grid()

        self.max_number = 10
        self.is_auto = tk.BooleanVar(value=False)

        # データベースの初期化
        self.db_manager = DatabaseManager()

        # 整理番号の履歴管理DB
        self.history_manager = HistoryManager()

        # UIコンポーネントの作成
        self.create_widgets()

        # デフォルトの値
        self.selected_number = None  # 現在選択されている番号
        self.used_numbers = []  # 使用済みの番号を追跡

        # 番号表示用のウィンドウを作成
        self.is_hide_bar = False
        self.create_display_window()

        # ディスプレイを更新
        self.update_display()

    def configure_grid(self):
        """メインウィンドウのグリッドレイアウトを設定"""
        for i in range(5):
            self.master.grid_rowconfigure(i, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=2)

    def create_widgets(self):
        """必要なUIコンポーネントをすべて作成"""
        self.default_font = ("Arial", 28)

        # 現在選択されている番号の表示ラベル
        self.current_label = ctk.CTkLabel(self.master, text="選択中の番号: ", font=("Arial", 48))
        self.current_label.grid(row=0, column=0, columnspan=2, pady=10, sticky="nsew")

        # 番号ボタン用のスクロール可能なフレーム
        self.create_scrollable_frame()

        # オートモード用スイッチボタン
        self.auto_button = ctk.CTkSwitch(self.master, variable=self.is_auto, text="オートモード")
        self.auto_button.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # アクションボタンの作成
        self.create_action_buttons()

    def create_scrollable_frame(self):
        """番号ボタンを表示するためのスクロール可能なフレームを作成"""
        self.scrollable_frame = ctk.CTkScrollableFrame(self.master, width=150, height=200)
        self.scrollable_frame.grid(row=1, column=0, rowspan=4, padx=10, pady=10, sticky="nsew")

        self.number_buttons = []
        for i in range(1, self.max_number + 1):
            button = ctk.CTkButton(self.scrollable_frame, text=str(i), font=("Arial", 18),
                                   command=lambda num=i: self.select_number(num))
            button.pack(pady=5, fill='both', expand=True)
            self.number_buttons.append(button)

        # スクロール速度のカスタマイズ
        self.scrollable_frame.bind("<MouseWheel>", self.on_mouse_wheel)

    def create_action_buttons(self):
        """調理中、提供可能、提供完了用のアクションボタンを作成"""
        self.cooking_button = ctk.CTkButton(self.master, text="調理中にする", font=self.default_font,
                                            command=self.cooking_number)
        self.cooking_button.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        self.provide_button = ctk.CTkButton(self.master, text="提供可能にする", font=self.default_font,
                                            command=self.provide_number)
        self.provide_button.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        self.complete_button = ctk.CTkButton(self.master, text="提供完了にする", font=self.default_font,
                                             command=self.complete_provide)
        self.complete_button.grid(row=4, column=1, padx=10, pady=10, sticky="nsew")

    def create_display_window(self):
        """調理中や提供可能番号を表示するためのサブウィンドウを作成"""
        self.display_window = ctk.CTkToplevel(self.master)
        # タイトルバーを非表示にする
        self.display_window.overrideredirect(self.is_hide_bar)
        # F11キーでバー表示モードを切り替える
        self.display_window.bind("<F11>", self.toggle_hide_bar)

        cooking_text_label = ctk.CTkLabel(self.display_window, text="調理中", font=("Arial", 24, "bold"))
        cooking_text_label.grid(row=0, column=0, padx=20, pady=20)

        provide_text_label = ctk.CTkLabel(self.display_window, text="できあがり", font=("Arial", 24, "bold"))
        provide_text_label.grid(row=0, column=1, padx=20, pady=20)

        self.cooking_label = ctk.CTkLabel(self.display_window, text="", font=("Arial", 24, "bold"))
        self.cooking_label.grid(row=1, column=0, padx=20, pady=20)

        self.provide_label = ctk.CTkLabel(self.display_window, text="", font=("Arial", 24, "bold"))
        self.provide_label.grid(row=1, column=1, padx=20, pady=20)

    def toggle_hide_bar(self, event=None):
        """Hキーでタブのバーを消す"""
        self.is_hide_bar = not self.is_hide_bar
        # タイトルバーを非表示にする
        self.display_window.overrideredirect(self.is_hide_bar)
        self.display_window.update_idletasks()

    def select_number(self, num):
        """番号を選択"""
        self.selected_number = num
        self.update_display()

    def handle_auto_add(self):
        """次に利用可能な番号を自動的に追加"""
        using_numbers = self.db_manager.get_numbers_by_status('cooking') + self.db_manager.get_numbers_by_status('providing')
        used_numbers = self.history_manager.get_used_numbers()
        available_numbers = set(range(1, self.max_number + 1)) - set(using_numbers) - set(used_numbers)

        if available_numbers:
            next_number = min(available_numbers)
            self.db_manager.add_number(next_number, 'cooking')
            self.history_manager.add_number_to_history(next_number)
            # 全ての番号を使用したら1番に戻ってくる
            if len(used_numbers) >= self.max_number - 1:
                self.history_manager.reset_history()  # 履歴をリセット
                print("整理番号がリセットされました。")
            self.update_display()
        else:
            print("無効な番号または既に呼び出し中です。")



    def handle_auto_transfer(self, from_status, to_status=None):
        """番号を自動的にあるステータスから別のステータスへ移動"""
        from_numbers = self.db_manager.get_numbers_by_status(from_status)
        if from_numbers:
            target_num = from_numbers[0]
            if to_status:
                self.db_manager.update_number_status(target_num, to_status)
                play_sound.play_sound_thread(target_num)
            else:
                self.db_manager.update_number_status(target_num, "served")
            self.update_display()

    def cooking_number(self):
        """選択された番号を「調理中」に設定"""
        if self.is_auto.get():
            self.handle_auto_add()
        elif self.selected_number and self.selected_number not in self.db_manager.get_numbers_by_status('cooking'):
            self.db_manager.add_number(self.selected_number, 'cooking')
            self.selected_number = None
            self.update_display()
        else:
            print("無効な番号または既に呼び出し中です。")

    def provide_number(self):
        """選択された番号を「提供可能」に設定"""
        if self.is_auto.get():
            self.handle_auto_transfer('cooking', 'providing')
        elif self.selected_number in self.db_manager.get_numbers_by_status('cooking'):
            self.db_manager.update_number_status(self.selected_number, 'providing')
            play_sound.play_sound_thread(self.selected_number)
            self.selected_number = None
            self.update_display()
        else:
            print("呼び出し中に存在しない番号です。")

    def complete_provide(self):
        """提供可能な番号を「提供完了」に設定"""
        if self.is_auto.get():
            self.handle_auto_transfer('providing')
        elif self.selected_number in self.db_manager.get_numbers_by_status('providing'):
            self.db_manager.update_number_status(self.selected_number, "served")
            self.selected_number = None
            self.update_display()
        else:
            print("提供可能リストに存在しない番号です。")

    def format_display_numbers(self, numbers, n=3):
        """数字の要素数nごとに改行する"""
        numbers = [f"{num:>3}" if num < 10 else str(num) for num in numbers]
        return "\n".join(["　".join(map(str, numbers[i:i + n])) for i in range(0, len(numbers), n)])
    
    def update_display(self):
        """調理中と提供可能な番号を画面に更新"""
        cooking_numbers = self.db_manager.get_numbers_by_status('cooking')
        providing_numbers = self.db_manager.get_numbers_by_status('providing')

        self.current_label.configure(text=f"選択中の番号: {self.selected_number}", font=self.default_font)
        self.cooking_label.configure(text=self.format_display_numbers(cooking_numbers))
        self.provide_label.configure(text=self.format_display_numbers(providing_numbers))

    def on_mouse_wheel(self, event):
        """スクロール可能フレームのスクロール速度をカスタマイズ"""
        self.scrollable_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / abs(event.delta)) * 100), "units")


# メインウィンドウの作成
if __name__ == "__main__":
    ctk.set_appearance_mode("Light")  # "Dark" または "Light" モードを設定
    ctk.set_default_color_theme("dark-blue")  # カラーテーマを設定
    
    root = ctk.CTk()  # customTkinter のメインウィンドウ
    app = NumberDisplayApp(root)
    root.mainloop()
    pygame.mixer.quit()
