# Sử dụng Python 3.11 Slim để tiết kiệm dung lượng
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# copy requirements.txt trước để tận dụng Docker Cache
COPY requirements.txt .

# Cài đặt các thư viện phụ thuộc
# Thêm --no-cache-dir để giảm kích thước image
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container
COPY . .

# Expose port 8000
EXPOSE 8000

# Thiết lập user non-root để tăng cường bảo mật
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Lệnh chạy ứng dụng
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
