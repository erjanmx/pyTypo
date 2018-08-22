import re
import base64
import logging

from github import GitHub
from autocorrect import spell
from tinydb import TinyDB, Query
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, Filters

GITHUB_TOKEN = ''
TELEGRAM_TOKEN = ''
TELEGRAM_USER_ID = 0

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

gh = GitHub(GITHUB_TOKEN)
db = TinyDB('db.json')

keyboard = [
    [
        InlineKeyboardButton("Skip", callback_data='skip'),
        InlineKeyboardButton("Skip repo", callback_data='skip-repo'),
        InlineKeyboardButton("Ignore", callback_data='ignore'),
    ],
    [
        InlineKeyboardButton("Approve", callback_data='approve')
    ]
]
reply_markup = InlineKeyboardMarkup(keyboard)

last = dict()
repo_gen = None
skip_repo = False


def get_a_repo(date):
    global skip_repo
    query = Query()

    populars = ['louisdh/source-editor', 'threepointone/css-suspense', 'Think-Silicon/GLOVE', 'LLZUPUP/vue-fallowFish', 'hihayk/scale', 'lizixian18/EasyMvp', 'PortSwigger/param-miner', 'zaptst/zap', 'obiwankenoobi/react-express-boilerplate', 'aichinateam/chinese-ai-developer', 'vinyldns/vinyldns', '22bulbs/brom', 'sootlasten/disentangled-representation-papers', 'rodeofx/OpenWalter', 'TheOfficialFloW/VitaTweaks', 'wjpdeveloper/my-action-github', 'AlexanderEllis/js-reading-list', 'skeeto/hash-prospector', 'sarah21cn/BlockChainTechnology', 'matrixgardener/AlgorithmCode', 'CompVis/adaptive-style-transfer', 'hamlim/inline-mdx.macro', 'prakashdanish/vim-githubinator', 'nacos-group/nacos-spring-project', 'mattatz/UNN', 'pldmgg/WinAdminCenterPS', 'wujunze/dingtalk-exception', 'cuixiaorui/cReptile', 'renjianan/initiator', 'codrops/MotionRevealSlideshow']
    populars = ['zaptst/zap']
    # gh.get_popular_repos_for_date(date)
    for repo in populars:
        readme = gh.get_readme(repo)
        content = str(base64.b64decode(str(readme['content']).replace('\\n', '')))
        print(content)
        # get unique list of alphabetical words with length more then 4 symbols
        words = set(filter(lambda w: re.search('^[a-zA-Z]{4,}$', w) is not None, content.split()))
        for word in words:
            if skip_repo:
                break

            suggested = spell(word)
            if suggested == word:
                continue

            # search in ignore list
            if db.search(query.word == word):
                continue

            yield repo, readme, word, suggested
        skip_repo = False


def add_to_ignore_list(word):
    db.insert({'word': word})


def send_next(bot, message_id=None):
    global last, repo_gen

    repo, readme, typo, suggested = next(repo_gen)
    last = {'repo': repo, 'readme': readme, 'typo': typo, 'suggested': suggested}

    text = 'https://github.com/{}\n\n{} - {}'.format(repo, typo, suggested)

    if message_id is None:
        bot.send_message(chat_id=TELEGRAM_USER_ID, text=text, reply_markup=reply_markup, disable_web_page_preview=True)
    else:
        bot.edit_message_text(chat_id=TELEGRAM_USER_ID, message_id=message_id, text=text, reply_markup=reply_markup,
                              disable_web_page_preview=True)


def start(bot, update):
    global repo_gen
    repo_gen = get_a_repo('2018-07-26')
    send_next(bot)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def action(bot, update):
    global skip_repo
    query = update.callback_query

    q_data = query.data

    if q_data == 'skip-repo':
        # skip the current repo
        skip_repo = True
    elif q_data == 'ignore':
        # add this word to ignore list
        add_to_ignore_list(last['typo'])
    elif q_data == 'approve':
        # print(gh.fork_repo(last['repo']).content)

        # readme = last['readme']['content']
        content = str(base64.b64decode(str(last['readme']['content']).replace('\\n', '')))
        modified_readme = content.replace(last['typo'], last['suggested'])
        gh.update_file('erjanmx/zap', content=modified_readme)
        # open pr
        print('approving')

    bot.answer_callback_query(callback_query_id=query.id)
    send_next(bot, message_id=query.message.message_id)


def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start, filters=Filters.user(user_id=TELEGRAM_USER_ID)))

    dp.add_handler(CallbackQueryHandler(action))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':

    # print(gh.get_readme('zaptst/zap'))

    # bot = Bot(TELEGRAM_TOKEN)
    # text = 'https://github.com/{}\n\n{} - {}'.format('louisdh/source-editor', 'typo', 'suggested')
    # bot.send_message(chat_id=TELEGRAM_USER_ID, text=text, disable_web_page_preview=True, reply_markup=reply_markup)
    main()
