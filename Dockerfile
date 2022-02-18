FROM python:3.8

WORKDIR /app

COPY . .

VOLUME /app/build/static/data

RUN pip install -r requirements.txt

CMD ["python", "server.py"]

EXPOSE 5005