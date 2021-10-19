import time

from sqlalchemy import *
from sqlalchemy.orm import relationship
from files.__main__ import Base

CATEGORIES = (
    "Awards",
    "Abilities",
    "Features"
)


ITEMS = {
    "ban": {
        "kind": "ban",
        "name": "One-Day Ban Award",
        "description": "Award that bans the recipient for one day.",
        "category": 0,
        "icon": "",
        "cost": 5000,
        "ability": False,
        "award": True,
        "awardKind": "ban",
        "prompt": None
    },
    "shit": {
        "kind": "shit",
        "name": "Shitpost Award",
        "description": "Put flies on the post and humiliate OP for sperging out like that.",
        "category": 0,
        "icon": "",
        "cost": 500,
        "ability": False,
        "award": True,
        "awardKind": "shit",
        "prompt": None
    },
    "gold": {
        "kind": "gold",
        "name": "Gold Award",
        "description": "Consooooom rdrama gold",
        "category": 0,
        "icon": "",
        "cost": 750,
        "ability": False,
        "award": True,
        "awardKind": "gold",
        "prompt": None
    },
    "flair": {
        "kind": "flair",
        "name": "24hr Title Change",
        "description": "Change the target user's title to something of your choice for 24 hours.",
        "category": 1,
        "icon": "",
        "cost": 900,
        "ability": True,
        "award": False,
        "awardKind": None,
        "prompt": "What to change their flair to? (emojis allowed)"
    },
    "pin": {
        "kind": "pin",
        "name": "24hr Pin",
        "description": "Pin the target post or comment for 24 hours.",
        "category": 1,
        "icon": "",
        "cost": 500,
        "ability": True,
        "award": False,
        "awardKind": None,
        "prompt": None
    }
}


class ShopItem(Base):

    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    kind = Column(String)

    user = relationship("User", primaryjoin="ShopItem.user_id == User.id", uselist=False, lazy="joined")

    @property
    def type(self):
        return ITEMS[self.kind]

    @property
    def json(self):

        return {
            "id": self.id,
            "item_id": self.item.id,
            "name": self.item.name,
            "description": self.item.description,
            "price": self.item.price,
            "award": bool(self.item.given_award),
            "ability": self.item.consumable
        }
