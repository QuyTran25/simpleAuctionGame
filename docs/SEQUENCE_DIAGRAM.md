# 📊 SEQUENCE DIAGRAMS - Simple Auction Game

**Project:** Simple Auction Game  

---

## 🎯 Cách Xem Sequence Diagrams

Các sequence diagrams trong file này được viết bằng **Mermaid syntax**. Để xem dạng hình vẽ:

### **Cách 1: Xem trên GitHub** (Khuyên dùng - Đơn giản nhất)
1. Mở file này trên GitHub: `docs/SEQUENCE_DIAGRAM.md`
2. GitHub tự động render Mermaid thành hình vẽ
3. ✅ Không cần cài đặt gì!

### **Cách 2: Xem trong VS Code**
1. Cài extension: **"Markdown Preview Mermaid Support"** by Matt Bierner
   - Nhấn `Ctrl + Shift + X` → Tìm "Markdown Preview Mermaid Support" → Install
2. Mở file `SEQUENCE_DIAGRAM.md`
3. Nhấn `Ctrl + K` rồi `V` → Xem preview bên cạnh
4. Hoặc `Ctrl + Shift + V` → Preview toàn màn hình

### **Cách 3: Xem online**
1. Copy code Mermaid (phần trong \`\`\`mermaid ... \`\`\`)
2. Vào https://mermaid.live
3. Paste code vào → Xem kết quả ngay

---

## 📖 Mục Lục

1. [Server Startup Sequence](#1-server-startup-sequence)
2. [Client Connection Sequence](#2-client-connection-sequence)
3. [Bid Placement Sequence (Success)](#3-bid-placement-sequence-success)
4. [Bid Placement Sequence (Failed)](#4-bid-placement-sequence-failed)
5. [Race Condition Handling](#5-race-condition-handling-với-lock)
6. [Timer Update Sequence](#6-timer-update-sequence)
7. [Warning Sequence](#7-warning-sequence-10s--5s)
8. [Auction End - Winner](#8-auction-end---có-winner)
9. [Auction End - No Winner](#9-auction-end---không-có-winner)
10. [Client Disconnect](#10-client-disconnect-sequence)
11. [Server Shutdown](#11-server-shutdown-sequence)

---

## 1. Server Startup Sequence

```mermaid
sequenceDiagram
    participant Main as main_server.py
    participant Config as AuctionConfig
    participant State as AuctionState
    participant Hub as AuctionHub
    participant Timer as TimerThread
    participant Socket as Server Socket

    Main->>Config: load_auction_config()
    Config->>Config: Read auction_config.json
    Config-->>Main: Return config object
    
    Main->>State: AuctionState(starting_price, item_name, desc)
    State->>State: Initialize lock, current_price, current_winner
    State-->>Main: State object created
    
    Main->>Hub: AuctionHub(auction_state)
    Hub->>Hub: Initialize clients dict, lock
    Hub-->>Main: Hub object created
    
    Main->>Socket: socket.socket(AF_INET, SOCK_STREAM)
    Main->>Socket: bind((HOST, PORT))
    Main->>Socket: listen(5)
    Socket-->>Main: Server socket ready
    
    Main->>Timer: TimerThread(duration, hub, state)
    Timer->>Timer: Initialize remaining_time
    Main->>Timer: start()
    Timer->>Timer: Begin countdown loop
    Timer->>Hub: broadcast_message(UPDATE_TIMER)
    
    Note over Main,Socket: Server ready to accept clients
```

**Mô tả:**
1. Main server load config từ JSON file
2. Khởi tạo AuctionState với lock để bảo vệ giá
3. Khởi tạo AuctionHub để quản lý clients
4. Tạo socket và lắng nghe tại port 9999
5. Start TimerThread để đếm ngược
6. Server sẵn sàng accept clients

---

## 2. Client Connection Sequence

```mermaid
sequenceDiagram
    participant Client as Client GUI
    participant Socket as Server Socket
    participant Main as Main Server
    participant CThread as ClientThread
    participant Hub as AuctionHub
    participant State as AuctionState

    Client->>Socket: connect(HOST, PORT)
    Socket-->>Client: Connection accepted
    
    Socket->>Main: accept() returns client_socket
    Main->>CThread: ClientThread(socket, id, hub, state)
    Main->>Hub: add_client(socket, client_id)
    Hub->>Hub: Lock acquired
    Hub->>Hub: clients[socket] = client_id
    Hub->>Hub: Lock released
    
    Main->>CThread: start()
    CThread->>CThread: run() begins
    
    CThread->>State: get_auction_info()
    State->>State: Lock acquired
    State-->>CThread: {item_name, price, winner, desc}
    State->>State: Lock released
    
    CThread->>Client: send_message(WELCOME)
    Note over Client,CThread: WELCOME message includes:<br/>item_name, starting_price,<br/>current_price, current_winner,<br/>description
    
    Client->>Client: Update UI with item info
    Client->>Client: Display timer, price, winner
    
    loop Every 1 second
        Timer->>Hub: broadcast_message(UPDATE_TIMER)
        Hub->>Client: UPDATE_TIMER {remaining: X}
        Client->>Client: Update timer display
    end
```

**Mô tả:**
1. Client gửi connection request
2. Server accept và tạo ClientThread mới
3. Hub add client vào danh sách (thread-safe với lock)
4. ClientThread gửi WELCOME message với thông tin vật phẩm
5. Client cập nhật UI
6. Client bắt đầu nhận UPDATE_TIMER mỗi giây

---

## 3. Bid Placement Sequence (Success)

```mermaid
sequenceDiagram
    participant Client as Client GUI
    participant CThread as ClientThread
    participant State as AuctionState
    participant Hub as AuctionHub
    participant AllClients as All Clients

    Client->>Client: User nhập giá: $1500
    Client->>Client: Click "Đặt Giá"
    Client->>CThread: send(BID {user: Player1, value: 1500})
    
    CThread->>CThread: handle_message(BID)
    CThread->>CThread: Parse user, value
    
    CThread->>State: place_bid(Player1, 1500)
    
    Note over State: CRITICAL SECTION
    State->>State: Lock acquired 🔒
    State->>State: Check: value > current_price?
    alt Value > current_price
        State->>State: current_price = 1500
        State->>State: current_winner = Player1
        State->>State: Lock released 🔓
        State-->>CThread: (True, "Success")
        
        CThread->>Hub: broadcast_new_price(Player1, 1500)
        Hub->>AllClients: broadcast(NEW_PRICE)
        
        AllClients->>AllClients: Update UI:
        Note over AllClients: • Giá cao nhất: $1500<br/>• Người dẫn đầu: Player1<br/>• Log: "Player1 đặt $1500"
    end
```

**Mô tả:**
1. Client gửi BID request với giá $1500
2. ClientThread nhận và parse message
3. Gọi `place_bid()` trong AuctionState
4. **Lock được acquire** - CRITICAL SECTION
5. Kiểm tra giá hợp lệ (> current_price)
6. Cập nhật state và release lock
7. Broadcast NEW_PRICE đến tất cả clients
8. Tất cả clients cập nhật UI

---

## 4. Bid Placement Sequence (Failed)

```mermaid
sequenceDiagram
    participant Client as Client GUI
    participant CThread as ClientThread
    participant State as AuctionState

    Note over Client: Current price: $1500
    Client->>Client: User nhập giá: $1200 (thấp hơn!)
    Client->>CThread: send(BID {user: Player2, value: 1200})
    
    CThread->>State: place_bid(Player2, 1200)
    
    State->>State: Lock acquired 🔒
    State->>State: Check: 1200 > 1500?
    State->>State: ❌ False! (1200 <= 1500)
    State->>State: Lock released 🔓
    State-->>CThread: (False, "Giá phải lớn hơn $1500")
    
    CThread->>Client: send(ERROR {"message": "Giá phải lớn hơn $1500"})
    
    Client->>Client: Display error message
    Note over Client: ❌ "Giá phải lớn hơn $1500"<br/>Current price không đổi
```

**Mô tả:**
1. Client gửi BID với giá thấp hơn current_price
2. State validate và reject (trong lock)
3. Trả về ERROR message
4. Chỉ client đó nhận error (không broadcast)
5. UI hiển thị lỗi, giá không thay đổi

---

## 5. Race Condition Handling (với Lock)

```mermaid
sequenceDiagram
    participant C1 as Client 1
    participant C2 as Client 2
    participant C3 as Client 3
    participant Thread1 as Thread-1
    participant Thread2 as Thread-2
    participant Thread3 as Thread-3
    participant State as AuctionState (Lock)
    participant Hub as Hub

    Note over C1,C3: Current price: $1000<br/>Tất cả bid CÙng LÚC:

    par Parallel Bids
        C1->>Thread1: BID $1500
        C2->>Thread2: BID $1600
        C3->>Thread3: BID $1400
    end

    Note over Thread1,State: Threads arrive at place_bid()
    
    Thread1->>State: place_bid(C1, 1500) - TRY LOCK
    Note over State: 🔒 Thread1 gets lock first
    State->>State: Check: 1500 > 1000? ✅ YES
    State->>State: current_price = 1500
    State->>State: current_winner = C1
    State-->>Thread1: Success
    Note over State: 🔓 Lock released
    Thread1->>Hub: broadcast_new_price(C1, 1500)
    
    Thread2->>State: place_bid(C2, 1600) - TRY LOCK
    Note over State: 🔒 Thread2 gets lock
    Note over State: (Thread3 waiting...)
    State->>State: Check: 1600 > 1500? ✅ YES
    State->>State: current_price = 1600
    State->>State: current_winner = C2
    State-->>Thread2: Success
    Note over State: 🔓 Lock released
    Thread2->>Hub: broadcast_new_price(C2, 1600)
    
    Thread3->>State: place_bid(C3, 1400) - TRY LOCK
    Note over State: 🔒 Thread3 gets lock
    State->>State: Check: 1400 > 1600? ❌ NO
    State->>State: REJECT (giá thấp hơn 1600)
    State-->>Thread3: Failed
    Note over State: 🔓 Lock released
    Thread3->>C3: send(ERROR)

    Note over C1,C3: Kết quả:<br/>✅ C1: Success (1500)<br/>✅ C2: Success (1600)<br/>❌ C3: Failed (1400 < 1600)<br/><br/>🎯 Không có race condition!<br/>Giá cuối cùng: $1600 (hợp lệ)
```

**Mô tả:**
- **Vấn đề:** 3 clients bid đồng thời
- **Giải pháp:** Lock trong AuctionState.place_bid()
- **Kết quả:**
  - Thread1 được lock đầu tiên → Success ($1500)
  - Thread2 chờ lock → Success ($1600 > $1500)
  - Thread3 chờ lock → Failed ($1400 < $1600)
- **Không có race condition:** current_price luôn hợp lệ

---

## 6. Timer Update Sequence

```mermaid
sequenceDiagram
    participant Timer as TimerThread
    participant Hub as AuctionHub
    participant C1 as Client 1
    participant C2 as Client 2
    participant CN as Client N

    Note over Timer: remaining_time = 120
    
    loop Every 1 second
        Timer->>Timer: time.sleep(1)
        Timer->>Timer: remaining_time -= 1
        
        Timer->>Timer: Create UPDATE_TIMER message
        Note over Timer: {type: "UPDATE_TIMER",<br/>remaining: 119}
        
        Timer->>Hub: broadcast_message(UPDATE_TIMER)
        
        Hub->>Hub: Lock clients list
        Hub->>Hub: Create snapshot of clients
        Hub->>Hub: Unlock clients list
        
        par Broadcast to all
            Hub->>C1: send(UPDATE_TIMER)
            Hub->>C2: send(UPDATE_TIMER)
            Hub->>CN: send(UPDATE_TIMER)
        end
        
        C1->>C1: Update timer UI: 01:59
        C2->>C2: Update timer UI: 01:59
        CN->>CN: Update timer UI: 01:59
        
        Note over Timer: remaining_time = 119
    end
```

**Mô tả:**
1. TimerThread sleep 1 giây
2. Giảm remaining_time
3. Tạo UPDATE_TIMER message
4. Hub broadcast đến tất cả clients (thread-safe)
5. Mỗi client cập nhật UI timer
6. Lặp lại đến khi remaining_time = 0

---

## 7. Warning Sequence (10s & 5s)

```mermaid
sequenceDiagram
    participant Timer as TimerThread
    participant Hub as AuctionHub
    participant Clients as All Clients

    Note over Timer: remaining_time = 10
    
    Timer->>Timer: Check: remaining == 10?
    Timer->>Timer: ✅ Yes! Send warning
    
    Timer->>Hub: broadcast_message(WARNING)
    Note over Hub: {type: "WARNING",<br/>message: "⚠️ Còn 10 giây!",<br/>remaining: 10}
    
    Hub->>Clients: broadcast(WARNING)
    
    Clients->>Clients: Display warning
    Note over Clients: • Log: "⚠️ Còn 10 giây!"<br/>• Timer color: ORANGE<br/>• Start blink effect
    
    Note over Timer: Continue countdown...
    Note over Timer: remaining_time = 5
    
    Timer->>Timer: Check: remaining == 5?
    Timer->>Timer: ✅ Yes! Send warning
    
    Timer->>Hub: broadcast_message(WARNING)
    Note over Hub: {type: "WARNING",<br/>message: "⚠️ Còn 5 giây!",<br/>remaining: 5}
    
    Hub->>Clients: broadcast(WARNING)
    
    Clients->>Clients: Display critical warning
    Note over Clients: • Log: "⚠️ Còn 5 giây!"<br/>• Timer color: RED<br/>• Blink faster
```

**Mô tả:**
1. Timer kiểm tra remaining_time mỗi giây
2. Khi remaining = 10s → Gửi WARNING
3. Clients hiển thị cảnh báo (màu cam, blink)
4. Khi remaining = 5s → Gửi WARNING thứ 2
5. Clients hiển thị cảnh báo nghiêm trọng (màu đỏ, blink nhanh)

---

## 8. Auction End - Có Winner

```mermaid
sequenceDiagram
    participant Timer as TimerThread
    participant State as AuctionState
    participant Hub as AuctionHub
    participant Clients as All Clients
    participant Main as Main Server

    Note over Timer: remaining_time = 0
    Timer->>Timer: Loop exits (time up!)
    Timer->>Timer: handle_auction_end()
    
    Timer->>State: get_current_winner()
    State-->>Timer: "Player1"
    
    Timer->>State: get_current_price()
    State-->>Timer: 2500
    
    alt Has Winner (price > starting_price)
        Timer->>Hub: broadcast_message(WINNER)
        Note over Hub: {type: "WINNER",<br/>user: "Player1",<br/>value: 2500,<br/>message: "🎉 Chúc mừng..."}
        
        Hub->>Clients: broadcast(WINNER)
        
        Clients->>Clients: Display winner
        Note over Clients: • Show popup: "🎉 Player1 thắng!"<br/>• Log: "WINNER: Player1 - $2500"<br/>• Timer: "🏆 Đã kết thúc"
        
        Timer->>Timer: time.sleep(5)
        Note over Timer: Đợi 5 giây để clients xử lý
        
        Timer->>Hub: broadcast_message(SHUTDOWN)
        Hub->>Clients: broadcast(SHUTDOWN)
        
        Timer->>Main: sys.exit(0)
        Note over Main: Trigger cleanup và shutdown
        
        Main->>Hub: close_all_clients()
        Main->>Main: Close server socket
        Main->>Main: Exit program
    end
```

**Mô tả:**
1. Timer hết giờ (remaining = 0)
2. Lấy thông tin winner từ State
3. Broadcast WINNER message đến tất cả clients
4. Clients hiển thị popup và log
5. Đợi 5 giây
6. Broadcast SHUTDOWN
7. Server cleanup và exit

---

## 9. Auction End - Không Có Winner

```mermaid
sequenceDiagram
    participant Timer as TimerThread
    participant State as AuctionState
    participant Hub as AuctionHub
    participant Clients as All Clients
    participant Main as Main Server

    Note over Timer: remaining_time = 0
    Timer->>Timer: handle_auction_end()
    
    Timer->>State: get_current_winner()
    State-->>Timer: None (không ai bid)
    
    alt No Winner
        Timer->>Hub: broadcast_message(NO_WINNER)
        Note over Hub: {type: "NO_WINNER",<br/>message: "❌ Không có người thắng"}
        
        Hub->>Clients: broadcast(NO_WINNER)
        
        Clients->>Clients: Display no winner
        Note over Clients: • Log: "❌ Không có winner"<br/>• Show popup: "Không có người thắng"
        
        Timer->>Timer: time.sleep(5)
        Timer->>Hub: broadcast_message(SHUTDOWN)
        Hub->>Clients: broadcast(SHUTDOWN)
        
        Timer->>Main: sys.exit(0)
        Main->>Main: Cleanup and exit
    end
```

**Mô tả:**
1. Timer hết giờ nhưng current_winner = None
2. Broadcast NO_WINNER message
3. Clients hiển thị thông báo không có winner
4. Đợi 5 giây và shutdown

---

## 10. Client Disconnect Sequence

```mermaid
sequenceDiagram
    participant Client as Client GUI
    participant CThread as ClientThread
    participant Hub as AuctionHub
    participant State as AuctionState

    Note over Client: User đóng cửa sổ hoặc<br/>network error
    
    Client->>Client: Connection closed
    
    CThread->>CThread: recv() returns empty data
    CThread->>CThread: Break from loop
    CThread->>CThread: cleanup()
    
    CThread->>Hub: remove_client(socket)
    Hub->>Hub: Lock acquired 🔒
    Hub->>Hub: Delete from clients dict
    Hub->>Hub: Lock released 🔓
    Note over Hub: Client count decreased
    
    CThread->>Client: socket.close()
    CThread->>CThread: Thread exits
    
    Note over State: State không đổi:<br/>Nếu client đã bid và đang lead,<br/>vẫn giữ current_winner
```

**Mô tả:**
1. Client ngắt kết nối (đóng app hoặc network error)
2. ClientThread phát hiện (recv = empty)
3. Cleanup: remove khỏi Hub
4. Đóng socket
5. Thread exits
6. State không bị ảnh hưởng (winner vẫn giữ)

---

## 11. Server Shutdown Sequence

```mermaid
sequenceDiagram
    participant User as User/Admin
    participant Main as Main Server
    participant Hub as AuctionHub
    participant Timer as TimerThread
    participant Clients as All Clients
    participant Socket as Server Socket

    User->>Main: Ctrl+C (SIGINT)
    Main->>Main: signal_handler() triggered
    Main->>Main: shutdown_flag.set()
    
    Main->>Hub: broadcast_shutdown()
    Hub->>Clients: broadcast(SHUTDOWN)
    Note over Clients: Nhận thông báo shutdown,<br/>hiển thị message
    
    Main->>Hub: close_all_clients()
    loop For each client
        Hub->>Clients: socket.close()
    end
    Hub->>Hub: clients.clear()
    
    Main->>Timer: timer.stop()
    Timer->>Timer: is_running = False
    Timer->>Timer: Exit loop
    Main->>Timer: timer.join(timeout=2)
    
    Main->>Socket: server_socket.close()
    Socket->>Socket: Release port 9999
    
    Main->>Main: sys.exit(0)
    Note over Main: Server shutdown hoàn tất
```

**Mô tả:**
1. Admin nhấn Ctrl+C
2. Signal handler bắt SIGINT
3. Set shutdown_flag
4. Broadcast SHUTDOWN message
5. Đóng tất cả client connections
6. Dừng TimerThread
7. Đóng server socket
8. Exit gracefully

---

## 📌 Chú Thích

### **Ký Hiệu:**
- 🔒 = Lock acquired (Critical Section)
- 🔓 = Lock released
- ✅ = Validation passed
- ❌ = Validation failed
- ⚠️ = Warning
- 🎯 = Important note

### **Thread-Safety:**
- Tất cả truy cập `current_price` và `current_winner` đều trong lock
- Hub.clients dict cũng được bảo vệ bởi lock
- Broadcast sử dụng snapshot để tránh modification during iteration

### **Message Flow:**
- **Unicast:** Server → 1 Client (WELCOME, ERROR)
- **Broadcast:** Server → All Clients (NEW_PRICE, UPDATE_TIMER, WARNING, WINNER, SHUTDOWN)

---

**Document Control:**
- Created: 2025-11-11
- Last Updated: 2025-11-11
- Version: 1.0
