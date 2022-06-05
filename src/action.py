from enum import Enum, unique


@unique
class Action(Enum):
    SKIP_WORD = "sk-word"
    SKIP_REPO = "sk-repo"
    IGNORE_WORD = "ig-word"
    APPROVE_REPO = "ap-typo"

    CLOSE_PULL_REQUEST = "cl-pull"
    BROWSE_PULL_REQUEST = "br-pull"
    DELETE_FORK = "dl-fork"
