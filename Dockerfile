FROM python:buster
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["main.py"]