# Build Stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package.json và package-lock.json (nếu có)
COPY package*.json ./

# Cài đặt dependencies
RUN npm install

# Copy source code
COPY . .

# Build production
RUN npm run build

# Serve Stage (Sử dụng Nginx siêu nhẹ)
FROM nginx:alpine

# Copy file build từ stage trước vào thư mục serve của Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copy file cấu hình Nginx (nếu cần custom, ở đây dùng mặc định kèm fix cho React Router)
# Tạo file nginx.conf tạm thời để handle React Router (F5 trang không bị 404)
RUN echo 'server { \
    listen 80; \
    location / { \
    root /usr/share/nginx/html; \
    index index.html index.htm; \
    try_files $uri $uri/ /index.html; \
    \
    # Security Headers \
    add_header X-Frame-Options "SAMEORIGIN" always; \
    add_header X-Content-Type-Options "nosniff" always; \
    add_header Referrer-Policy "strict-origin-when-cross-origin" always; \
    } \
    }' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
