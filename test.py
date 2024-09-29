import unittest
import sqlite3
from unittest.mock import patch
from main import DatabaseManager, HistoryManager  # モジュール名は適切に変更してください

class TestDatabaseManager(unittest.TestCase):

    def setUp(self):
        """テスト用にメモリ内データベースを使用"""
        self.db_manager = DatabaseManager(':memory:')  # メモリ内データベースを使用
        self.db_manager.create_table()
        self.db_manager.add_number(1, 'cooking')

    def test_add_number(self):
        """番号をデータベースに追加できているか"""
        result = self.db_manager.get_numbers_by_status('cooking')
        self.assertIn(1, result)

    def test_update_number_status(self):
        """番号のステータスを更新"""
        self.db_manager.update_number_status(1, 'providing')
        result = self.db_manager.get_numbers_by_status('providing')
        self.assertIn(1, result)

    def test_delete_number(self):
        """番号をデータベースから削除"""
        self.db_manager.delete_number(1)
        result = self.db_manager.get_numbers_by_status('cooking')
        self.assertNotIn(1, result)

    def test_get_numbers_by_status(self):
        """ステータスによる番号の取得"""
        self.db_manager.add_number(2, 'providing')
        cooking_numbers = self.db_manager.get_numbers_by_status('cooking')
        providing_numbers = self.db_manager.get_numbers_by_status('providing')
        self.assertIn(1, cooking_numbers)
        self.assertIn(2, providing_numbers)


class TestHistoryManager(unittest.TestCase):

    def setUp(self):
        """テスト用にメモリ内データベースを使用"""
        self.history_manager = HistoryManager(':memory:')  # メモリ内データベースを使用
        self.history_manager.create_table()
        self.history_manager.add_number_to_history(1)

    def test_add_number_to_history(self):
        """番号を履歴に追加できているか"""
        result = self.history_manager.get_used_numbers()
        self.assertIn(1, result)

    def test_get_used_numbers(self):
        """使用された番号をすべて取得"""
        self.history_manager.add_number_to_history(2)
        result = self.history_manager.get_used_numbers()
        self.assertIn(1, result)
        self.assertIn(2, result)

    def test_reset_history(self):
        """履歴をリセット"""
        self.history_manager.reset_history()
        result = self.history_manager.get_used_numbers()
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()
