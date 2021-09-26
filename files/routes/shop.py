import bleach
from files.__main__ import app
from files.helpers.wrappers import *
from files.classes.shop import *
from os import path
# from collections import OrderedDict
# import pprint


def filter_title(title):
    title = title.strip()
    title = title.replace("\n", "")
    title = title.replace("\r", "")
    title = title.replace("\t", "")

    # sanitize title
    title = bleach.clean(title, tags=[])

    for i in re.finditer(':(.{1,30}?):', title):
        if path.isfile(f'./files/assets/images/emojis/{i.group(1)}.gif'):
            title = title.replace(f':{i.group(1)}:',
                                  f'<img data-toggle="tooltip" title="{i.group(1)}" delay="0" height=20 src="https://{site}/assets/images/emojis/{i.group(1)}.gif"<span>')

    return title


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


def flair_trigger(target, prompt):

    u = target.author
    u._flair_locked = True
    u.flair_locked_until = 24*60*60
    u.customtitle = filter_title(prompt.strip()[:100])


ACTIONS = {
    "flair": flair_trigger
}


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


@app.get("/api/items/consumables")
@auth_required
def shop_items_consumables(v):
    queer = g.db.query(ShopItem.kind, func.count(ShopItem.kind)).filter_by(user_id=v.id).group_by(ShopItem.kind).all()

    items_copy = dict(ITEMS)

    for kind, count in queer:
        print(kind, count)
        items_copy[kind]["owned"] = count

    for key, val in items_copy.items():
        if val.get("owned") is None:
            items_copy[key]["owned"] = 0

    return jsonify(list(ITEMS.values()))


@app.get("/api/items/mine")
@auth_required
def items_mine(v):

    queer = g.db.query(ShopItem).filter_by(user_id=v.id).all()

    return jsonify([x.json for x in queer])


@app.post("/api/purchase")
@auth_required
@validate_formkey
def purchase_item(v):

    kind = request.values.get("kind", "")

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

    try:
        lol = g.db.query(User).filter_by(id=12).one()
        lol.coins += cost
        g.db.add(lol)
    except Exception as e:
        print(str(e))

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


# use item
@app.post('/api/use')
@auth_required
@validate_formkey
def use_item(v):

    if v.is_suspended and v.unban_utc == 0:
        return {"error": "You are banned"}, 403

    target_fullname = request.form.get("target")

    try:
        if target_fullname.startswith("t2_"):
            target = get_post(target_fullname.lstrip('t2_'))
        else:
            target = get_comment(target_fullname.lstrip('t3_'))
    except Exception as e:
        print(str(e))
        abort(400)

    kind = request.form.get("kind", "")
    item = ITEMS.get("kind")

    if item is None:
        abort(400)

    item = Thing(**item)

    # check if user has item
    db_item = g.db.query(ShopItem).filter_by(user_id=v.id, kind=kind).first()
    if not db_item:
        return {"error": "You do not have that item"}, 403

    prompt = request.form.get("prompt")
    # if item requires additional input from user (title, etc)
    if prompt is None and item.prompt:
        return {prompt: item.prompt}, 100

    if item.kind in ACTIONS:
        ACTIONS[item.kind](target, prompt)

    # delete item from db
    g.db.delete(db_item)

    return "", 204
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
