"""
Timer Thread Module cho Auction Game Server

Nhiệm vụ:
- Đếm ngược từ AUCTION_DURATION (120 giây)
- Gửi UPDATE_TIMER mỗi 1 giây để Client cập nhật realtime
- Gửi WARNING ở 10s và 5s
- Khi hết giờ: Broadcast WINNER → Đợi 5s → Shutdown server
"""

import threading
import time
import json


class TimerThread(threading.Thread):
    """
    Thread quản lý bộ đếm ngược thời gian đấu giá
    """
    
    def __init__(self, duration, auction_hub, auction_state):
        """
        Khởi tạo Timer Thread
        
        Args:
            duration: Thời gian đấu giá (giây) - VD: 120
            auction_hub: Reference đến AuctionHub để broadcast messages
            auction_state: Reference đến AuctionState để lấy thông tin winner
        """
        super().__init__()
        self.duration = duration
        self.auction_hub = auction_hub
        self.auction_state = auction_state
        self.remaining_time = duration
        self.is_running = True
        self.daemon = True  # Thread sẽ tự động kết thúc khi main thread kết thúc
        
        # NEW: Flag để chờ admin start
        self.wait_for_start = True
        self.game_started = False
        
        # Flags để tracking đã gửi cảnh báo chưa
        self.warning_10s_sent = False
        self.warning_5s_sent = False
    
    def run(self):
        """
        Main loop của Timer Thread
        Đếm ngược từ duration về 0
        """
        print(f"[TIMER] Thread khởi động - Đợi admin bắt đầu game...")
        
        # NEW: Đợi admin start game
        while self.wait_for_start and self.is_running:
            time.sleep(0.5)  # Check mỗi 0.5 giây
        
        if not self.is_running:
            print("[TIMER] Timer đã bị dừng trước khi bắt đầu")
            return
        
        print(f"[TIMER] 🚀 Game đã bắt đầu! Đếm ngược {self.duration} giây")
        self.game_started = True
        
        # Gửi initial timer update
        self.broadcast_timer_update()
        
        # Countdown loop
        while self.is_running and self.remaining_time > 0:
            # Sleep 1 giây
            time.sleep(1)
            
            if not self.is_running:
                print("[TIMER] Timer đã bị dừng")
                break
            
            # Giảm thời gian
            self.remaining_time -= 1
            
            # Gửi UPDATE_TIMER mỗi giây (Yêu cầu 1)
            self.broadcast_timer_update()
            
            # Kiểm tra cảnh báo 10 giây (Yêu cầu 3)
            if self.remaining_time == 10 and not self.warning_10s_sent:
                self.broadcast_warning(10)
                self.warning_10s_sent = True
            
            # Kiểm tra cảnh báo 5 giây (Yêu cầu 3)
            elif self.remaining_time == 5 and not self.warning_5s_sent:
                self.broadcast_warning(5)
                self.warning_5s_sent = True
            
            # Log mỗi 10 giây để tracking
            if self.remaining_time % 10 == 0:
                print(f"[TIMER] Còn lại {self.remaining_time} giây")
        
        # Hết giờ - Xử lý kết thúc (Yêu cầu 2)
        if self.is_running and self.remaining_time == 0:
            print("[TIMER] Hết thời gian! Đang xử lý kết thúc...")
            self.handle_auction_end()
    
    def broadcast_timer_update(self):
        """
        Gửi UPDATE_TIMER message cho tất cả clients
        Format: {"type": "UPDATE_TIMER", "remaining": <seconds>}
        """
        message = {
            "type": "UPDATE_TIMER",
            "remaining": self.remaining_time
        }
        
        # Broadcast qua auction_hub
        if self.auction_hub:
            self.auction_hub.broadcast_message(message)
    
    def broadcast_warning(self, seconds):
        """
        Gửi WARNING message khi còn X giây
        Format: {"type": "WARNING", "message": "...", "remaining": <seconds>}
        
        Args:
            seconds: Số giây còn lại (10 hoặc 5)
        """
        message = {
            "type": "WARNING",
            "message": f"⚠️ Cảnh báo: Còn {seconds} giây!",
            "remaining": seconds
        }
        
        print(f"[TIMER] ⚠️ CẢNH BÁO: Còn {seconds} giây!")
        
        if self.auction_hub:
            self.auction_hub.broadcast_message(message)
    
    def handle_auction_end(self):
        """
        Xử lý khi đấu giá kết thúc (hết giờ)
        
        Flow:
        1. Lấy thông tin winner từ auction_state
        2. Broadcast WINNER hoặc NO_WINNER
        3. Đợi 5 giây để clients xử lý
        4. Gọi shutdown server
        """
        print("[TIMER] ===== PHIÊN ĐẤU GIÁ KẾT THÚC =====")
        
        # Lấy thông tin winner
        winner_name = self.auction_state.get_current_winner()
        winner_price = self.auction_state.get_current_price()
        starting_price = self.auction_state.starting_price
        
        # Kiểm tra có winner hay không
        if winner_name and winner_price > starting_price:
            # Có người thắng
            message = {
                "type": "WINNER",
                "user": winner_name,
                "value": winner_price,
                "message": f"🎉 Chúc mừng {winner_name} đã thắng với giá ${winner_price}!"
            }
            
            print(f"[TIMER] 🏆 WINNER: {winner_name} - ${winner_price}")
            
        else:
            # Không có người thắng (không ai đặt giá)
            message = {
                "type": "NO_WINNER",
                "message": "❌ Phiên đấu giá kết thúc mà không có người đặt giá!"
            }
            
            print("[TIMER] ❌ Không có người thắng")
        
        # Broadcast kết quả
        if self.auction_hub:
            self.auction_hub.broadcast_message(message)
        
        # Đợi 5 giây để clients nhận và xử lý message (Yêu cầu 2)
        print("[TIMER] Đợi 5 giây để clients xử lý kết quả...")
        time.sleep(5)
        
        # Gửi SHUTDOWN message trước khi tắt
        shutdown_msg = {
            "type": "SHUTDOWN",
            "message": "Server đang đóng. Cảm ơn bạn đã tham gia!"
        }
        
        if self.auction_hub:
            self.auction_hub.broadcast_message(shutdown_msg)
        
        # Đợi thêm 1 giây để shutdown message được gửi
        time.sleep(1)
        
        # Trigger server shutdown
        print("[TIMER] Kích hoạt shutdown server...")
        
        # Import ở đây để tránh circular import
        import sys
        sys.exit(0)  # Exit để trigger cleanup trong main_server.py
    
    def start_game(self):
        """
        NEW: Method để admin start game (gọi khi nhấn Y)
        """
        if self.wait_for_start:
            print("[TIMER] 🎮 Admin đã bắt đầu game!")
            self.wait_for_start = False
            
            # Broadcast GAME_START message
            if self.auction_hub:
                message = {
                    "type": "GAME_START",
                    "message": "🎮 Phiên đấu giá đã bắt đầu!",
                    "duration": self.duration
                }
                self.auction_hub.broadcast_message(message)
    
    def stop(self):
        """
        Dừng Timer Thread (được gọi khi server shutdown)
        """
        print("[TIMER] Nhận lệnh dừng timer...")
        self.is_running = False
    
    def get_remaining_time(self):
        """
        Lấy thời gian còn lại
        
        Returns:
            int: Số giây còn lại
        """
        return self.remaining_time
    
    def format_time(self):
        """
        Format thời gian còn lại thành MM:SS
        
        Returns:
            str: Thời gian dạng "MM:SS"
        """
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        return f"{minutes:02d}:{seconds:02d}"
