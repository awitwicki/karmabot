# karmabot
Telegram KarmaBot with chat management
Based on Aiogram
## Install
Fill tour telegram token in `config.ini` file

## Run
### Docker

```
docker build -t karmabot .
docker run --name=karmabot -v `pwd`:/app/data -d karmabot:latest
```

### Python

```
cd app/
pip3 install -r requirements.txt
python main.py
```
