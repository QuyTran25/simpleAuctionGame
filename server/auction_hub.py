"""
Auction Hub Module - Quản lý Broadcast và Client Connections

Nhiệm vụ chính:
1. Quản lý danh sách clients đang kết nối
2. Broadcast messages đến tất cả clients (realtime)
3. Xử lý add/remove clients thread-safe
4. Cung cấp các hàm broadcast chuyên biệt (NEW_PRICE, WINNER, etc.)

Thread-Safety:
- Sử dụng threading.Lock() để bảo vệ danh sách clients
- Mỗi thao tác với clients dict phải acquire lock
"""

import threading
import json
import socket


class AuctionHub:
    """
    Class quản lý broadcast và client connections
    
    Attributes:
        clients (dict): Dictionary mapping {socket: client_id}
        auction_state: Reference đến AuctionState để lấy thông tin
        lock (threading.Lock): Lock để đồng bộ hóa truy cập clients dict
    """
    
    def __init__(self, auction_state):
        """
        Khởi tạo Auction Hub
        
        Args:
            auction_state: Reference đến AuctionState object
        """
        self.clients = {}  # {socket: client_id}
        self.auction_state = auction_state
        
        # QUAN TRỌNG: Lock để bảo vệ clients dictionary
        # Tránh Race Condition khi nhiều threads add/remove clients đồng thời
        self.lock = threading.Lock()
        
        print("[AUCTION_HUB] Khởi tạo Hub - Sẵn sàng quản lý clients")
    
    def add_client(self, client_socket, client_id):
        """
        Thêm client mới vào danh sách (thread-safe)
        
        Args:
            client_socket: Socket object của client
            client_id (str): ID duy nhất của client
        """
        with self.lock:
            self.clients[client_socket] = client_id
            client_count = len(self.clients)
        
        print(f"[AUCTION_HUB] ➕ Thêm client: {client_id} (Tổng: {client_count})")
    
    def remove_client(self, client_socket):
        """
        Xóa client khỏi danh sách (thread-safe)
        
        Args:
            client_socket: Socket object cần xóa
        """
        with self.lock:
            if client_socket in self.clients:
                client_id = self.clients[client_socket]
                del self.clients[client_socket]
                client_count = len(self.clients)
                print(f"[AUCTION_HUB] ➖ Xóa client: {client_id} (Còn lại: {client_count})")
    
    def get_client_count(self):
        """
        Lấy số lượng clients đang kết nối (thread-safe)
        
        Returns:
            int: Số lượng clients
        """
        with self.lock:
            return len(self.clients)
    
    def broadcast_message(self, message_dict):
        """
        Broadcast message đến TẤT CẢ clients
        
        Đây là hàm CORE của Hub - được gọi bởi:
        - ClientThread: Khi có BID mới (broadcast NEW_PRICE)
        - TimerThread: Mỗi giây (broadcast UPDATE_TIMER)
        - Server: Khi shutdown (broadcast SHUTDOWN)
        
        Args:
            message_dict (dict): Dictionary chứa message data
                Format: {"type": "...", "message": "...", ...}
        
        Thread-Safety:
        - Tạo snapshot của clients list để tránh modification during iteration
        - Xử lý từng client trong snapshot (không hold lock lâu)
        """
        # Tạo JSON string từ dict
        try:
            message_json = json.dumps(message_dict) + "\n"
            message_bytes = message_json.encode('utf-8')
        except Exception as e:
            print(f"[AUCTION_HUB] ❌ Lỗi encode message: {e}")
            return
        
        # Tạo snapshot của clients để tránh modification during iteration
        with self.lock:
            clients_snapshot = list(self.clients.items())
        
        # Broadcast đến từng client
        failed_sockets = []
        
        for client_socket, client_id in clients_snapshot:
            try:
                client_socket.sendall(message_bytes)
            except socket.error as e:
                # Client đã disconnect hoặc socket error
                print(f"[AUCTION_HUB] ⚠️ Không gửi được đến {client_id}: {e}")
                failed_sockets.append(client_socket)
            except Exception as e:
                print(f"[AUCTION_HUB] ❌ Lỗi broadcast đến {client_id}: {e}")
                failed_sockets.append(client_socket)
        
        # Cleanup các sockets failed
        if failed_sockets:
            for sock in failed_sockets:
                self.remove_client(sock)
    
    def broadcast_new_price(self, user, value):
        """
        Broadcast khi có giá mới (NEW_PRICE event)
        
        Được gọi bởi ClientThread khi place_bid thành công
        
        Args:
            user (str): Tên người đặt giá
            value (float): Giá mới
        """
        message = {
            "type": "NEW_PRICE",
            "user": user,
            "value": value,
            "message": f"{user} đã đặt giá ${value}"
        }
        
        print(f"[AUCTION_HUB] 📢 Broadcast NEW_PRICE: {user} = ${value}")
        self.broadcast_message(message)
    
    def broadcast_winner(self, user, value):
        """
        Broadcast thông báo người thắng cuộc
        
        Được gọi bởi TimerThread khi đấu giá kết thúc
        
        Args:
            user (str): Tên người thắng
            value (float): Giá thắng
        """
        message = {
            "type": "WINNER",
            "user": user,
            "value": value,
            "message": f"🎉 Chúc mừng {user} đã thắng với giá ${value}!"
        }
        
        print(f"[AUCTION_HUB] 🏆 Broadcast WINNER: {user} = ${value}")
        self.broadcast_message(message)
    
    def broadcast_no_winner(self):
        """
        Broadcast khi không có người thắng (không ai bid)
        
        Được gọi bởi TimerThread khi đấu giá kết thúc nhưng không có bid
        """
        message = {
            "type": "NO_WINNER",
            "message": "⚠️ Phiên đấu giá kết thúc - Không có người thắng"
        }
        
        print("[AUCTION_HUB] ⚠️ Broadcast NO_WINNER")
        self.broadcast_message(message)
    
    def broadcast_shutdown(self):
        """
        Broadcast thông báo server shutdown
        
        Được gọi bởi Server trước khi shutdown
        """
        message = {
            "type": "SHUTDOWN",
            "message": "Server đang shutdown. Cảm ơn đã tham gia!"
        }
        
        print("[AUCTION_HUB] 🛑 Broadcast SHUTDOWN")
        self.broadcast_message(message)
    
    def close_all_clients(self):
        """
        Đóng tất cả client connections
        
        Được gọi khi server shutdown
        """
        print("[AUCTION_HUB] Đang đóng tất cả client connections...")
        
        with self.lock:
            clients_snapshot = list(self.clients.items())
        
        for client_socket, client_id in clients_snapshot:
            try:
                client_socket.close()
                print(f"[AUCTION_HUB] Đã đóng {client_id}")
            except Exception as e:
                print(f"[AUCTION_HUB] Lỗi khi đóng {client_id}: {e}")
        
        # Clear danh sách
        with self.lock:
            self.clients.clear()
        
        print(f"[AUCTION_HUB] Đã đóng tất cả {len(clients_snapshot)} clients")
    
    def get_clients_info(self):
        """
        Lấy thông tin tất cả clients (cho debugging)
        
        Returns:
            list: List của client IDs
        """
        with self.lock:
            return list(self.clients.values())
