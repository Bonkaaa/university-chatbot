# Dùng image Python nhẹ gọn
FROM python:3.11-slim

# HF Spaces yêu cầu chạy dưới quyền user thông thường để bảo mật (không dùng root)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Đặt thư mục làm việc bên trong máy chủ
WORKDIR /app

# Copy file requirements và cài đặt thư viện
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code của bạn vào
COPY --chown=user . /app

# Expose port 7860 (Đây là port bắt buộc mà HF Spaces quy định)
EXPOSE 7860

# Lệnh chạy Chainlit, trỏ đúng vào file main.py của bạn
CMD ["chainlit", "run", "src/main.py", "-w", "--port", "7860", "--host", "0.0.0.0"]