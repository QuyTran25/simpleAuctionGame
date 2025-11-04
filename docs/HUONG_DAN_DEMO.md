# 🎯 HƯỚNG DẪN THAY ĐỔI SẢN PHẨM CHO DEMO

## 📝 CÁCH NHANH NHẤT - 3 BƯỚC

### **BƯỚC 1: Mở và sửa file config**

```bash
cd server
notepad auction_config.json
```

Hoặc dùng bất kỳ editor nào (VSCode, Notepad++, v.v.)

### **BƯỚC 2: Thay đổi thông tin**
# thay đổi thông tin trực tieps ở file acution_config.json để để server nhận được
```json 
{
  "item_name": "TÊN SẢN PHẨM CỦA BẠN",
  "starting_price": GIÁ_KHỞI_ĐIỂM,
  "auction_duration": THỜI_GIAN_GIÂY,
  "description": "MÔ TẢ SẢN PHẨM"
}
```
## các json dưới đây là ví dụ có thể copy rồi dán nhanh qua file acution_config.json để test

**VÍ DỤ - Demo PS5:**
```json
{
  "item_name": "PlayStation 5 Console + 2 Tay Cam",
  "starting_price": 5000,
  "auction_duration": 120,
  "description": "Kem 5 game dia AAA, bao hanh 12 thang"
}
```

**VÍ DỤ - Demo MacBook:**
```json
{
  "item_name": "MacBook Pro M3 Max 16-inch",
  "starting_price": 20000,
  "auction_duration": 180,
  "description": "36GB RAM, 1TB SSD, Space Black"
}
```

**VÍ DỤ - Test nhanh (30 giây):**
```json
{
  "item_name": "Test Item - Demo",
  "starting_price": 100,
  "auction_duration": 30,
  "description": "Test nhanh 30 giay"
}
```
## 🎮 QUY TRÌNH DEMO CHUẨN

### **Chuẩn bị (5 phút trước demo)**

```bash
# 1. Sửa config ( file auction_config.json)**
cd server
notepad auction_config.json
# → Thay đổi item_name, starting_price, duration, description như mô tả ở trên

# 2. Kiểm tra
python check_config.py
# → Xem output, đảm bảo ✅

# 3. Start server ( đảm bảo server chạy sẵn sàn rồi mới chuyển qua bước tiếp)**
python main_server.py
# → Xem log confirm config đúng
```

### **Trong demo**

```bash
# Terminal 1: Server (đã chạy)
cd server
python main_server.py

# Terminal 2, 3, 4...: Clients
cd client
python client_ui.py
# → Nhập tên: Player1, Player2, Player3...
# → Kết nối: localhost:9999
```

---

## ⚡ THAY ĐỔI NHANH KHÔNG CẦN RESTART

**Nếu đang demo và muốn đổi sản phẩm:**

1. **Dừng server**: Ctrl+C
2. **Sửa config**: `notepad auction_config.json`
3. **Kiểm tra**: `python check_config.py`
4. **Restart server**: `python main_server.py`
5. **Clients tự động reconnect** (hoặc click "Kết nối lại")

**Thời gian**: ~30 giây

---

## 🎯 VÍ DỤ CỤ THỂ CHO DEMO

### **Demo 1: iPhone (2 phút)**
```json
{
  "item_name": "iPhone 15 Pro Max 256GB Titan Blue",
  "starting_price": 10000,
  "auction_duration": 120,
  "description": "Hang chinh hang Apple, bao hanh 12 thang"
}
```

### **Demo 2: PS5 (3 phút)**
```json
{
  "item_name": "PlayStation 5 Console + 2 Controllers",
  "starting_price": 5000,
  "auction_duration": 180,
  "description": "Kem 5 game AAA: Spider-Man, God of War, Horizon..."
}
```

### **Demo 3: Test nhanh (30 giây)**
```json
{
  "item_name": "Demo Test Item",
  "starting_price": 100,
  "auction_duration": 30,
  "description": "Test chuc nang nhanh"
}
```

---

## 🚨 LƯU Ý QUAN TRỌNG

### ✅ **Nên làm**
- Luôn chạy `check_config.py` trước khi demo
- Tránh tiếng Việt có dấu (dùng không dấu)
- Test với duration ngắn (30-60s) trước
- Có backup config (copy sang file khác)

### ❌ **Không nên**
- Sửa config khi server đang chạy (phải restart)
- Dùng giá trị âm hoặc 0
- Duration < 10 giây (quá ngắn)
- Quên kiểm tra JSON syntax

---

## 📞 TROUBLESHOOTING

**Q: Sửa config nhưng server vẫn dùng config cũ?**
→ Phải restart server (Ctrl+C rồi chạy lại)

**Q: JSON bị lỗi syntax?**
→ Chạy: `python -m json.tool auction_config.json`
→ Xem dòng nào lỗi, sửa lại (thiếu dấu phẩy, ngoặc, v.v.)

**Q: UI không hiển thị item name đúng?**
→ Check WELCOME message trong log server
→ Check client có nhận được message không

**Q: Muốn test nhanh không cần sửa file?**
→ Dùng command line:
```bash
python main_server.py --item "Test" --price 100 --duration 30
```