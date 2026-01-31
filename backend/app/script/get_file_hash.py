
import hashlib
import os

def calculate_file_hash(file_path):
    print(f"File path: {file_path}")
    if not os.path.exists(file_path):
        print("File không tồn tại!")
        return None
        
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Đọc file theo chunk để tránh tốn RAM
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

if __name__ == "__main__":
    # Đường dẫn hardcode tới file PDF
    # app/script -> app -> backend
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    target_file = os.path.join(BASE_DIR, "data", "raw", "LuatDanSu2015.pdf")
    
    file_hash = calculate_file_hash(target_file)
    if file_hash:
        print(f"SHA-256 Hash: {file_hash}")
        print("--- Hãy copy chuỗi này vào cấu hình bảo mật ---")
