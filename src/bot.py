import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    Updater,
)

from src.action import Action
from src.repo_readme_typo import RepoReadmeTypo
from src.typo_client import TypoClient

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, token: str, chat_id: int, client: TypoClient):
        self.client = client
        self.chat_id = chat_id
        self.updater = Updater(token)

    def handler_start(self, update: Update, context: CallbackContext):
        self.client.reset_look_date()
        self.send_next_candidate(context.bot)

    def handler_callback(self, update, context):
        try:
            self.query_callback(update, context)
        except Exception as e:
            logger.exception(e)
            self.client.lower_look_date()
            self.send_next_candidate(context.bot)

    def query_callback(self, update: Update, context: CallbackContext):
        query = update.callback_query
        message_id = query.message.message_id

        callback_response_text = "Skipped"

        # extract data from query
        action, repository, maybe_typo, suggested = query.data.split("|")

        if action == Action.DELETE_FORK:
            self.client.delete_fork_repository(repository)
            context.bot.answer_callback_query(
                callback_query_id=query.id, text="Fork deleted"
            )
            return

        elif action == Action.IGNORE_WORD:
            callback_response_text = "Ignored"
            self.client.add_to_ignored(maybe_typo)

        elif action == Action.APPROVE_REPO:
            typo = RepoReadmeTypo(
                repository=repository, word=maybe_typo, suggested=suggested
            )
            pull_request = self.client.create_pull_request_with_fix(typo)
            self.client.add_to_approved(typo)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "Close PR",
                        callback_data=self.build_callback_button_data(
                            Action.DELETE_FORK, typo
                        ),
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
        except (AttributeError, TypeError, StopIteration):
            pass

        self.send_next_candidate(context.bot, message_id)

        try:
            context.bot.answer_callback_query(
                callback_query_id=query.id, text=callback_response_text
            )
        except BadRequest:
            pass

    def send_next_candidate(self, bot, message_id=None):
        self.client.init_generator()

        try:
            typo = next(self.client.repo_generator)
        except StopIteration:
            self.client.lower_look_date()
            self.send_next_candidate(bot, message_id)
            return

        context = typo.get_typo_with_context()

        text = (
            f"{self.client.get_date()}\n\n"
            f"{self.client.github.get_repo_link(typo.repository)}\n\n"
            f"{typo.maybe_typo} ➡ {typo.suggested_word} ({typo.get_word_readme_occurrence_count()})\n\n"
            f'<a href="{self.client.github.get_repo_link_with_context(typo.repository, context)}">'
            f"{context.replace(typo.maybe_typo, f'<b><u>{typo.maybe_typo}</u></b>')}</a>"
        )  # Android client can't render urls with "underline" format, so adding "bold" as well

        keyboard = [
            [
                InlineKeyboardButton(
                    "Skip",
                    callback_data=self.build_callback_button_data(
                        Action.SKIP_WORD, typo
                    ),
                ),
                InlineKeyboardButton(
                    "Skip repo",
                    callback_data=self.build_callback_button_data(
                        Action.SKIP_REPO, typo
                    ),
                ),
                InlineKeyboardButton(
                    "Ignore",
                    callback_data=self.build_callback_button_data(
                        Action.IGNORE_WORD, typo
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "Approve",
                    callback_data=self.build_callback_button_data(
                        Action.APPROVE_REPO, typo
                    ),
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
            try:
                bot.edit_message_text(message_id=message_id, **kwargs)
            except BadRequest:
                logger.exception("Edit message exception")
                self.send_next_candidate(bot, message_id)

    def delete_forks_with_closed_pull_requests(self, context):
        """
        Runs periodically and deletes all forks with closed PRs

        :param context:
        :return:
        """
        self.client.delete_forks_with_closed_pull_requests()

    def init_handlers(self):
        """
        Initialize bot command handlers

        :return:
        """
        dispatcher = self.updater.dispatcher

        dispatcher.add_handler(
            CommandHandler(
                "start", self.handler_start, filters=Filters.user(user_id=self.chat_id)
            )
        )
        dispatcher.add_handler(CallbackQueryHandler(self.handler_callback))
        dispatcher.add_error_handler(self.handler_error)

    def start_polling(self):
        """
        Start telegram bot polling

        :return:
        """
        self.init_handlers()
        self.updater.start_polling()

        self.updater.job_queue.run_repeating(
            callback=self.delete_forks_with_closed_pull_requests,
            first=60,  # first run after a minute
            interval=60 * 60 * 24,  # run daily
        )

        self.updater.idle()

    @staticmethod
    def build_callback_button_data(action: str, typo: RepoReadmeTypo):
        """
        Build button input text data

        :param action: str
        :param typo: RepoReadmeTypo
        :return: str
        """
        return f"{action}|{typo.repository}|{typo.maybe_typo}|{typo.suggested_word}"

    @staticmethod
    def handler_error(update: Update, context: CallbackContext):
        logger.error('Update "%s" caused error "%s"', update, context.error)
