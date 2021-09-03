from files.__main__ import app
from files.helpers.wrappers import *
from files.classes.shop import *


@app.get("/shop")
@auth_required
def shop_index(v):

    return render_template("shop/shop.html", v=v)


@app.get("/shop/edit/<iid>")
@auth_required
def get_shop_item_edit(iid, v):

    if v.admin_level < 6:
        abort(403)

    item = g.db.query(ShopItemDef).filter_by(id=iid).first()

    if not item:
        abort(404)

    cats = g.db.query(ShopCategory).options(lazyload('*')).filter(ShopCategory.id != item.category_id).all()

    return render_template("shop/shop-edit.html", item=item, cats=cats, v=v)


@app.post("/api/edit_item/<iid>")
@auth_required
def shop_item_edit(iid, v):

    if v.admin_level < 6:
        abort(403)

    item = g.db.query(ShopItemDef).filter_by(id=iid).first()

    if not item:
        abort(404)

    item.name = request.form.get("name", item.name).strip()
    item.description = request.form.get("description", item.description).strip()
    item.icon_url = request.form.get("icon-url", item.icon_url).strip()
    item.price = int(request.form.get("price", item.price))
    item.discount_price = int(request.form.get("discount-price", "0"))
    item.category_id = int(request.form.get("category", 1))

    g.db.add(item)

    cats = g.db.query(ShopCategory).options(lazyload('*')).filter(ShopCategory.id != item.category_id).all()

    return render_template("shop/shop-edit.html", item=item, cats=cats, v=v)


@app.get("/api/items/all")
def shop_items_get():

    cats_only = bool(int(request.args.get("cats_only", "0")))

    # option to load only categories without items
    if cats_only:

        # don't need to load related items here - overwrite default load with lazy load
        queer = g.db.query(ShopCategory).options(lazyload('*')).all()

        return jsonify([x.json_noitems for x in queer])

    queer = g.db.query(ShopCategory).all()
    data = [x.json for x in queer]

    # option to auto-add a featured section
    if 'with_featured' in request.args:
        queer2 = g.db.query(ShopItemDef).filter_by(featured=True).all()

        featured = {
            "id": 0,
            "name": "New & Noteworthy",
            "description": "These items are now being featured.",
            "items": [x.json for x in queer2]
        }

        data.append(featured)
        data = sorted(data, key=lambda x: x['id'])

    return jsonify(data)


@app.get("/api/items/featured")
def shop_items_featured():

    queer = g.db.query(ShopItemDef).filter_by(featured=True).all()

    return jsonify([x.json for x in queer])


@app.get("/api/items/consumables")
def shop_items_consumables():

    queer = g.db.query(ShopItemDef).filter_by(consumable=True).all()

    return jsonify([x.json for x in queer])


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
