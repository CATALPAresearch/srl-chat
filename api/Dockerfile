FROM python:3.12

WORKDIR /api

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY  . .
RUN cat ./certs/chat-impact-fernuni-hagen-de.pem >> /usr/local/lib/python3.12/site-packages/certifi/cacert.pem

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000"]
