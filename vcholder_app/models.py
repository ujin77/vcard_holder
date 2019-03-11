from vcholder_app import db


class VCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(50))
    vc_property = db.Column(db.String(100), nullable=False)
    vc_value = db.Column(db.String(1000), nullable=False)

    def __init__(self, uid, vc_property, vc_value):
        self.uid = uid
        self.vc_property = vc_property
        self.vc_value = vc_value
