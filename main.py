import logging
import os

from dotenv import load_dotenv

from src.bot import Bot
from src.client import Client
from src.database import TinyDBProvider
from src.github_client import GithubClient

load_dotenv()

DB_PATH = os.getenv("DB_PATH")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_USER_ID = int(os.getenv("TELEGRAM_USER_ID"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():
    client = Client(github=GithubClient(GITHUB_TOKEN), database=TinyDBProvider(DB_PATH))
    bot = Bot(TELEGRAM_TOKEN, chat_id=TELEGRAM_USER_ID, client=client)
    bot.start_polling()


if __name__ == "__main__":
    main()
