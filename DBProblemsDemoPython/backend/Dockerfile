FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install debugging tools
RUN apt-get update && apt-get install -y curl net-tools iputils-ping && apt-get clean

COPY . .

EXPOSE 5001

CMD ["python", "app.py"]