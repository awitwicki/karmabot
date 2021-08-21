# karmabot
Telegram KarmaBot with chat management
Based on Aiogram
## Install
Fill tour telegram token in `config.ini` file

## Run
### Docker

```
docker build -t karmabot .

docker run --name=karmabot --env KARMABOT_TELEGRAM_TOKEN={telegram token} --env KARMABOT_FLOOD_TIMEOUT=10 --env KARMABOT_DELETE_TIMEOUT=30 --env KARMABOT_DATABASE_FILENAME=db.json -v `pwd`:/app/data -d karmabot:latest
```

* `KARMABOT_TELEGRAM_TOKEN` - telegram token
* `KARMABOT_FLOOD_TIMEOUT` - cooldown to allow +- karma per chat
* `KARMABOT_DELETE_TIMEOUT` - time before bot messages being deleted
* `KARMABOT_DATABASE_FILENAME` - stored database name

* `-v 'pwd':/app/data` - mount volume to store database on host directory, instead `'pwd'` you can set absolute path

### Python

```
cd app/
pip3 install -r requirements.txt
python main.py
```
