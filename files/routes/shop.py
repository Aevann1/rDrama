from files.__main__ import app
from files.helpers.wrappers import *
from files.classes.shop import *
from collections import OrderedDict


@app.get("/shop")
@auth_required
def shop_index(v):

    return render_template("shop/shop.html", v=v)


@app.get("/api/items/all")
def shop_items_get():

    cats_only = bool(int(request.args.get("cats_only", "0")))

    # option to load only categories without items
    if cats_only:

        return jsonify(list(CATEGORIES))

    # group items into cats
    data = OrderedDict()
    for x in list(ITEMS.values()):

        _cat = CATEGORIES[x["category"]]

        if _cat in data:
            data[_cat].append(x)
        else:
            data[_cat] = [x]

    # featured
    if 'with_featured' in request.args:

        _f = [x for x in list(ITEMS.values()) if x["featured"]]

        data = {"Featured": _f, **data}

    return jsonify(data)


@app.get("/api/items/featured")
def shop_items_featured():

    return jsonify([x for x in ITEMS.values() if x['featured']])


@app.get("/api/items/consumables")
@auth_required
def shop_items_consumables(v):

    queer = g.db.query(func.count(ShopItem.item_id).label("owned"), ShopItemDef)\
        .join(ShopItem.item)\
        .filter(ShopItem.user_id == v.id)\
        .group_by(ShopItem.item_id, ShopItemDef.id)\
        .all()

    data = []
    for owned, item in queer:
        _json = item.json
        _json["owned"] = owned
        data.append(_json)

    return jsonify(data)


@app.get("/api/items/mine")
@auth_required
def items_mine(v):

    queer = g.db.query(ShopItem).filter_by(user_id=v.id).all()

    return jsonify([x.json for x in queer])


@app.post("/api/items/mine/<iid>")
@auth_required
@validate_formkey
def purchase_item(iid, v):

    item = g.db.query(ShopItemDef).filter_by(id=iid).first()

    if not item:
        return jsonify({"error": "Invalid item"}), 404

    if item.cost > v.coins:
        return jsonify({"error": f"You need {item.cost - v.coins} more coins to buy this item."}), 403

    new_item = ShopItem(
        user_id=v.id,
        item_id=item.id
    )

    g.db.add(new_item)

    v.coins -= item.cost
    v.coins_spent += item.cost

    if item.given_award:
        latest = g.db.query(AwardRelationship).order_by(AwardRelationship.id.desc()).first()

        if latest:
            thing = latest.id+1
        else:
            thing = 1

        give_award = AwardRelationship(
            id=thing,
            kind=item.given_award,
            user_id=v.id
        )

        g.db.add(give_award)

    g.db.add(v)

    return jsonify({"message": f"{item.name} purchased"}), 201


# toggle featured status on item
@app.patch("/api/items/<iid>/featured")
@auth_required
@validate_formkey
def toggle_item_featured(iid, v):

    if v.admin_level < 6:
        return jsonify({"error": "Nice try retard"}), 403

    item = g.db.query(ShopItemDef).filter_by(id=iid).first()

    if not item:
        return jsonify({"error": "You tried to feature an item that doesn't even exist. Please do better."}), 404

    return_msg = f"{item.name} removed from featured" if item.featured else f"{item.name} added to featured"

    item.featured = not item.featured

    g.db.add(item)

    return jsonify({"message": return_msg})
