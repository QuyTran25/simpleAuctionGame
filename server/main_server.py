import socket
import threading
import sys
import signal

# Import các module cần thiết 
from timer_thread import TimerThread
from client_thread import ClientThread
from auction_config import load_auction_config

# Import các module Logic và Hub (Người 2)
from auction_logic import AuctionState
from auction_hub import AuctionHub

# CẤU HÌNH SERVER 
HOST = '0.0.0.0'  # Lắng nghe trên tất cả network interfaces
PORT = 9999        # Port để clients kết nối

# AUCTION CONFIG (sẽ được load từ file/args)
auction_config = None

# BIẾN TOÀN CỤC 
server_socket = None
auction_hub = None
timer_thread = None
auction_state = None
shutdown_flag = threading.Event()

def signal_handler(sig, frame):
    print("\n[SERVER] Nhận tín hiệu dừng server (Ctrl+C)...")
    shutdown_server()

def wait_for_admin_start():
    """
    Thread để đợi admin nhấn Y/N để bắt đầu game
    """
    global timer_thread
    
    while not shutdown_flag.is_set():
        try:
            user_input = input().strip().upper()
            
            if user_input == 'Y':
                print("\n" + "=" * 60)
                print("🚀 ADMIN ĐÃ BẮT ĐẦU GAME!")
                print("=" * 60)
                timer_thread.start_game()
                break
            elif user_input == 'N':
                print("\n[SERVER] Admin đã hủy - Đang shutdown...")
                shutdown_server()
                break
            else:
                print("❌ Vui lòng nhấn 'Y' để bắt đầu hoặc 'N' để hủy")
        except:
            break

def shutdown_server():
    print("[SERVER] Đang shutdown server...")
    shutdown_flag.set()
    
    # Đóng tất cả client connections
    if auction_hub:
        auction_hub.broadcast_shutdown()
        auction_hub.close_all_clients()
    
    # Dừng timer thread
    if timer_thread:
        timer_thread.stop()
        timer_thread.join(timeout=2)
    
    # Đóng server socket
    if server_socket:
        try:
            server_socket.close()
            print("[SERVER] Server socket đã đóng")
        except Exception as e:
            print(f"[SERVER] Lỗi khi đóng socket: {e}")
    
    print("[SERVER] Server đã dừng hoàn toàn")
    sys.exit(0)

def start_server():

    global server_socket, auction_hub, timer_thread, auction_state, auction_config
    
    print("=" * 60)
    print("🎯 SIMPLE AUCTION GAME - SERVER")
    print("=" * 60)
    
    # BƯỚC 0: Load Auction Config
    print("[CONFIG] Đang load cấu hình đấu giá...")
    auction_config = load_auction_config()
    print()
    
    # BƯỚC 1: Khởi tạo Auction State 
    print("[INIT] Khởi tạo Auction State...")
    # Sử dụng config từ file/args
    auction_state = AuctionState(
        starting_price=auction_config.starting_price,
        item_name=auction_config.item_name,
        description=auction_config.description
    )

    # BƯỚC 2: Khởi tạo Auction Hub
    print("[INIT] Khởi tạo Auction Hub...")
    auction_hub = AuctionHub(auction_state)

    # BƯỚC 3: Tạo Server Socket
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Cho phép reuse address ngay sau khi socket đóng
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)  # Queue tối đa 5 pending connections
        print(f"[SERVER] Đang lắng nghe tại {HOST}:{PORT}")
        print(f"[SERVER] Thời gian đấu giá: {auction_config.auction_duration} giây")
        print("-" * 60)
    except Exception as e:
        print(f"[ERROR] Không thể khởi động server: {e}")
        sys.exit(1)
    
    #  BƯỚC 4: Khởi động Timer Thread (CHƯA BẮT ĐẦU ĐẾM NGƯỢC)
    print("[TIMER] Khởi động timer thread...")
    timer_thread = TimerThread(
        duration=auction_config.auction_duration,
        auction_hub=auction_hub,
        auction_state=auction_state
    )
    timer_thread.start()
    print(f"[TIMER] Timer đã sẵn sàng ({auction_config.auction_duration} giây)")
    print("-" * 60)
    print()
    print("⏸️  GAME CHƯA BẮT ĐẦU - Đợi admin...")
    print("📢 Nhấn 'Y' và Enter để BẮT ĐẦU đấu giá")
    print("📢 Nhấn 'N' và Enter để HỦY và thoát")
    print("-" * 60)
    
    # BƯỚC 5: Start Admin Input Thread
    admin_thread = threading.Thread(target=wait_for_admin_start, daemon=True)
    admin_thread.start()
    
    # BƯỚC 6: Accept Loop (Main Server Loop)
    client_counter = 0
    active_threads = []  # Danh sách tracking các client threads
    
    print("[SERVER] Sẵn sàng chấp nhận clients...")
    print("[SERVER] Nhấn Ctrl+C để dừng server\n")
    
    try:
        while not shutdown_flag.is_set():
            try:
                # Set timeout để có thể check shutdown_flag định kỳ
                server_socket.settimeout(1.0)
                
                # Chấp nhận kết nối mới
                client_socket, client_address = server_socket.accept()
                
                # Kiểm tra nếu đang shutdown thì không nhận client mới
                if shutdown_flag.is_set():
                    client_socket.close()
                    break
                
                client_counter += 1
                client_id = f"Client-{client_counter}"
                
                print(f"[CONNECT] {client_id} kết nối từ {client_address}")
                
                # Tạo thread mới cho client này
                client_thread = ClientThread(
                    client_socket=client_socket,
                    client_address=client_address,
                    client_id=client_id,
                    auction_hub=auction_hub,
                    auction_state=auction_state
                )
                
                # Đăng ký client vào hub
                auction_hub.add_client(client_socket, client_id)
                
                # Khởi động thread
                client_thread.start()
                active_threads.append(client_thread)
                
                print(f"[SERVER] Tổng số clients đang kết nối: {auction_hub.get_client_count()}")
                
                # Cleanup các threads đã kết thúc
                active_threads = [t for t in active_threads if t.is_alive()]
                
            except socket.timeout:
                # Timeout là bình thường, tiếp tục loop để check shutdown_flag
                continue
            except OSError as e:
                # Socket đã đóng (có thể do shutdown)
                if shutdown_flag.is_set():
                    break
                print(f"[ERROR] Lỗi socket: {e}")
                break
                
    except KeyboardInterrupt:
        # Ctrl+C được bắt ở đây nếu signal handler không hoạt động
        print("\n[SERVER] Nhận KeyboardInterrupt...")
    except Exception as e:
        print(f"[ERROR] Lỗi không mong đợi trong accept loop: {e}")
    finally:
        # Cleanup
        print("\n[SERVER] Đang cleanup...")
        
        # Đợi tất cả client threads kết thúc (timeout 5 giây)
        for thread in active_threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        shutdown_server()
def main():

    # Đăng ký signal handler để xử lý Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Khởi động server
    start_server()

if __name__ == "__main__":
    main()
