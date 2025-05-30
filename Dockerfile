FROM python:3.9

# 设置工作目录
WORKDIR /app

ENV TZ Asia/Shanghai

# 将requirements.txt文件复制到容器中
COPY requirements.txt .

# 安装Python依赖包
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用程序代码到容器中
COPY . .

CMD ["python3", "main.py"]