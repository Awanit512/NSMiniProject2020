from flask_login import UserMixin
from __init__ import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    salt = db.Column(db.String(100))
    loginCountFailure =  db.Column(db.Integer)
    FirstLoginTime = db.Column(db.String(100))
    currentLoginTime = db.Column(db.String(100))


    # @classmethod
    # def updateLoginFailureCounter(cls, id,increased=True):
    #     model = User.get(cls.id == id)
    #     if model is not None :
    #         if increased:
    #             model.loginCountFailure = loginCountFailure  + 1
    #         else:
    #             model.loginCountFailure = 0
    #     model.save() 
    #     return 

    # @classmethod
    # def updatecurrentLoginTime(cls, id, currenttime):
    #     model = User.get(cls.id == id)
    #     if model is not None:
    #         model.currentLoginTime = str(currenttime)
    #     model.save() 
    #     return 



