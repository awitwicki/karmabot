# karmabot
Telegram KarmaBot with chat management
Based on Aiogram
## Install

Use next environment variables:

* `KARMABOT_TELEGRAM_TOKEN={YOUR_TOKEN}` - telegram token

    (other variables is not necessarty and have default values)

* `KARMABOT_FLOOD_TIMEOUT=10` - cooldown to allow +- karma per chat, default 30 seconds
* `KARMABOT_DELETE_TIMEOUT=30` - time before bot messages being deleted
* `KARMABOT_DATABASE_FILENAME=karmabot_db.json` - stored database name
* `KARMABOT_ALLOWED_CHATS=-10010101,-10000101010` - whitelist chats. If it empty or not added to envs, whitelist mode will be turned off.

**Python:** Add to system environment that variables.

**Docker compose:**  create `.env` file and fill it with that variables.

## Run

### Docker compose

Then run in console command:

```
docker-compose up -d
```

### Python

```
cd app/
pip3 install -r requirements.txt
python main.py
```
