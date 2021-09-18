from files.__main__ import app
from files.helpers.wrappers import *
from files.classes.shop import *
# from collections import OrderedDict
# import pprint

# discounts for paypigs
DISCOUNTS = {
    1: 10,
    2: 15,
    3: 30
}


def real_cost(v: User, cost: int) -> int:
    """
    takes an user object and a price as an argument and returns the discount price for that user
    """

    if v.patron > 0:
        if v.patron in range(1, 4):
            return cost - (cost//100*DISCOUNTS[v.patron])
        else:
            return cost - (cost//100*30)
    else:
        return cost


# fuck it i'm lazy
class Thing:

    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def real_cost(self, v: User) -> int:
        return real_cost(v, self.cost)


@app.get("/shop")
@auth_required
def shop_index(v):

    return render_template("shop/shop.html", v=v)


@app.get("/api/items/all")
@auth_required
def shop_items_get(v):

    cats_only = bool(int(request.args.get("cats_only", "0")))

    # option to load only categories without items
    if cats_only:

        return jsonify(list(CATEGORIES))

    # group items into cats
    data = {}
    for x in list(ITEMS.values()):

        x["cost"] = real_cost(v, x.get("cost"))

        _cat = CATEGORIES[x["category"]]

        if _cat in data:
            data[_cat].append(x)
        else:
            data[_cat] = [x]

    return jsonify(data)


# @app.get("/api/items/featured")
# def shop_items_featured():
#
#     return jsonify([x for x in ITEMS.values() if x['featured']])


# @app.get("/api/items/consumables")
# @auth_required
# def shop_items_consumables(v):
#
#     queer = g.db.query(func.count(ShopItem.item_id).label("owned"), ShopItemDef)\
#         .join(ShopItem.item)\
#         .filter(ShopItem.user_id == v.id)\
#         .group_by(ShopItem.item_id, ShopItemDef.id)\
#         .all()
#
#     data = []
#     for owned, item in queer:
#         _json = item.json
#         _json["owned"] = owned
#         data.append(_json)
#
#     return jsonify(data)


@app.get("/api/items/mine")
@auth_required
def items_mine(v):

    queer = g.db.query(ShopItem).filter_by(user_id=v.id).all()

    return jsonify([x.json for x in queer])


@app.post("/api/purchase/<kind>")
@auth_required
@validate_formkey
def purchase_item(kind, v):

    i = ITEMS.get(kind)

    if not i:
        return jsonify({"error": "Invalid item"}), 400

    i = Thing(**i)
    cost = i.real_cost(v)

    if cost > v.coins:
        return jsonify({"error": f"You need {cost - v.coins} more coins to buy this item"}), 403

    v.coins -= cost
    v.coins_spent += cost
    g.db.add(v)

    item = ShopItem(user_id=v.id, kind=i.kind)
    g.db.add(item)

    if i.awardKind:

        try:
            thing = g.db.query(AwardRelationship).order_by(AwardRelationship.id.desc()).first().id
        except AttributeError:
            thing = 0

        award = AwardRelationship(
            id=thing+1,
            user_id=v.id,
            kind=i.awardKind
        )

        g.db.add(award)

    return jsonify({"message": f"{i.name} purchased"}), 201


# toggle featured status on item
# @app.patch("/api/items/<iid>/featured")
# @auth_required
# @validate_formkey
# def toggle_item_featured(iid, v):
#
#     if v.admin_level < 6:
#         return jsonify({"error": "Nice try retard"}), 403
#
#     item = g.db.query(ShopItemDef).filter_by(id=iid).first()
#
#     if not item:
#         return jsonify({"error": "You tried to feature an item that doesn't even exist. Please do better."}), 404
#
#     return_msg = f"{item.name} removed from featured" if item.featured else f"{item.name} added to featured"
#
#     item.featured = not item.featured
#
#     g.db.add(item)
#
#     return jsonify({"message": return_msg})
