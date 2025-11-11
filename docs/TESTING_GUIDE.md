# 🧪 TESTING GUIDE - Simple Auction Game

**Hướng dẫn chi tiết cách chạy test và ghi nhận kết quả**

---

## 📋 Chuẩn Bị

### **1. Kiểm tra môi trường**
```bash
# Kiểm tra Python version
python --version  # Phải >= 3.8

# Kiểm tra tkinter (cho GUI)
python -c "import tkinter; print('Tkinter OK')"

# Navigate to project
cd simpleAuctionGame
```

### **2. Backup config hiện tại**
```bash
cd server
copy auction_config.json auction_config.backup.json  # Windows
# cp auction_config.json auction_config.backup.json  # Linux/Mac
```

---

## 🎯 Test Scenarios

### **SCENARIO 1: Single Client Test (15 phút)**

**Mục tiêu:** Kiểm tra chức năng cơ bản với 1 client

**Setup:**
```bash
# Terminal 1: Server
cd server
python main_server.py --config config_examples/test.json  # 30 giây

# Terminal 2: Client
cd client
python client_ui.py
```

**Test Steps:**

1. **TC001: Server Startup**
   - [ ] Server khởi động không lỗi
   - [ ] Hiển thị config đúng
   - [ ] Timer bắt đầu đếm ngược
   - [ ] Log: ✅ Pass / ❌ Fail

2. **TC002: Client Connection**
   - [ ] Nhập tên: "TestPlayer1"
   - [ ] Kết nối: localhost:9999
   - [ ] Nhận WELCOME message
   - [ ] Hiển thị item info đúng
   - [ ] Log: ✅ Pass / ❌ Fail

3. **TC003: Valid Bid**
   - [ ] Nhập giá: `starting_price + 100`
   - [ ] Click "Đặt Giá"
   - [ ] Client nhận NEW_PRICE
   - [ ] Giá và winner cập nhật đúng
   - [ ] Log: ✅ Pass / ❌ Fail

4. **TC004: Invalid Bid (Low Price)**
   - [ ] Nhập giá thấp hơn current_price
   - [ ] Nhận ERROR message
   - [ ] Error hiển thị đúng
   - [ ] Current price không đổi
   - [ ] Log: ✅ Pass / ❌ Fail

5. **TC010-TC012: Timer & Warnings**
   - [ ] Timer đếm ngược đúng (30→0)
   - [ ] Nhận UPDATE_TIMER mỗi giây
   - [ ] Warning ở 10s
   - [ ] Warning ở 5s
   - [ ] Timer color thay đổi
   - [ ] Log: ✅ Pass / ❌ Fail

6. **TC013: Auction End**
   - [ ] Hết giờ, nhận WINNER message
   - [ ] Popup hiển thị
   - [ ] Server shutdown sau 5s
   - [ ] Log: ✅ Pass / ❌ Fail

**Ghi chú kết quả:**
```
SCENARIO 1 RESULTS:
- Total tests: 6
- Passed: __
- Failed: __
- Issues found: 
  1. ___________________
  2. ___________________
```

---

### **SCENARIO 2: Multi-Client Test (20 phút)**

**Mục tiêu:** Kiểm tra 4 clients đồng thời

**Setup:**
```bash
# Terminal 1: Server
cd server
python main_server.py --config config_examples/test.json

# Terminals 2-5: Clients
cd client
python client_ui.py  # x4 lần, 4 terminals khác nhau
```

**Test Steps:**

1. **TC006: Connect 4 Clients**
   - [ ] Tên: Player1, Player2, Player3, Player4
   - [ ] Tất cả kết nối thành công
   - [ ] Server log: "Tổng số clients: 4"
   - [ ] Tất cả nhận WELCOME
   - [ ] Log: ✅ Pass / ❌ Fail

2. **TC009: Broadcast Sync**
   - [ ] Player1 bid $1000
   - [ ] Tất cả 4 clients nhận NEW_PRICE
   - [ ] Tất cả hiển thị giá mới
   - [ ] Tất cả hiển thị winner: Player1
   - [ ] Sync time < 1 giây
   - [ ] Log: ✅ Pass / ❌ Fail

3. **TC: Sequential Bids**
   - [ ] Player1 bid $1000
   - [ ] Player2 bid $1200
   - [ ] Player3 bid $1500
   - [ ] Player4 bid $2000
   - [ ] Tất cả bids chấp nhận
   - [ ] Winner cuối: Player4
   - [ ] Current price: $2000
   - [ ] Log: ✅ Pass / ❌ Fail

4. **TC015: Client Disconnect**
   - [ ] Player2 đóng GUI
   - [ ] Server log: "Xóa client"
   - [ ] 3 clients còn lại hoạt động bình thường
   - [ ] Player3 bid $2500 thành công
   - [ ] Log: ✅ Pass / ❌ Fail

**Screenshot:** (Chụp màn hình 4 clients cùng lúc)

**Ghi chú kết quả:**
```
SCENARIO 2 RESULTS:
- Total tests: 4
- Passed: __
- Failed: __
- Network latency: ___ ms (ước tính)
- Issues: ___________________
```

---

### **SCENARIO 3: Race Condition Test (30 phút) ⭐⭐⭐**

**Mục tiêu:** Kiểm tra locking mechanism - TEST QUAN TRỌNG NHẤT

**Setup:**
```bash
# Terminal 1: Server
cd server
python main_server.py --duration 60  # Đủ thời gian để test

# Terminals 2-5: 4 Clients
cd client
python client_ui.py  # x4
```

**Test Steps:**

**Test 3A: Simultaneous Bids (Bid đồng thời)**

Chuẩn bị:
- Tất cả 4 clients đã kết nối
- Current price: $1000
- Sẵn sàng các giá:
  - Player1: $1500
  - Player2: $1600
  - Player3: $1400
  - Player4: $1700

Thực hiện:
1. **Đếm 3-2-1 và tất cả click "Đặt Giá" CÙNG LÚC**
2. Ghi nhận kết quả từng client:

```
Player1 ($1500): ✅ Success / ❌ Failed / Message: __________
Player2 ($1600): ✅ Success / ❌ Failed / Message: __________
Player3 ($1400): ✅ Success / ❌ Failed / Message: __________
Player4 ($1700): ✅ Success / ❌ Failed / Message: __________

Final current_price: $ ______
Final current_winner: __________
```

Kiểm tra:
- [ ] Chỉ bids hợp lệ (> current_price) được chấp nhận
- [ ] Giá cuối cùng là hợp lệ nhất
- [ ] Không có state corruption
- [ ] Server log tuần tự rõ ràng
- [ ] Log: ✅ Pass / ❌ Fail

**Chạy lại test này 5 lần:**
```
Run 1: Pass/Fail - Final price: $ _____
Run 2: Pass/Fail - Final price: $ _____
Run 3: Pass/Fail - Final price: $ _____
Run 4: Pass/Fail - Final price: $ _____
Run 5: Pass/Fail - Final price: $ _____

Consistency: ✅ Consistent / ❌ Inconsistent
```

---

**Test 3B: Rapid Spam Bids**

Chuẩn bị:
- 2 clients: Player1, Player2
- Current price: $1000

Thực hiện:
1. Player1 spam click "+$100" button 10 lần liên tục
2. Player2 spam click "+$500" button 5 lần liên tục (đồng thời)

Kiểm tra:
- [ ] Server xử lý tất cả bids tuần tự
- [ ] Không mất message
- [ ] Giá tăng dần hợp lệ
- [ ] Không có exception trong log
- [ ] Log: ✅ Pass / ❌ Fail

**Server log analysis:**
```
Total bids received: ____
Total bids accepted: ____
Total bids rejected: ____
Final price: $ ______
Winner: __________
```

---

**Test 3C: Edge Case - Same Value**

Chuẩn bị:
- 3 clients
- Current price: $1000

Thực hiện:
1. Tất cả 3 clients bid **cùng giá $1500** đồng thời

Kiểm tra:
- [ ] Chỉ 1 bid được chấp nhận (người đầu tiên)
- [ ] 2 bids còn lại bị reject
- [ ] Error message đúng: "Giá phải lớn hơn $1500"
- [ ] Log: ✅ Pass / ❌ Fail

**Ghi chú kết quả:**
```
SCENARIO 3 RESULTS:
- Test 3A (Simultaneous): ___
- Test 3B (Rapid Spam): ___
- Test 3C (Same Value): ___
- Race condition detected: ✅ Yes / ❌ No
- Lock mechanism working: ✅ Yes / ❌ No
- Critical issues: ___________________
```

---

### **SCENARIO 4: Stress Test (30 phút)**

**Mục tiêu:** Test với tải cao

**Setup:**
```bash
# Server
python main_server.py --duration 120

# 10 Clients (nếu máy mạnh, hoặc 6-8 clients)
# Mở 10 terminals và chạy client_ui.py
```

**Test Steps:**

1. **Connect 10 Clients**
   - [ ] Tất cả kết nối thành công
   - [ ] Server log clients count = 10
   - [ ] Log: ✅ Pass / ❌ Fail

2. **Random Bidding (2 phút)**
   - Mỗi client bid random trong 2 phút
   - Ghi nhận:
     - Server CPU usage: ____%
     - Memory usage: ____ MB
     - Response time (trung bình): ____ ms
     - Tổng bids gửi: ____
     - Tổng bids chấp nhận: ____

3. **Server Stability**
   - [ ] Server không crash
   - [ ] Không có exception
   - [ ] Broadcast messages không mất
   - [ ] UI responsive
   - [ ] Log: ✅ Pass / ❌ Fail

**Performance metrics:**
```
Peak clients: ____
Total bids processed: ____
Average response time: ____ ms
Max response time: ____ ms
Errors encountered: ____
Server uptime: 100% / <100%
```

---

### **SCENARIO 5: Config Testing (15 phút)**

**Test TC017: JSON Config**

```bash
# 1. Sửa auction_config.json
cd server
notepad auction_config.json

# Thay đổi:
{
  "item_name": "Test Product XYZ",
  "starting_price": 777,
  "auction_duration": 45,
  "description": "Test description 123"
}

# 2. Check config
python check_config.py
# - [ ] Preview đúng
# - [ ] Validation pass

# 3. Start server
python main_server.py
# - [ ] Load config đúng
# - [ ] Client nhận info đúng
```

**Test TC018: CLI Override**

```bash
python main_server.py --item "CLI Override Test" --price 9999 --duration 60

# Kiểm tra:
# - [ ] CLI args override file
# - [ ] Config source = "command_line"
# - [ ] Item name hiển thị đúng
# - [ ] Price = 9999
```

---

## 📊 Test Report Template

Sau khi chạy xong tất cả tests, điền vào form này:

```markdown
# TEST EXECUTION REPORT

**Date:** ________________
**Tester:** GK_Người 5 (Sang)
**Environment:** Windows / Linux / Mac
**Python Version:** ________

## Summary

| Scenario | Test Cases | Passed | Failed | Notes |
|----------|-----------|--------|--------|-------|
| Scenario 1 (Single) | 6 | __ | __ | __________ |
| Scenario 2 (Multi) | 4 | __ | __ | __________ |
| Scenario 3 (Race) | 3 | __ | __ | __________ |
| Scenario 4 (Stress) | 3 | __ | __ | __________ |
| Scenario 5 (Config) | 2 | __ | __ | __________ |
| **TOTAL** | **18** | **__** | **__** | |

**Pass Rate:** ____%

## Critical Findings

### ✅ Strengths
1. ____________________
2. ____________________

### ❌ Issues Found

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| BUG-001 | ___________ | High/Med/Low | Open/Fixed |
| BUG-002 | ___________ | High/Med/Low | Open/Fixed |

### 🔒 Thread-Safety Verification

- [ ] No race conditions detected
- [ ] Lock mechanism working correctly
- [ ] State always consistent
- [ ] No data corruption

### 📈 Performance

- Max clients tested: ____
- Average response time: ____ ms
- Server stability: Excellent / Good / Poor
- Memory usage: Normal / High

## Recommendations

1. ____________________
2. ____________________

## Screenshots

(Đính kèm screenshots của các test cases quan trọng)

---
**Sign-off:** _____________  
**Date:** _____________
```

---

## 💡 Testing Tips

### **Debugging Tips:**
```bash
# Xem server log chi tiết
python main_server.py 2>&1 | tee server.log

# Nếu client crash, check traceback
python client_ui.py 2>&1 | tee client.log
```

### **Network Issues:**
```bash
# Test local connection
ping localhost
telnet localhost 9999  # Kiểm tra port mở

# Check firewall (Windows)
netsh advfirewall show allprofiles
```

### **Performance Monitoring:**
```python
# Thêm vào code để đo response time
import time
start = time.time()
# ... code ...
print(f"Time: {time.time() - start:.3f}s")
```

---

## 📝 Checklist Trước Khi Hoàn Thành

- [ ] Đã chạy tất cả 5 scenarios
- [ ] Đã chạy race condition test ít nhất 5 lần
- [ ] Đã test với ít nhất 4 clients
- [ ] Đã ghi nhận tất cả bugs
- [ ] Đã chụp screenshots
- [ ] Đã điền test report
- [ ] Đã cập nhật TEST_PLAN.md với kết quả
- [ ] Đã commit code nếu có fixes

---

**Good luck testing! 🧪🎯**
