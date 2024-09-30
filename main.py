import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import sqlite3
import play_sound
import pygame
from menu_dialogue import open_dialog

class DatabaseManager:
    def __init__(self, db_name='orders.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        """データベーステーブルを作成。デフォルトでJSTで保存する"""
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                            id INTEGER PRIMARY KEY,
                            number INTEGER NOT NULL,
                            topping TEXT NOT NULL,
                            status TEXT NOT NULL,
                            accepted_at TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP, '+9 hours')),
                            updated_at TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP, '+9 hours'))
                        )''')
        self.conn.commit()

    def add_number(self, number, topping, status):
        """番号をデータベースに追加"""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO orders (number, topping, status) VALUES (?, ?, ?)", (number, topping, status))
        self.conn.commit()

    def update_number_status(self, number, new_status):
        """番号のステータスを更新"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE orders 
            SET status = ?, updated_at = (datetime(CURRENT_TIMESTAMP, '+9 hours'))
            WHERE number = ? AND status != 'served'
        ''', (new_status, number))
        self.conn.commit()

    def update_number_status_by_id(self, number_id, new_status):
        """IDでステータスを更新"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE orders 
            SET status = ?, updated_at = (datetime(CURRENT_TIMESTAMP, '+9 hours'))
            WHERE id = ?
        ''', (new_status, number_id))
        self.conn.commit()

    def delete_number(self, number):
        """番号をデータベースから削除"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM orders WHERE number = ?", (number,))
        self.conn.commit()

    def delete_number_by_id(self, number_id):
        """IDで番号を削除"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id = ?", (number_id,))
        self.conn.commit()

    def get_numbers_by_status(self, status):
        """特定のステータスの番号を取得"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT number FROM orders WHERE status = ?", (status,))
        return [row[0] for row in cursor.fetchall()]

    def get_id_by_number(self, number):
        """整理番号のIDを取得"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM orders WHERE number = ? ORDER BY updated_at DESC LIMIT 1", (number,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def get_all_orders(self):
        """全ての注文を取得"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT number, topping, status FROM orders ORDER BY accepted_at ASC")
        return cursor.fetchall()
    
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

        self.default_font = ("Arial", 28)

        # グリッドレイアウトの設定
        self.configure_grid()

        self.max_number = 30
        self.is_auto = tk.BooleanVar(value=False)

        # データベースの初期化
        self.db_manager = DatabaseManager()

        # 整理番号の履歴管理DB
        self.history_manager = HistoryManager()

        # 操作履歴のためのスタック（やり直し用）
        self.action_history = []

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
        self.master.grid_rowconfigure((6,7), weight=3)
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=2)

    def create_widgets(self):
        """必要なUIコンポーネントをすべて作成"""

        # 現在選択されている番号の表示ラベル
        self.current_label = ctk.CTkLabel(self.master, text="選択中の番号: ", font=("Arial", 48))
        self.current_label.grid(row=0, column=0, columnspan=2, pady=10, sticky="nsew")

        # 番号ボタン用のスクロール可能なフレーム
        self.create_scrollable_frame()

        # オートモード用スイッチボタン
        self.auto_button = ctk.CTkSwitch(self.master, variable=self.is_auto, text="オートモード")
        self.auto_button.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # アクションボタンの作成(row=2～5)
        self.create_action_buttons()

        # Treeviewのスタイルを設定
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 18), rowheight=30)  # 文字サイズ16のArialフォント
        style.configure("Treeview.Heading", font=("Arial", 16, "bold"))  # ヘッダーのフォント設定

        # Treeviewウィジェットを作成    
        self.tree = ttk.Treeview(self.master, columns=('number', 'status', 'topping'), show='headings')
        self.tree.heading('number', text='番号')
        self.tree.heading('status', text='ステータス')
        self.tree.heading('topping', text='トッピング')

        # 各列の幅を設定
        self.tree.column('number', width=60, anchor=tk.CENTER, stretch=False)
        self.tree.column('status', width=120, anchor=tk.CENTER, stretch=False)

        #提供中のタグを付けた行を緑にする
        self.tree.tag_configure('providing', background='lightgreen')

        self.tree.grid(row=6, column=0, rowspan=2, columnspan=2, padx=10, pady=10, sticky="nsew")

    def create_scrollable_frame(self):
        """番号ボタンを表示するためのスクロール可能なフレームを作成"""
        self.scrollable_frame = ctk.CTkScrollableFrame(self.master, width=150, height=200)
        self.scrollable_frame.grid(row=1, column=0, rowspan=5, padx=10, pady=10, sticky="nsew")

        self.number_buttons = []
        for i in range(1, self.max_number + 1):
            button = ctk.CTkButton(self.scrollable_frame, text=str(i), font=("Arial", 18),
                                   command=lambda num=i: self.select_number(num))
            button.pack(pady=5, fill='both', expand=True)
            self.number_buttons.append(button)

        # スクロール速度のカスタマイズ
        self.scrollable_frame.bind("<MouseWheel>", self.on_mouse_wheel)

    def create_action_buttons(self):
        """調理中、提供可能、提供完了用等のアクションボタンを作成"""
        self.cooking_button = ctk.CTkButton(self.master, text="調理中にする", font=self.default_font,
                                            command=self.cooking_number)
        self.cooking_button.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        self.provide_button = ctk.CTkButton(self.master, text="提供可能にする", font=self.default_font,
                                            command=self.provide_number)
        self.provide_button.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        self.complete_button = ctk.CTkButton(self.master, text="提供完了にする", font=self.default_font,
                                             command=self.complete_provide)
        self.complete_button.grid(row=4, column=1, padx=10, pady=10, sticky="nsew")

        self.undo_button = ctk.CTkButton(self.master, text="1つ戻す", fg_color="gray", font=self.default_font, command=self.undo_action)
        self.undo_button.grid(row=5, column=1, padx=30, pady=20, sticky="nsew")

    def create_display_window(self):
        """調理中や提供可能番号を表示するためのサブウィンドウを作成"""
        self.display_window = ctk.CTkToplevel(self.master)
        # タイトルバーを非表示にする
        self.display_window.overrideredirect(self.is_hide_bar)
        # F11キーでバー表示モードを切り替える
        self.display_window.bind("<F11>", self.toggle_hide_bar)

        cooking_text_label = ctk.CTkLabel(self.display_window, text="　　-調理中-　　", font=("Arial", 24, "bold"))
        cooking_text_label.grid(row=0, column=0, padx=20, pady=20)

        provide_text_label = ctk.CTkLabel(self.display_window, text_color="darkgreen", text="　-できあがり-　", font=("Arial", 24, "bold"))
        provide_text_label.grid(row=0, column=1, padx=20, pady=20)

        self.cooking_label = ctk.CTkLabel(self.display_window, text="", font=("Arial", 30, "bold"))
        self.cooking_label.grid(row=1, column=0, padx=20, pady=20)

        self.provide_label = ctk.CTkLabel(self.display_window, text_color="darkgreen", text="", font=("Arial", 30, "bold"))
        self.provide_label.grid(row=1, column=1, padx=20, pady=20)

    def toggle_hide_bar(self, event=None):
        """タブのバーを消す"""
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
            topping = open_dialog(self.master)
            if topping is None:
                self.show_info("トッピングを選択してください")
                return

            target_num = min(available_numbers)
            old_status = "none"
            self.db_manager.add_number(target_num, topping, 'cooking')
            self.add_to_action_history(target_num, old_status, 'cooking') #履歴に追加
            self.history_manager.add_number_to_history(target_num)
            # 全ての番号を使用したら1番に戻ってくる
            if len(used_numbers) >= self.max_number - 1:
                self.history_manager.reset_history()  # 履歴をリセット
                print("整理番号が1番に戻ってきました。")
            self.update_display()
        else:
            self.show_info("無効な番号または既に呼び出し中です。")


    def handle_auto_transfer(self, current_status, next_status):
        """番号を自動的にあるステータスから別のステータスへ移動"""
        current_status_num = self.db_manager.get_numbers_by_status(current_status)

        if current_status_num:
            target_num = current_status_num[0] #特定ステータスの先頭の数字を取得
            self.db_manager.update_number_status(target_num, next_status)
            old_status = current_status
            self.add_to_action_history(target_num, old_status, next_status)  # 履歴に追加
            if next_status == 'providing':                
                play_sound.play_sound_thread(target_num)

            self.update_display()

    def cooking_number(self):
        """選択された番号を「調理中」に設定"""

        if self.is_auto.get():
            self.handle_auto_add()
            return
        
        if self.selected_number and self.selected_number not in self.db_manager.get_numbers_by_status('cooking'):
            topping = open_dialog(self.master)
            if topping is None:
                self.show_info("トッピングを選択してください")
                return
            old_status = 'none'
            self.db_manager.add_number(self.selected_number, topping, 'cooking')
            self.add_to_action_history(self.selected_number, old_status, 'cooking') #履歴に追加
            self.selected_number = None
            self.update_display()
        else:
            self.show_info("無効な番号または既に呼び出し中です。")

    def provide_number(self):
        """選択された番号を「提供可能」に設定"""
        if self.is_auto.get():
            self.handle_auto_transfer('cooking', 'providing')
            return
        
        if self.selected_number in self.db_manager.get_numbers_by_status('cooking'):
            old_status = 'cooking'
            self.db_manager.update_number_status(self.selected_number, 'providing')
            self.add_to_action_history(self.selected_number, old_status, 'providing')  # 履歴に追加
            play_sound.play_sound_thread(self.selected_number)
            self.selected_number = None
            self.update_display()
        else:
            self.show_info("呼び出し中に存在しない番号です。")

    def complete_provide(self):
        """提供可能な番号を「提供完了」に設定"""
        if self.is_auto.get():
            self.handle_auto_transfer('providing', 'served')
        elif self.selected_number in self.db_manager.get_numbers_by_status('providing'):
            old_status = 'providing'
            self.db_manager.update_number_status(self.selected_number, "served")
            self.add_to_action_history(self.selected_number, old_status, 'served')  # 履歴に追加
            self.selected_number = None
            self.update_display()
        else:
            self.show_info("提供可能リストに存在しない番号です。")

    def undo_action(self):
        """最後の操作をやり直す"""
        if not self.action_history:
            self.show_info("やり直し可能な操作がありません。")
            return

        # 最後の操作を取得して、戻す
        last_action = self.action_history.pop()
        number, number_id, old_status, new_status = last_action

        if old_status == 'none':
            # 番号を削除する
            self.db_manager.delete_number_by_id(number_id)
        else:
            # 番号を元の状態に戻す
            self.db_manager.update_number_status_by_id(number_id, old_status)
        
        status_mapping = {
        "none": "未注文",
        "cooking": "調理中",
        "providing": "呼出中",
        "served": "提供済み",
        }

        # ディスプレイを更新
        self.update_display()
        self.show_info(f"番号 {number} を「{status_mapping[new_status]}」から「{status_mapping[old_status]}」に戻しました。")

    def add_to_action_history(self, number, old_status, new_status):
        """操作履歴に追加"""
        number_id = self.db_manager.get_id_by_number(number)
        self.action_history.append((number, number_id, old_status, new_status))

    def format_display_numbers(self, numbers, n=5):
        """数字の要素数nごとに改行する"""
        numbers = [f"{num:>3}" if num < 10 else str(num) for num in numbers]
        return "\n".join(["　".join(map(str, numbers[i:i + n])) for i in range(0, len(numbers), n)])
    
    def update_display(self):
        """調理中と提供可能な番号を画面に更新, ついでにコントロールパネルの注文リストも更新"""
        cooking_numbers = self.db_manager.get_numbers_by_status('cooking')
        providing_numbers = self.db_manager.get_numbers_by_status('providing')

        self.current_label.configure(text=f"選択中の番号: {self.selected_number}", font=self.default_font)
        self.cooking_label.configure(text=self.format_display_numbers(cooking_numbers))
        self.provide_label.configure(text=self.format_display_numbers(providing_numbers))

        # Listboxの更新
        for row in self.tree.get_children():
            self.tree.delete(row)

        status_mapping = {
        "cooking": "調理中",
        "providing": "呼出中"
        }

        orders = self.db_manager.get_all_orders()
        for idx, order in enumerate(orders):
            status = status_mapping.get(order[2])
            if not status:
                continue
            
            self.tree.insert('', 'end', values=(order[0], status, order[1]))

            # ステータスに応じて背景色を変更
            if status == "呼出中":
                self.tree.item(self.tree.get_children()[-1], tags=('providing',))

    def show_info(self, text):
        self.current_label.configure(text=text)

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
