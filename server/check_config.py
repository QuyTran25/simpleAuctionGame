"""
Script kiểm tra và validate config trước khi chạy server
Dùng để đảm bảo config được load đúng
"""

import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.dirname(__file__))

from auction_config import load_auction_config


def main():
    print("=" * 70)
    print("🔍 KIỂM TRA CONFIG - AUCTION GAME")
    print("=" * 70)
    print()
    
    # Load config
    print("📂 Đang load config...")
    config = load_auction_config()
    print()
    
    # Validate
    print("✅ KIỂM TRA VALIDATION")
    print("-" * 70)
    is_valid, error_msg = config.validate()
    
    if is_valid:
        print("✅ Config hợp lệ!")
    else:
        print(f"❌ Config không hợp lệ: {error_msg}")
        return False
    
    print()
    
    # Chi tiết config
    print("📋 CHI TIẾT CONFIG SẼ ĐƯỢC SỬ DỤNG:")
    print("-" * 70)
    print(f"  🎁 Vật phẩm       : {config.item_name}")
    print(f"  💰 Giá khởi điểm  : ${config.starting_price:,}")
    print(f"  ⏰ Thời gian      : {config.auction_duration}s ({config.auction_duration // 60}:{config.auction_duration % 60:02d})")
    print(f"  📝 Mô tả          : {config.description}")
    print(f"  📌 Nguồn          : {config.config_source}")
    print()
    
    # Xem trước UI
    print("🖼️  XEM TRƯỚC TRÊN UI:")
    print("-" * 70)
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🎁 ĐANG ĐẤU GIÁ                                           ║")
    print(f"║  {config.item_name:<58} ║")
    print(f"║  💵 Giá khởi điểm: ${config.starting_price:,}".ljust(62) + " ║")
    
    # Cắt mô tả nếu quá dài
    desc = config.description
    if len(desc) > 50:
        desc = desc[:47] + "..."
    print(f"║  📝 {desc:<56} ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # JSON output
    print("📤 JSON SẼ GỬI CHO CLIENT:")
    print("-" * 70)
    import json
    welcome_msg = {
        "type": "WELCOME",
        "message": "Chào mừng Player1!",
        "current_price": config.starting_price,
        "current_winner": "Chưa có",
        "item_name": config.item_name,
        "starting_price": config.starting_price,
        "description": config.description
    }
    print(json.dumps(welcome_msg, indent=2, ensure_ascii=False))
    print()
    
    print("=" * 70)
    print("✅ CONFIG ĐÃ SẴN SÀNG! Có thể chạy server:")
    print("   python main_server.py")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
