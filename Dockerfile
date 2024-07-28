FROM python:3.12

WORKDIR /flask_v2

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY  flask_v2/ ./

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000"]
