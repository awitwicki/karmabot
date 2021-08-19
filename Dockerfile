FROM python:buster
WORKDIR /app
COPY ./app/. .
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["main.py"]