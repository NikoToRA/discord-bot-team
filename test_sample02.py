#!/usr/bin/env python3
"""
sample02_roomlog.pyのテスト用スクリプト
リアルタイムルームログ機能をローカルでテストします
"""

import os
import json
import datetime
from sample02_roomlog import RoomLogger

def test_room_logger():
    """RoomLoggerクラスのテスト"""
    print("=== RoomLogger テスト開始 ===")
    
    # テスト用ルームID
    test_room_id = 1418511738046779393
    
    # RoomLoggerインスタンス作成
    logger = RoomLogger(test_room_id)
    print(f"✅ RoomLogger作成完了")
    print(f"   ログファイル: {logger.log_file}")
    print(f"   メタデータファイル: {logger.metadata_file}")
    
    # ファイル存在確認
    if os.path.exists(logger.log_file):
        print(f"✅ ログファイル存在確認済み")
    else:
        print(f"❌ ログファイルが存在しません")
        
    if os.path.exists(logger.metadata_file):
        print(f"✅ メタデータファイル存在確認済み")
    else:
        print(f"❌ メタデータファイルが存在しません")
    
    # ダミーメッセージクラス
    class DummyMessage:
        def __init__(self, content, author, message_id):
            self.content = content
            self.author = author
            self.id = message_id
            self.created_at = datetime.datetime.now()
            self.attachments = []
            self.reactions = []
    
    # テストメッセージ追加
    test_messages = [
        DummyMessage("テストメッセージ1", "TestUser#1234", 111111),
        DummyMessage("テストメッセージ2", "TestUser#5678", 222222),
        DummyMessage("絵文字テスト 🎉🚀", "TestUser#9999", 333333),
    ]
    
    print(f"\n--- テストメッセージ追加 ---")
    for msg in test_messages:
        logger.append_message(msg)
        print(f"✅ メッセージ追加: {msg.content}")
    
    # ログ情報取得テスト
    print(f"\n--- ログ情報取得テスト ---")
    log_info = logger.get_log_info()
    if log_info:
        print(f"✅ ログ情報取得成功")
        print(f"   メッセージ数: {log_info['message_count']}")
        print(f"   ファイルサイズ: {log_info['file_size_mb']:.3f}MB")
        print(f"   最終更新: {log_info['last_updated']}")
    else:
        print(f"❌ ログ情報取得失敗")
    
    # ログファイル内容確認
    print(f"\n--- ログファイル内容確認 ---")
    try:
        with open(logger.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"✅ ログファイル読み込み成功 ({len(lines)}行)")
            print(f"   最後の5行:")
            for line in lines[-5:]:
                print(f"     {line.rstrip()}")
    except Exception as e:
        print(f"❌ ログファイル読み込み失敗: {e}")
    
    # メタデータファイル内容確認
    print(f"\n--- メタデータファイル内容確認 ---")
    try:
        with open(logger.metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            print(f"✅ メタデータ読み込み成功")
            for key, value in metadata.items():
                print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ メタデータ読み込み失敗: {e}")
    
    print(f"\n=== テスト完了 ===")

def clean_test_files():
    """テスト用ファイルを削除"""
    test_room_id = 1418511738046779393
    log_dir = "/Users/suguruhirayama/Desktop/AI実験室/Discordbot"
    
    files_to_remove = [
        os.path.join(log_dir, f"room_{test_room_id}_log.txt"),
        os.path.join(log_dir, f"room_{test_room_id}_metadata.json")
    ]
    
    print("=== テストファイル削除 ===")
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ 削除: {file_path}")
        else:
            print(f"⚠️ ファイル不存在: {file_path}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'clean':
        clean_test_files()
    else:
        test_room_logger()
        
    print(f"\n💡 テストファイルを削除する場合:")
    print(f"   python test_sample02.py clean")