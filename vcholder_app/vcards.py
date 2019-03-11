from vcholder_app import db
from vcholder_app.models import VCard
# import uuid
# import json


# def get_vcard(uid):
#     return 'test<HR>'


# def new_uuid():
#     return str(uuid.uuid4())


# def add_defaults():
#     uid = '00000000-0000-0000-0000-000000000000'
#     db.session.add(VCard(uid, 'N', 'Gump;Forrest;;Mr.;'))
#     db.session.add(VCard(uid, 'FN', 'Forrest Gump'))
#     db.session.add(VCard(uid, 'ORG', 'Bubba Gump Shrimp Co.'))
#     db.session.add(VCard(uid, 'TITLE', 'Shrimp Man'))
#     db.session.commit()


class VCards(object):

    def is_uid(self, uid):
        if VCard.query.filter_by(uid=uid).first():
            return True
        return False

    def get_by_uid(self, uid, html=False):
        vcl = ['BEGIN:VCARD', 'VERSION:3.0']
        vc = VCard.query.filter_by(uid=uid).all()
        for vc_item in vc:
            vcl.append('%s:%s' % (vc_item.vc_property, vc_item.vc_value))
        # vcl.append('UID:%s' % uid)
        vcl.append('END:VCARD')
        if html:
            return '<BR>'.join(vcl)
        return "\n".join(vcl)

    def ldap_sync(self, uid, data):
        updated = 0
        inserted = 0
        for vc_property in data:
            vcard = VCard.query.filter_by(uid=uid, vc_property=vc_property).first()
            if vcard:
                if vcard.vc_value != data[vc_property]:
                    # print('Update: [%s] [%s]' % (vcard.vc_value, data[vc_property]))
                    vcard.vc_value = data[vc_property]
                    updated += 1
            else:
                db.session.add(VCard(uid, vc_property, data[vc_property]))
                inserted += 1
                # print('Insert')
        db.session.commit()
        return updated, inserted

    def delete_by_uid(self, uid):
        for vcard in VCard.query.filter_by(uid=uid).all():
            db.session.delete(vcard)
        db.session.commit()
        return True
