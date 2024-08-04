FROM python:3.12

WORKDIR /flask_v2

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY  flask_v2/ ./
RUN mkdir /mnt/azure
RUN mv ./srl_chat.db /mnt/azure/

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000"]
