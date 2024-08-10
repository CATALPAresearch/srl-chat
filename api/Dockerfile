FROM python:3.12

WORKDIR /api

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY  . .

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000"]
