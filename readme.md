# 🔫 Hand Gun Battle - AI Computer Vision Game

> Trò chơi bắn súng tương tác thực tế ảo (AR) sử dụng cử chỉ tay, được xây dựng bằng Python, OpenCV và Google Mediapipe.

![Python](https://img.shields.io/badge/Python-3.13%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green)
![Mediapipe](https://img.shields.io/badge/Mediapipe-Hand%20Tracking-orange)

## 🎮 Giới thiệu

**Hand Gun Battle** biến webcam của bạn thành một trò chơi bắn súng. Không cần chuột hay bàn phím, bạn sử dụng chính đôi tay của mình để ngắm và bắn các mục tiêu trên màn hình.

Game được tối ưu hóa với thuật toán làm mượt (smoothing) giúp tâm ngắm di chuyển ổn định, không bị rung lắc, cùng với chế độ chia đôi màn hình (Split-screen) để 2 người có thể thi đấu trực tiếp.

## ✨ Tính năng nổi bật

* **Điều khiển bằng cử chỉ:**
    * 👆 **Ngón trỏ:** Di chuyển tâm ngắm.
    * 👍 **Gập ngón cái:** Bóp cò bắn.
* **Chế độ chơi đa dạng:**
    * 🏆 **Endless Mode (1 Người):** Luyện tập bắn tự do, tích điểm.
    * ⚔️ **Battle Mode (2 Người):** Màn hình chia đôi, mỗi người bảo vệ một nửa sân, đua điểm trong 60 giây.
* **Smart UX:**
    * **Aim Smoothing:** Giúp tâm ngắm "lướt" mượt mà, giảm độ trễ và rung.
    * **Camera Phụ:** Hiển thị khung xương tay thời gian thực ở góc dưới màn hình.
    * **Anti-Overlap:** Mục tiêu không bao giờ xuất hiện ở khu vực bị camera che khuất.

## 🛠️ Cài đặt và Chạy game

Dự án này khuyến khích sử dụng môi trường ảo (`venv`).

### Bước 1: Clone dự án
```bash
git clone https://github.com/kien17/GUNCAM.git
cd gunCam
```
### Bước 2: Thiết lập môi trường ảo
#### Tạo venv
```bash
python -m venv venv
```

#### Kích hoạt venv
##### Trên Windows:
```bash
.\venv\Scripts\activate
```
##### Trên macOS/Linux:
```bash
source venv/bin/activate
```

### Bước 3: Cài đặt thư viện
```bash
python -m pip install -r requirements.txt
```

### Bước 4: Khởi chạy chương trình
```bash
python gunCam.py
```

## 🎮 Hướng dẫn chơi

### ⌨️ Các phím tắt (Keyboard Shortcuts)

| Phím | Chức năng |
|----|----------|
| **1** | Chế độ Endless (1 Người) |
| **2** | Chế độ Battle (2 Người) |
| **M** | Quay về Menu chính (khi ở màn hình kết quả) |
| **Q** | Thoát game |

---

### ✋ Cách điều khiển bằng tay

- Đưa tay lên trước camera (**khoảng cách 0.5m – 1m**)
- Sử dụng **ngón trỏ** để di chuyển tâm ngắm **(+)** đến mục tiêu 🔴
- **Gập nhanh ngón cái vào lòng bàn tay** để bắn

🔹 **Chế độ 2 người**:
- Người chơi **thứ nhất** điều khiển màn hình **bên trái**
- Người chơi **thứ hai** điều khiển màn hình **bên phải**

---

## 📂 Cấu trúc dự án
```bash
GUNCAM/
├── gunCam.py # Source code chính
├── hand_landmarker.task # Model AI (Model chính dùng cho nhận diện tay lấy từ google)
├── requirements.txt # Danh sách thư viện
└── README.md # Tài liệu hướng dẫn
```