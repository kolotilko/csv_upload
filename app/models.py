from app import db


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    categories_id_lvl2 = db.Column(db.Text)
    categories_id_lvl4 = db.Column(db.Text)
    real_category_id = db.Column(db.Text)
    categories_name_lvl4 = db.Column(db.Text)
    categories_name_lvl5 = db.Column(db.Text)
    categories_name_lvl7 = db.Column(db.Text)
    categories_name_lvl6 = db.Column(db.Text)
    categories_name_lvl8 = db.Column(db.Text)
    categories_id_lvl8 = db.Column(db.Text)
    categories_id_lvl6 = db.Column(db.Text)
    categories_name_lvl2 = db.Column(db.Text)
    categories_name_lvl3 = db.Column(db.Text)
    categories_id_lvl5 = db.Column(db.Text)
    categories_id_lvl7 = db.Column(db.Text)
    categories_name_lvl1 = db.Column(db.Text)
    categories_id_lvl1 = db.Column(db.Text)
    categories_id_lvl0 = db.Column(db.Text)
    categories_id_lvl3 = db.Column(db.Text)
    category_id = db.Column(db.Text)
    categories_name_lvl0 = db.Column(db.Text)

    def __repr__(self):
        return self.category_lvl_1

