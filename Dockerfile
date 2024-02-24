FROM python:3.12.2-slim-bookworm


ENV PYTHONYNBUFFERED 1
ENV APP_HOME /app

WORKDIR $APP_HOME
COPY ["atualizar_noticias.py", "requirements.txt", "./"]
COPY ["sites", "./sites"]

RUN pip install -r requirements.txt

CMD ["python", "atualizar_noticias.py"]