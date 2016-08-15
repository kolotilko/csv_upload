from app import db


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_lvl_1 = db.Column(db.Text)

    def __repr__(self):
        return self.category_lvl_1

