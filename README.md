# PyTypo

Your Telegram bot that helps find typos in other Github repositories (in ReadMe file) and can create Pull requests with
a fix.

## How to run

- Create a [Telegram Bot](https://core.telegram.org/bots)
- Generate your [Github token](https://github.com/settings/tokens)
- Clone the repo
```bash
git clone https://github.com/erjanmx/pyTypo.git
```
- Create a virtual environment and install the dependencies 
```bash
pip install -r requirements.txt
```
- Copy vars to .env file and update its content accordingly
```bash
cp .env.example .env 
```
- Run the script
```bash
python main.py
```
- Send `/start` command to your Telegram bot.

## Development

### Source code formatting

```bash
pip install -r requirements-dev.txt

isort --profile black src/ tests/ main.py && black src/ tests/ main.py
```

### Running the tests
```bash
python -m unittest discover tests/
```
