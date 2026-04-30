# Dùng image Python nhẹ gọn
FROM python:3.11-slim

# BƯỚC 1: Đặt thư mục làm việc (Lúc này mặc định vẫn đang là quyền root cao nhất)
WORKDIR /app

# BƯỚC 3: Tạo user và cấp toàn quyền sở hữu thư mục /app cho user này
RUN useradd -m -u 1000 user
RUN chown -R user:user /app

# BƯỚC 4: Chuyển sang user thường để bảo mật (Bắt buộc của HF Spaces)
USER user
ENV PATH="/home/user/.local/bin:$PATH"
ENV PYTHONPATH="/app"

# BƯỚC 5: Copy file và cài đặt thư viện
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# BƯỚC 6: Copy toàn bộ source code của bạn vào
COPY --chown=user . /app

# Expose port 7860
EXPOSE 7860

# Lệnh chạy Chainlit
CMD ["bash", "-c", "bash scripts/setup.sh && bash scripts/run.sh"]