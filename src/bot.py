import datetime
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


def get_inline_keyboard(typo: Typo):
    def build_callback_data(action, typo: Typo):
        return f"{action}|{typo.repository}|{typo.word}|{typo.suggested}"

    keyboard = [
        [
            InlineKeyboardButton("Skip", callback_data=build_callback_data(Action.SKIP_WORD, typo)),
            InlineKeyboardButton("Skip repo", callback_data=build_callback_data(Action.SKIP_REPO, typo)),
            InlineKeyboardButton("Ignore", callback_data=build_callback_data(Action.IGNORE_WORD, typo)),
        ], [
            InlineKeyboardButton("Approve", callback_data=build_callback_data(Action.APPROVE_REPO, typo))
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


class Bot:
    # look_date = None
    # repo_generator = None

    def __init__(self, token: str, chat_id: int, client: Client):
        self.client = client
        self.chat_id = chat_id
        self.updater = Updater(token)

    def handler_start(self, update: Update, context: CallbackContext):
        self.client.init()
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

        action, repository, word, suggested = query.data.split("|")

        typo = Typo(repository=repository, word=word, suggested=suggested)

        if action == Action.APPROVE_REPO:
            self.client.approve_typo(typo)

            context.bot.edit_message_reply_markup(
                chat_id=self.chat_id,
                message_id=query.message.message_id,
                reply_markup=None,
            )
            message_id = None

        context.bot.answer_callback_query(callback_query_id=query.id, text=action, show_alert=True)
        self.client.repo_generator.send(action)
        self.send_next_candidate(context.bot, message_id)

    def send_next_candidate(self, bot, message_id=None):
        try:
            typo = next(self.client.repo_generator)

            text = f'{self.client.get_date()}\n\n' \
                   f'{typo.get_repository_url()}\n\n' \
                   f'{typo.word} ➡ {typo.suggested} ({typo.get_count()})\n\n' \
                   f'<pre>{typo.get_context()}</pre>'

            key_markup = get_inline_keyboard(typo)
        except StopIteration:
            return
            # return self.handler_start()

        if message_id is None:
            bot.send_message(
                chat_id=self.chat_id,
                text=text,
                reply_markup=key_markup,
                disable_web_page_preview=True,
                parse_mode="HTML",
            )
        else:
            bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=message_id,
                text=text,
                reply_markup=key_markup,
                disable_web_page_preview=True,
                parse_mode="HTML",
            )

    def init_handlers(self):
        dispatcher = self.updater.dispatcher

        dispatcher.add_handler(CommandHandler("start", self.handler_start, filters=Filters.user(user_id=self.chat_id)))
        dispatcher.add_handler(CallbackQueryHandler(self.handler_callback))
        dispatcher.add_error_handler(self.handler_error)

    def start_polling(self):
        self.init_handlers()
        self.updater.start_polling()
        self.updater.idle()

    @staticmethod
    def handler_error(update: Update, context: CallbackContext):
        logger.error('Update "%s" caused error "%s"', update, context.error)
