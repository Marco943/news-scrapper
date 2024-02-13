FROM python:3.10.13

ENV PYTHONYNBUFFERED 1
ENV APP_HOME /app

WORKDIR $APP_HOME
COPY ["atualizar_noticias.py", "db.py", "sites_sync.py", "requirements.txt", "./"]

RUN pip install -r requirements.txt

CMD ["python", "atualizar_noticias.py"]