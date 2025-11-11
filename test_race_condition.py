"""
Script để test race condition - Gửi 4 BID requests đồng thời
"""
import socket
import json
import threading
import time

HOST = 'localhost'
PORT = 9999

def send_bid(user, value):
    """Gửi BID request đến server"""
    try:
        # Kết nối
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        print(f"[{user}] Đã kết nối")
        
        # Nhận WELCOME (bỏ qua)
        welcome = sock.recv(4096)
        
        # Gửi BID
        bid_msg = {
            "type": "BID",
            "user": user,
            "value": value
        }
        message = json.dumps(bid_msg) + "\n"
        sock.sendall(message.encode('utf-8'))
        print(f"[{user}] Đã gửi bid: ${value}")
        
        # Nhận response
        time.sleep(0.5)  # Đợi response
        response = sock.recv(4096).decode('utf-8')
        print(f"[{user}] Response: {response}")
        
        sock.close()
        
    except Exception as e:
        print(f"[{user}] Error: {e}")

def test_race_condition():
    """Test với 4 threads gửi đồng thời"""
    print("=" * 60)
    print("RACE CONDITION TEST - Simultaneous Bids")
    print("=" * 60)
    
    # Đợi người dùng sẵn sàng
    input("Nhấn Enter để bắt đầu test (đảm bảo server đã chạy)...")
    
    # Danh sách bids
    bids = [
        ("Player1", 500),
        ("Player2", 600),
        ("Player3", 400),
        ("Player4", 700),
    ]
    
    # Tạo threads
    threads = []
    for user, value in bids:
        thread = threading.Thread(target=send_bid, args=(user, value))
        threads.append(thread)
    
    # Đếm ngược
    print("\nĐếm ngược...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("GO! Gửi tất cả bids đồng thời...")
    
    # Start tất cả threads cùng lúc
    start_time = time.time()
    for thread in threads:
        thread.start()
    
    # Đợi tất cả threads hoàn thành
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start_time
    
    print(f"\n✅ Hoàn thành trong {elapsed:.3f} giây")
    print("=" * 60)

if __name__ == "__main__":
    test_race_condition()
