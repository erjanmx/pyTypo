import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    Updater,
)

from src.action import Action
from src.client import Client
from src.typo import Typo

logger = logging.getLogger(__name__)


def build_callback_data(action, typo: Typo):
    return f"{action}|{typo.repository}|{typo.word}|{typo.suggested}"


class Bot:
    def __init__(self, token: str, chat_id: int, client: Client):
        self.client = client
        self.chat_id = chat_id
        self.updater = Updater(token)

    def handler_start(self, update: Update, context: CallbackContext):
        self.send_next_candidate(context.bot)

    def handler_callback(self, update, context):
        try:
            self.query_callback(update, context)
        except Exception as e:
            logger.exception(e)
            self.handler_start(update, context)

    def query_callback(self, update: Update, context: CallbackContext):
        query = update.callback_query
        message_id = query.message.message_id

        callback_response_text = "Skipped"

        # extract data from query
        action, repository, word, suggested = query.data.split("|")

        if action == Action.DELETE_FORK:
            self.client.delete_fork_repository(repository)
            context.bot.answer_callback_query(
                callback_query_id=query.id, text="Fork deleted"
            )
            return

        elif action == Action.IGNORE_WORD:
            callback_response_text = "Ignored"
            self.client.add_to_ignored(word)

        elif action == Action.APPROVE_REPO:
            typo = Typo(repository=repository, word=word, suggested=suggested)
            pull_request = self.client.create_pull_request_with_fix(typo)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "Close PR",
                        callback_data=build_callback_data(Action.DELETE_FORK, typo),
                    ),
                    InlineKeyboardButton(
                        "Browse PR", url=f"{pull_request.html_url}/files"
                    ),
                ],
            ]
            markup = InlineKeyboardMarkup(keyboard)

            context.bot.edit_message_reply_markup(
                chat_id=self.chat_id, message_id=message_id, reply_markup=markup
            )
            message_id = None
            callback_response_text = "Pull request created"

        try:
            self.client.repo_generator.send(action)
        except (AttributeError, TypeError):
            pass

        self.send_next_candidate(context.bot, message_id)

        context.bot.answer_callback_query(
            callback_query_id=query.id, text=callback_response_text
        )

    def send_next_candidate(self, bot, message_id=None):
        self.client.init()

        typo = next(self.client.repo_generator)

        text = (
            f"{self.client.get_date()}\n\n"
            f"{typo.get_repository_url()}\n\n"
            f"{typo.word} ➡ {typo.suggested} ({typo.get_count()})\n\n"
            f"<pre>{typo.get_context()}</pre>"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Skip", callback_data=build_callback_data(Action.SKIP_WORD, typo)
                ),
                InlineKeyboardButton(
                    "Skip repo",
                    callback_data=build_callback_data(Action.SKIP_REPO, typo),
                ),
                InlineKeyboardButton(
                    "Ignore",
                    callback_data=build_callback_data(Action.IGNORE_WORD, typo),
                ),
            ],
            [
                InlineKeyboardButton(
                    "Approve",
                    callback_data=build_callback_data(Action.APPROVE_REPO, typo),
                )
            ],
        ]

        kwargs = {
            "text": text,
            "chat_id": self.chat_id,
            "reply_markup": InlineKeyboardMarkup(keyboard),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if message_id is None:
            bot.send_message(**kwargs)
        else:
            bot.edit_message_text(message_id=message_id, **kwargs)

    def init_handlers(self):
        dispatcher = self.updater.dispatcher

        dispatcher.add_handler(
            CommandHandler(
                "start", self.handler_start, filters=Filters.user(user_id=self.chat_id)
            )
        )
        dispatcher.add_handler(CallbackQueryHandler(self.handler_callback))
        dispatcher.add_error_handler(self.handler_error)

    def start_polling(self):
        self.init_handlers()
        self.updater.start_polling()
        self.updater.idle()

    @staticmethod
    def handler_error(update: Update, context: CallbackContext):
        logger.error('Update "%s" caused error "%s"', update, context.error)
