import datetime
import logging
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    RegexHandler,
    Updater,
)
from tinydb import Query, TinyDB

from src.action import Action
from src.client import Client
from src.typo import Typo

logger = logging.getLogger(__name__)


class Bot:
    look_date = None
    repo_generator = None

    def get_inline_keyboard(self, typo: Typo):
        def a(action, typo):
            return f"{action}|{typo.repository}|{typo.word}|{typo.suggested}"

        keyboard = [
            [
                InlineKeyboardButton("Skip", callback_data=a(Action.SKIP_WORD, typo)),
                InlineKeyboardButton(
                    "Skip repo", callback_data=a(Action.SKIP_REPO, typo)
                ),
                InlineKeyboardButton(
                    "Ignore", callback_data=a(Action.IGNORE_WORD, typo)
                ),
            ],
            [
                # InlineKeyboardButton("Approve", callback_data='ap-typo|necreas1ng/VLANPWN|Specity|Specify')
                InlineKeyboardButton(
                    "Approve", callback_data=a(Action.APPROVE_REPO, typo)
                )
            ],
        ]
        print(a(Action.APPROVE_REPO, typo))
        return InlineKeyboardMarkup(keyboard)

    def get_inline_keyboard2(self, typo: Typo):
        def a(action, typo):
            return f"{action}|{typo.repository}|{typo.word}|{typo.suggested}"

        keyboard = [
            [
                InlineKeyboardButton(
                    "Close PR", callback_data=a(Action.CLOSE_PULL_REQUEST, typo)
                ),
                InlineKeyboardButton(
                    "Delete fork", callback_data=a(Action.DELETE_FORK, typo)
                ),
                InlineKeyboardButton(
                    "Ignore", callback_data=a(Action.IGNORE_WORD, typo)
                ),
            ],
            [InlineKeyboardButton("Browse PR", url=typo.pull_request.html_url)],
        ]
        return InlineKeyboardMarkup(keyboard)

    def __init__(self, token: str, chat_id: int, client: Client):
        self.updater = Updater(token)
        self.client = client
        self.chat_id = chat_id
        self.init_handlers()

    def handler_start(self, update: Update, context: CallbackContext):
        self.look_date = datetime.datetime.now() - datetime.timedelta(days=9)

        self.repo_generator = self.client.get_repo_typo(
            self.look_date.strftime("%Y-%m-%d")
        )
        self.send_next_candidate(context.bot)

    def handler_callback(self, update, context):
        try:
            self.handler_callback2(update, context)
        except Exception as e:
            logger.exception(e)

    def handler_callback2(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query_data = query.data

        message_id = query.message.message_id

        action, repository, word, suggested = query_data.split("|")

        typo = Typo(repository=repository, word=word, suggested=suggested)

        if action == Action.APPROVE_REPO:
            self.client.approve(typo)

            context.bot.edit_message_reply_markup(
                chat_id=self.chat_id,
                message_id=query.message.message_id,
                reply_markup=None,
            )
            message_id = None

        if self.repo_generator is None:
            self.look_date = datetime.datetime.now() - datetime.timedelta(days=8)
            self.repo_generator = self.client.get_repo_typo(
                self.look_date.strftime("%Y-%m-%d")
            )
            self.send_next_candidate(context.bot, message_id=message_id)
            return

        self.repo_generator.send(action)
        context.bot.answer_callback_query(callback_query_id=query.id, text=action)
        self.send_next_candidate(context.bot, message_id)

    @staticmethod
    def handler_error(update: Update, context: CallbackContext):
        logger.error('Update "%s" caused error "%s"', update, context.error)

    def send_next_candidate(self, bot, message_id=None):
        try:
            typo = next(self.repo_generator)

            context_head, context_tail = typo.get_context()

            context = f"{context_head} *{typo.word}* {context_tail}".strip()

            count = typo.readme.count(typo.word)

            key_markup = self.get_inline_keyboard(typo)
            text = (
                "{}\n\nhttps://github.com/{}\n\n{} ➡️ {} ({})\n\n<pre>{}</pre>".format(
                    self.look_date.strftime("%Y-%m-%d"),
                    typo.repository,
                    typo.word,
                    typo.suggested,
                    count,
                    context,
                )
            )

        except StopIteration:
            self.look_date -= datetime.timedelta(days=1)
            self.repo_generator = self.client.get_repo_typo(
                self.look_date.strftime("%Y-%m-%d")
            )
            self.send_next_candidate(bot, message_id)
            return

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
        dp = self.updater.dispatcher

        dp.add_handler(CommandHandler("start", self.handler_start))
        dp.add_handler(CallbackQueryHandler(self.handler_callback))
        dp.add_error_handler(self.handler_error)
        # dp.add_handler(CommandHandler("start", start, filters=Filters.user(user_id=TELEGRAM_USER_ID)))
        # dp.add_handler(RegexHandler(r'([\d]{4}-[\d]{2}-[\d]{2})', for_date, pass_groups=True))

    def start_polling(self):
        self.updater.start_polling()
        self.updater.idle()

    def handle_action(self, action, typo):
        pass
