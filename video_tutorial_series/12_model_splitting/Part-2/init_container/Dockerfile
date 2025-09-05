FROM python:latest

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt


COPY . /app

WORKDIR /app
ENTRYPOINT ["python3", "main.py"]