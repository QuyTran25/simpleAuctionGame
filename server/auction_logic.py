"""
Auction Logic Module - Quản lý trạng thái đấu giá

Nhiệm vụ chính:
1. Duy trì giá cao nhất (current_price) và người thắng cuộc (current_winner)
2. Áp dụng Lock/Mutex để bảo vệ biến trạng thái khi nhiều threads truy cập đồng thời
3. Xử lý logic place_bid với validation

Thread-Safety:
- Sử dụng threading.Lock() để đảm bảo thread-safe operations
- Mỗi thao tác đọc/ghi current_price và current_winner đều phải acquire lock
- Tránh Race Condition khi nhiều clients bid cùng lúc
"""

import threading


class AuctionState:
    """
    Class quản lý trạng thái đấu giá (Auction State)
    
    Attributes:
        starting_price (float): Giá khởi điểm
        current_price (float): Giá cao nhất hiện tại
        current_winner (str): Tên người đang thắng
        item_name (str): Tên vật phẩm đấu giá
        description (str): Mô tả vật phẩm
        lock (threading.Lock): Lock để đồng bộ hóa truy cập
    """
    
    def __init__(self, starting_price, item_name, description):
        """
        Khởi tạo trạng thái đấu giá
        
        Args:
            starting_price (float): Giá khởi điểm
            item_name (str): Tên vật phẩm đấu giá
            description (str): Mô tả vật phẩm
        """
        self.starting_price = starting_price
        self.current_price = starting_price
        self.current_winner = None  # Chưa có người thắng ban đầu
        self.item_name = item_name
        self.description = description
        
        # QUAN TRỌNG: Lock để bảo vệ current_price và current_winner
        # Tránh Race Condition khi nhiều client threads truy cập đồng thời
        self.lock = threading.Lock()
        
        print(f"[AUCTION_LOGIC] Khởi tạo đấu giá: {item_name}")
        print(f"[AUCTION_LOGIC] Giá khởi điểm: ${starting_price}")
        print(f"[AUCTION_LOGIC] Mô tả: {description}")
    
    def place_bid(self, user, value):
        """
        Xử lý đặt giá (BID) từ client
        
        Logic:
        1. Acquire lock để đảm bảo thread-safe
        2. Kiểm tra giá đặt có hợp lệ không (phải > current_price)
        3. Nếu hợp lệ: cập nhật current_price và current_winner
        4. Release lock
        5. Trả về (success, message)
        
        Args:
            user (str): Tên người đặt giá
            value (float): Giá đặt
        
        Returns:
            tuple: (success: bool, message: str)
                - success=True: Bid thành công
                - success=False: Bid thất bại (giá thấp hơn)
        
        Thread-Safety:
        - Sử dụng 'with self.lock' để tự động acquire/release lock
        - Đảm bảo không có 2 threads cùng thay đổi current_price
        """
        # CRITICAL SECTION - Bảo vệ bởi Lock
        with self.lock:
            # Validation: Giá phải lớn hơn giá hiện tại
            if value <= self.current_price:
                error_msg = f"Giá phải lớn hơn ${self.current_price}"
                return False, error_msg
            
            # Validation passed - Cập nhật trạng thái
            self.current_price = value
            self.current_winner = user
            
            success_msg = f"Bid thành công: {user} = ${value}"
            print(f"[AUCTION_LOGIC] {success_msg}")
            
            return True, success_msg
    
    def get_current_price(self):
        """
        Lấy giá hiện tại (thread-safe)
        
        Returns:
            float: Giá cao nhất hiện tại
        """
        with self.lock:
            return self.current_price
    
    def get_current_winner(self):
        """
        Lấy người thắng hiện tại (thread-safe)
        
        Returns:
            str or None: Tên người đang thắng, hoặc None nếu chưa có
        """
        with self.lock:
            return self.current_winner
    
    def get_auction_info(self):
        """
        Lấy toàn bộ thông tin đấu giá (thread-safe)
        
        Returns:
            dict: Dictionary chứa thông tin đấu giá
        """
        with self.lock:
            return {
                "item_name": self.item_name,
                "description": self.description,
                "starting_price": self.starting_price,
                "current_price": self.current_price,
                "current_winner": self.current_winner
            }
    
    def reset(self, starting_price=None):
        """
        Reset trạng thái đấu giá (dùng cho multi-round)
        
        Args:
            starting_price (float, optional): Giá khởi điểm mới
        """
        with self.lock:
            if starting_price is not None:
                self.starting_price = starting_price
            
            self.current_price = self.starting_price
            self.current_winner = None
            
            print(f"[AUCTION_LOGIC] Reset đấu giá: ${self.starting_price}")
