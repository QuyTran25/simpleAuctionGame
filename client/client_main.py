import socket
import threading
import json

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9999 

# Hàm nhận data từ server
def listen_from_server(sock):
    while True:
        try:
            data = sock.recv(1024).decode("utf-8")
            if not data:
                print("Server đóng kết nối.")
                break

            # Có thể server gửi nhiều JSON một lúc -> tách theo newline
            messages = data.split("\n")
            for msg in messages:
                if msg.strip() == "":
                    continue
                try:
                    parsed = json.loads(msg)
                    handle_server_message(parsed)
                except json.JSONDecodeError:
                    print("Dữ liệu lỗi:", msg)

        except:
            print("Mất kết nối với server.")
            break


# Xử lý JSON nhận từ Server
def handle_server_message(obj):
    msg_type = obj.get("type")

    if msg_type == "WELCOME":
        # Server gửi thông tin welcome khi mới kết nối
        print("\n" + "=" * 60)
        print("CHAO MUNG DEN VOI PHIEN DAU GIA!")
        print("=" * 60)
        print(f"Vat pham: {obj.get('item_name', 'N/A')}")
        print(f"Mo ta: {obj.get('description', 'N/A')}")
        print(f"Gia khoi diem: ${obj.get('starting_price', 0)}")
        print(f"Gia hien tai: ${obj.get('current_price', 0)}")
        print(f"Nguoi dan dau: {obj.get('current_winner', 'Chua co')}")
        print("=" * 60)
        print(obj.get('message', ''))
        print()
    
    elif msg_type == "NEW_PRICE":
        # Có người đặt giá mới
        user = obj.get('user', 'Unknown')
        value = obj.get('value', 0)
        print(f"\n[UPDATE] {user} dang dan dau voi gia ${value}")
        print(f"   {obj.get('message', '')}")
    
    elif msg_type == "UPDATE_TIMER":
        # Cập nhật thời gian còn lại
        remaining = obj.get('remaining', 0)
        minutes = remaining // 60
        seconds = remaining % 60
        print(f"\r[TIMER] Thoi gian con lai: {minutes:02d}:{seconds:02d}", end='', flush=True)
    
    elif msg_type == "WARNING":
        # Cảnh báo còn ít thời gian
        print(f"\n\n[CANH BAO] {obj.get('message', '')}")
        print("=" * 60)
    
    elif msg_type == "WINNER":
        # Thông báo người thắng
        print("\n\n" + "=" * 60)
        print("PHIEN DAU GIA KET THUC!")
        print("=" * 60)
        print(f"Nguoi thang: {obj.get('user', 'N/A')}")
        print(f"Gia thang: ${obj.get('value', 0)}")
        print(f"{obj.get('message', '')}")
        print("=" * 60)
    
    elif msg_type == "NO_WINNER":
        # Không có người thắng
        print("\n\n" + "=" * 60)
        print("PHIEN DAU GIA KET THUC - KHONG CO NGUOI THANG")
        print("=" * 60)
        print(f"{obj.get('message', '')}")
        print("=" * 60)
    
    elif msg_type == "ERROR":
        # Lỗi từ server (VD: bid quá thấp)
        print(f"\n[LOI] {obj.get('message', 'Unknown error')}")
    
    elif msg_type == "SHUTDOWN":
        # Server đang shutdown
        print(f"\n\n[SHUTDOWN] {obj.get('message', 'Server dang dong')}")
    
    else:
        print("\n[UNKNOWN] Server gui:", obj)


def main():
    print("=" * 60)
    print("SIMPLE AUCTION GAME - CLIENT")
    print("=" * 60)
    print()
    
    client_name = input("Nhap ten cua ban: ")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_HOST, SERVER_PORT))
        print(f"Da ket noi den server tai {SERVER_HOST}:{SERVER_PORT}")
        print()
    except ConnectionRefusedError:
        print(f"[LOI] Khong the ket noi den server tai {SERVER_HOST}:{SERVER_PORT}")
        print("Hay dam bao server dang chay!")
        return
    except Exception as e:
        print(f"[LOI] Loi ket noi: {e}")
        return

    # Tạo thread để nghe server
    threading.Thread(target=listen_from_server, args=(sock,), daemon=True).start()

    # Đợi 1 giây để nhận WELCOME message
    import time
    time.sleep(1)

    # Hiển thị hướng dẫn
    print("\n" + "=" * 60)
    print("HUONG DAN SU DUNG")
    print("=" * 60)
    print("  <so tien>  - Dat gia (VD: 1500)")
    print("  info       - Xem huong dan")
    print("  exit       - Thoat")
    print("=" * 60)
    print()

    while True:
        try:
            user_input = input("\nNhap gia (hoac 'info'/'exit'): ").strip()

            # Thoát
            if user_input.lower() == "exit" or user_input.lower() == "quit":
                print("Dang thoat...")
                break
            
            # Xem hướng dẫn
            elif user_input.lower() == "info" or user_input.lower() == "help":
                print("\n" + "=" * 60)
                print("HUONG DAN SU DUNG")
                print("=" * 60)
                print("  <so tien>  - Dat gia (VD: 1500)")
                print("  info       - Xem huong dan")
                print("  exit       - Thoat")
                continue

            # Nhập số trực tiếp với validation
            try:
                # Chuyển đổi sang số
                price = float(user_input)
                
                # Validation: Kiểm tra giá trị hợp lệ
                if price <= 0:
                    print("[LOI] Gia phai lon hon 0!")
                    continue
                
                # Giới hạn giá tối đa (tránh số quá lớn như 1e+27)
                if price > 999999999:  # Tối đa 999 triệu
                    print("[LOI] Gia qua lon! Vui long nhap gia hop ly (toi da 999,999,999)")
                    continue
                
                # Kiểm tra số thập phân hợp lý (không quá nhiều chữ số)
                if len(user_input.replace('.', '').replace('-', '')) > 12:
                    print("[LOI] Gia khong hop le! Vui long nhap so binh thuong (VD: 1500)")
                    continue
                
                # Gửi bid
                bid_packet = {
                    "type": "BID",
                    "user": client_name,
                    "value": price
                }
                sock.send((json.dumps(bid_packet) + "\n").encode())
                
                # Hiển thị giá với format đẹp (có dấu phẩy)
                print(f"[SEND] Da gui bid: ${price:,.0f}")
                
            except ValueError:
                  # Không phải số hợp lệ
                print("[LOI] Vui long nhap so tien hop le (VD: 1500 hoac 1500.5)")
                print("      Hoac go 'info' de xem huong dan")

        except KeyboardInterrupt:
            print("\n\nNhan Ctrl+C - Dang thoat...")
            break
        except Exception as e:
            print(f"[LOI] {e}")
            break

    sock.close()
    print("Da thoat client. Cam on da tham gia!")


if __name__ == "__main__":
    main()
