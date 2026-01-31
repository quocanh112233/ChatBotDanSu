# ChatBot Dân Sự - Trợ Lý Luật Sư Ảo

Dự án ChatBot tư vấn pháp luật chuyên sâu về **Bộ Luật Dân Sự 2015** của Việt Nam. Hệ thống sử dụng công nghệ RAG (Retrieval-Augmented Generation) kết hợp với mô hình ngôn ngữ lớn (LLM) chạy cục bộ (**Qwen 2.5**) để đảm bảo tính riêng tư và bảo mật dữ liệu.

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20|%20React%20|%20Ollama%20|%20PostgreSQL-blue)

---

## Tính Năng Nổi Bật

- **Tra cứu luật chính xác:** Sử dụng tìm kiếm Vector (Semantic Search) để tìm đúng điều luật liên quan.
- **Hoạt động Offline 100%:** Sử dụng Ollama chạy Local LLM, không gửi dữ liệu ra ngoài Internet.
- **Bảo mật dữ liệu:**
  - "Niêm phong" dữ liệu gốc bằng SHA-256 Hash.
  - Chống DDoS (Rate Limiting).
- **Trải nghiệm mượt mà:** Chế độ trả lời Streaming (gõ chữ thời gian thực).
- **Giao diện hiện đại:** ReactJS + TailwindCSS.

---

## Yêu Cầu Hệ Thống

- **OS:** Windows / Linux / macOS.
- **RAM:** Tối thiểu 8GB (Khuyến nghị 16GB).
- **Phần mềm cần cài đặt:**
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Khuyến nghị dùng Docker để chạy nhanh nhất).
  - [Ollama](https://ollama.com/) (Bắt buộc để chạy AI).

---

## Hướng Dẫn Cài Đặt (Khuyên Dùng Docker)

### Bước 1: Chuẩn Bị AI (Ollama)
Cài đặt Ollama và tải model Qwen 2.5 (3B parameters):
```bash
ollama pull qwen2.5:3b
```
Đảm bảo Ollama đang chạy ở background.

### Bước 2: Cấu Hình
Copy file cấu hình mẫu:
```bash
cd backend
cp .env.example .env
```
Mở file `.env` và cập nhật các thông số nếu cần (mặc định đã cấu hình sẵn để chạy local).

### Bước 3: Khởi Động Hệ Thống
Tại thư mục gốc của dự án:
```bash
docker-compose up --build
```
Lần đầu chạy sẽ mất vài phút để build image.

Sau khi chạy xong, truy cập các địa chỉ sau:
- **Frontend (Web App):** http://localhost:5173
- **Backend (API Docs):** http://localhost:3000/docs
- **Database (Postgres):** Port 5433

---

## Hướng Dẫn Nạp Dữ Liệu (Lần Đầu)

Khi mới khởi động, Database sẽ rỗng. Bạn cần chạy lệnh sau để nạp dữ liệu từ file PDF vào Database (Chỉ cần làm 1 lần).

**Cách 1: Chạy trong Docker Container (Nếu đang dùng Docker)**
```bash
# Vào container backend
docker exec -it chatbot_backend bash

# Chạy lệnh nạp dữ liệu
python -m app.script.ingest_to_db
```

**Cách 2: Chạy thủ công (Nếu chạy bằng Python venv)**
```bash
cd backend
# Kích hoạt venv
source venv/bin/activate  # Hoặc venv\Scripts\activate trên Windows
# Chạy lệnh
python -m app.script.ingest_to_db
```

---

## Cơ Chế Bảo Mật

1. **Niêm Phong Dữ Liệu:**
   Hệ thống tự động kiểm tra mã Hash SHA-256 của file `LuatDanSu2015.pdf` mỗi khi import. Nếu file bị thay đổi trái phép, quá trình import sẽ bị chặn lại.
   Mã Hash chuẩn được lưu trong `.env` (`DATA_INTEGRITY_HASH`).

2. **Chống Spam (Rate Limit):**
   Mỗi IP chỉ được phép đặt tối đa **5 câu hỏi / phút**.

---

## Hướng Dẫn Chạy Thủ Công (Dành Cho Dev)

Nếu muốn phát triển (Code), bạn nên chạy từng phần riêng lẻ:

**1. Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**2. Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Liên Hệ
Dự án được phát triển bởi [Trần Nguyễn Quốc Anh].
Mọi đóng góp xin gửi về [Email: trannguyenquocanh2004@gmail.com].
