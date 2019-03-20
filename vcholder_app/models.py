from vcholder_app import db, app
import uuid


def on_init_db():
    app.logger.debug("on_init_db")
    db.create_all()
    # db.session.delete(User.query.first())
    # db.session.commit()
    if not User.query.first():
        db.session.add(User('admin', 'admin'))
        db.session.commit()


class VCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(50), nullable=False)
    vc_property = db.Column(db.String(100), nullable=False)
    vc_value = db.Column(db.String(1000), nullable=False)

    def __init__(self, uid, vc_property, vc_value):
        self.uid = uid
        self.vc_property = vc_property
        self.vc_value = vc_value
        super(VCard, self).__init__()

    def __repr__(self):
        return '<VCard [%i]%s:%s>' % (self.id, self.uid, self.vc_property)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    api_key = db.Column(db.String(100), nullable=False)
    # last_login =

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.api_key = uuid.uuid4().hex

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User [%i]%s:%s>' % (self.id, self.username, self.api_key)
