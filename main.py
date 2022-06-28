import json
import logging
import os

from dotenv import load_dotenv

from src.bot import Bot
from src.database import TinyDBProvider
from src.github_client import GithubClient
from src.typo_detector import TypoDetector
from src.typo_client import TypoClient
from autocorrect import Speller

load_dotenv()

DB_PATH = os.getenv("DB_PATH")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_USER_ID = int(os.getenv("TELEGRAM_USER_ID"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=LOGGING_LEVEL
)

logger = logging.getLogger(__name__)


def main():
    # custom words data for autocorrect.Speller
    with open('data/word_count.json') as file:
        speller = Speller(nlp_data=json.load(file))

    client = TypoClient(
        github=GithubClient(GITHUB_TOKEN), database=TinyDBProvider(DB_PATH), typo_detector=TypoDetector(speller)
    )
    bot = Bot(TELEGRAM_TOKEN, chat_id=TELEGRAM_USER_ID, client=client)
    bot.start_polling()


if __name__ == "__main__":
    main()
