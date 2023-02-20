FROM python:3.10-alpine
COPY ./db/character.db /var/www/character.db
COPY ./db/genshinVoice.db /var/www/genshinVoice.db
COPY ./requirements.txt /var/www/requirements.txt
COPY ./app.py /var/www/app.py
COPY ./config.py /var/www/config.py
COPY ./run.py /var/www/run.py

RUN pip install -r /var/www/requirements.txt
ENTRYPOINT ["python", "/var/www/run.py"]
EXPOSE 8000
