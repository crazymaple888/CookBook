"""Seed ingredient categories and common synonyms into the database.

Run: python -m scripts.init_ingredients
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.models import Ingredient, IngredientCategory, IngredientSynonym
from app.models.base import SessionLocal

CATEGORIES = [
    ("蔬菜", 1),
    ("肉类", 2),
    ("水产", 3),
    ("蛋奶", 4),
    ("豆制品", 5),
    ("主食", 6),
    ("菌菇", 7),
    ("水果", 8),
    ("调料", 9),
]

# name -> (category, [synonyms])
SEED_INGREDIENTS: dict[str, tuple[str, list[str]]] = {
    "西红柿": ("蔬菜", ["番茄", "蕃茄", "西红杮"]),
    "鸡蛋": ("蛋奶", ["鸡蛋液", "土鸡蛋"]),
    "土豆": ("蔬菜", ["马铃薯", "洋芋"]),
    "洋葱": ("蔬菜", ["洋葱头"]),
    "大蒜": ("调料", ["蒜", "蒜瓣", "蒜米"]),
    "生姜": ("调料", ["姜", "姜片"]),
    "小葱": ("蔬菜", ["葱", "香葱", "葱花"]),
    "白菜": ("蔬菜", ["大白菜", "娃娃菜"]),
    "菠菜": ("蔬菜", ["菠菜叶"]),
    "胡萝卜": ("蔬菜", ["红萝卜"]),
    "猪肉": ("肉类", ["五花肉", "里脊肉", "猪五花"]),
    "牛肉": ("肉类", ["牛里脊", "牛腩", "肥牛"]),
    "鸡肉": ("肉类", ["鸡胸肉", "鸡腿肉", "整鸡"]),
    "豆腐": ("豆制品", ["北豆腐", "嫩豆腐"]),
    "大米": ("主食", ["米", "白米"]),
    "面粉": ("主食", ["小麦粉", "中筋面粉"]),
    "生抽": ("调料", ["酱油"]),
    "老抽": ("调料", ["红烧酱油"]),
    "蚝油": ("调料", []),
    "白糖": ("调料", ["砂糖", "白砂糖"]),
    "盐": ("调料", ["食盐"]),
    "料酒": ("调料", ["黄酒"]),
    "食用油": ("调料", ["油", "色拉油", "花生油"]),
    "辣椒": ("蔬菜", ["红辣椒", "尖椒", "杭椒"]),
    "黄瓜": ("蔬菜", ["青瓜"]),
    "茄子": ("蔬菜", []),
    "青椒": ("蔬菜", ["甜椒", "灯笼椒"]),
    "香菇": ("菌菇", ["鲜香菇", "冬菇"]),
    "金针菇": ("菌菇", []),
    "虾": ("水产", ["鲜虾", "基围虾", "明虾"]),
    "鱼": ("水产", ["草鱼", "鲤鱼", "鲈鱼"]),
    "苹果": ("水果", []),
    "香蕉": ("水果", []),
    "牛奶": ("蛋奶", ["纯牛奶", "鲜牛奶"]),
}


def main() -> None:
    db = SessionLocal()
    try:
        cat_by_name: dict[str, IngredientCategory] = {}
        for name, sort_order in CATEGORIES:
            cat = db.scalar(select(IngredientCategory).where(IngredientCategory.name == name))
            if cat is None:
                cat = IngredientCategory(name=name, sort_order=sort_order)
                db.add(cat)
                db.flush()
            cat_by_name[name] = cat
        db.flush()

        created = 0
        for name, (cat_name, synonyms) in SEED_INGREDIENTS.items():
            ing = db.scalar(select(Ingredient).where(Ingredient.name == name))
            if ing is None:
                ing = Ingredient(name=name, category_id=cat_by_name[cat_name].id)
                db.add(ing)
                db.flush()
                created += 1
            for syn in synonyms:
                exists = db.scalar(
                    select(IngredientSynonym).where(IngredientSynonym.synonym == syn)
                )
                if exists is None:
                    db.add(IngredientSynonym(ingredient_id=ing.id, synonym=syn))
        db.commit()
        print(f"Seeded {created} new ingredients and their synonyms.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
