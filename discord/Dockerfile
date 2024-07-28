FROM python:3.12

WORKDIR /discord
COPY bot.py ./

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY .env ./

CMD ["python", "bot.py"]