"""
Auction Config Module - Đọc cấu hình đấu giá

Hỗ trợ 2 nguồn config (theo thứ tự ưu tiên):
1. Command Line Arguments (--item, --price, --duration, --desc)
2. Config File (auction_config.json)

Nếu không có cả 2 → Sử dụng giá trị mặc định
"""

import json
import os
import argparse


class AuctionConfig:
    """
    Class quản lý cấu hình đấu giá
    """
    
    # Giá trị mặc định
    DEFAULT_ITEM_NAME = "Sản phẩm bí mật"
    DEFAULT_STARTING_PRICE = 1000
    DEFAULT_DURATION = 120
    DEFAULT_DESCRIPTION = "Một món đồ đặc biệt đang chờ chủ nhân!"
    
    def __init__(self):
        """
        Khởi tạo với giá trị mặc định
        """
        self.item_name = self.DEFAULT_ITEM_NAME
        self.starting_price = self.DEFAULT_STARTING_PRICE
        self.auction_duration = self.DEFAULT_DURATION
        self.description = self.DEFAULT_DESCRIPTION
        self.config_source = "default"
    
    def load_from_file(self, config_path="auction_config.json"):
        """
        Đọc cấu hình từ JSON file
        
        Args:
            config_path: Đường dẫn đến file config (mặc định: auction_config.json)
        
        Returns:
            bool: True nếu đọc thành công, False nếu không
        """
        try:
            # Kiểm tra file tồn tại
            if not os.path.exists(config_path):
                print(f"[CONFIG] File {config_path} không tồn tại")
                return False
            
            # Đọc JSON
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse các trường
            self.item_name = data.get("item_name", self.DEFAULT_ITEM_NAME)
            self.starting_price = data.get("starting_price", self.DEFAULT_STARTING_PRICE)
            self.auction_duration = data.get("auction_duration", self.DEFAULT_DURATION)
            self.description = data.get("description", self.DEFAULT_DESCRIPTION)
            self.config_source = f"file:{config_path}"
            
            print(f"[CONFIG] ✅ Đã load config từ {config_path}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"[CONFIG] ❌ Lỗi parse JSON: {e}")
            return False
        except Exception as e:
            print(f"[CONFIG] ❌ Lỗi đọc file: {e}")
            return False
    
    def load_from_args(self, args=None):
        """
        Đọc cấu hình từ command line arguments
        
        Args:
            args: argparse.Namespace object (nếu None, sẽ parse từ sys.argv)
        
        Returns:
            argparse.Namespace: Parsed arguments
        """
        parser = argparse.ArgumentParser(
            description="🎯 Simple Auction Game Server",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main_server.py
  python main_server.py --item "PS5 Console" --price 5000
  python main_server.py --config custom_config.json
  python main_server.py --item "MacBook Pro M3" --price 20000 --duration 180
            """
        )
        
        parser.add_argument(
            '--config',
            type=str,
            default='auction_config.json',
            help='Đường dẫn đến file config JSON (mặc định: auction_config.json)'
        )
        
        parser.add_argument(
            '--item',
            type=str,
            help='Tên vật phẩm đấu giá (override config file)'
        )
        
        parser.add_argument(
            '--price',
            type=int,
            help='Giá khởi điểm (override config file)'
        )
        
        parser.add_argument(
            '--duration',
            type=int,
            help='Thời gian đấu giá (giây) (override config file)'
        )
        
        parser.add_argument(
            '--desc',
            type=str,
            help='Mô tả vật phẩm (override config file)'
        )
        
        # Parse arguments
        if args is None:
            args = parser.parse_args()
        
        # Bước 1: Load từ config file (nếu có)
        self.load_from_file(args.config)
        
        # Bước 2: Override bằng command line arguments (ưu tiên cao hơn)
        if args.item:
            self.item_name = args.item
            self.config_source = "command_line"
        
        if args.price:
            self.starting_price = args.price
            self.config_source = "command_line"
        
        if args.duration:
            self.auction_duration = args.duration
            self.config_source = "command_line"
        
        if args.desc:
            self.description = args.desc
            self.config_source = "command_line"
        
        return args
    
    def validate(self):
        """
        Kiểm tra tính hợp lệ của config
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        # Validate item name
        if not self.item_name or len(self.item_name.strip()) == 0:
            return False, "Tên vật phẩm không được để trống"
        
        # Validate starting price
        if self.starting_price <= 0:
            return False, "Giá khởi điểm phải lớn hơn 0"
        
        # Validate duration
        if self.auction_duration <= 0:
            return False, "Thời gian đấu giá phải lớn hơn 0"
        
        if self.auction_duration < 10:
            return False, "Thời gian đấu giá phải ít nhất 10 giây"
        
        return True, ""
    
    def print_config(self):
        """
        In ra cấu hình hiện tại (dùng để debug/confirm)
        """
        print("=" * 60)
        print("📋 CẤU HÌNH ĐẤU GIÁ")
        print("=" * 60)
        print(f"🎁 Vật phẩm      : {self.item_name}")
        print(f"💰 Giá khởi điểm : ${self.starting_price}")
        print(f"⏰ Thời gian     : {self.auction_duration} giây ({self.auction_duration // 60}:{self.auction_duration % 60:02d})")
        print(f"📝 Mô tả         : {self.description}")
        print(f"📌 Nguồn config  : {self.config_source}")
        print("=" * 60)
    
    def to_dict(self):
        """
        Chuyển config thành dictionary (để gửi qua JSON)
        
        Returns:
            dict: Config dưới dạng dictionary
        """
        return {
            "item_name": self.item_name,
            "starting_price": self.starting_price,
            "auction_duration": self.auction_duration,
            "description": self.description
        }


def load_auction_config():
    """
    Helper function để load config (sử dụng trong main_server.py)
    
    Returns:
        AuctionConfig: Config object đã được load
    """
    config = AuctionConfig()
    config.load_from_args()
    
    # Validate
    is_valid, error_msg = config.validate()
    if not is_valid:
        print(f"[CONFIG] ❌ Lỗi: {error_msg}")
        print("[CONFIG] Sử dụng giá trị mặc định")
    
    # Print config
    config.print_config()
    
    return config


if __name__ == "__main__":
    # Test config loader
    print("🧪 Testing Config Loader\n")
    
    config = load_auction_config()
    
    print("\n📊 Config as dict:")
    print(config.to_dict())
