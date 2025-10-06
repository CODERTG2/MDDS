from mongoengine import Document, StringField, DateTimeField
from datetime import datetime

class CacheDB(Document):
    query = StringField(required=True)
    answer = StringField(required=True)
    tag = StringField(required=True, enum=["normal", "deep"])
    createdAt = DateTimeField(required=True, default=datetime.now)    

    meta = {
        'collection': 'cache',
        'indexes': [
            {'fields': ['query', 'answer', 'createdAt'], 'unique': True}
        ]
    }