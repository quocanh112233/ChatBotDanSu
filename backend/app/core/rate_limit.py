from slowapi import Limiter
from slowapi.util import get_remote_address

# Khởi tạo Limiter, sử dụng địa chỉ IP của client để định danh (key_func)
limiter = Limiter(key_func=get_remote_address)
