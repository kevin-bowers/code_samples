#!/usr/bin/env python
import bson
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from bson import ObjectId


class Mongo:
    def __init__(self, user=None, password=None, host='127.0.0.1', database='salt', verbose=False):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.verbose = verbose
        self._connect()

    def _log(self, msg):
        if self.verbose:
            print('Mongo:: {}'.format(msg))

    def _connect(self):
        user = self.user
        password = self.password
        database = self.database
        host = self.host
        try:
            if user and password:
                client = MongoClient('mongodb://' + user + ':' + password + '@' + host)
            else:
                client = MongoClient()
            self.client = client
            self.db = client[database]
            self._log('Successfully connected to Mongo.')
            return True
        except OperationFailure as e:
            self._log('Unable to connect to Mongo - Exception: {}'.format(e))
            return False

    def find(self, collection):
        self._log('Executing find_one on collection: {}'.format(collection))
        result = self.db[collection].find_one()
        return result

    def find_all(self, collection):
        self._log('Executing find_all on collection: {}'.format(collection))
        result = self.db[collection].find()
        return result

    def count(self, collection):
        self._log('Executing count on collection: {}'.format(collection))
        result = self.db[collection].count()
        return result

    def insert(self, collection, data):
        self._log('Inserting data into {}'.format(collection))
        if type(data) != dict:
            raise ValueError('Expecting to insert type dict; got {}'.format(type(data)))
        insert = self.db[collection].insert_one(data)
        return insert

    def update_kv(self, collection, cid, key, value):
        self._log('Updating Collection: {}'.format(collection))
        if type(cid) != bson.objectid.ObjectId:
            cid = ObjectId(cid)
        update = self.db[collection].update_one({'_id': cid}, {"$set": {key: value}})
        return update

    def update_collection(self, collection, cid, data):
        self._log('Updating Collection: {}'.format(collection))
        if type(cid) != bson.objectid.ObjectId:
            cid = ObjectId(cid)
        update = self.db[collection].update_one({'_id': cid}, {"$set": data})
        return update

    def insert_history(self, collection, data):
        self._log('Updating history collection for {} collection'.format(collection))
        history_collection = '{}_history'.format(collection)
        data.pop('_id', None)
        insert = self.insert(history_collection, data)
        return insert

    def delete_key(self, collection, key):
        self._log('Deleting Key: {}'.format(key))
        collection_id = self.find(collection)['_id']
        update = self.db.settings.update({'_id': ObjectId(collection_id)}, {"$unset": {key: 1}})
        return update

    def rename_key(self, collection, old_key, new_key):
        self._log('Re-naming Key: {}'.format(old_key))
        collection_id = self.find(collection)['_id']
        update = self.db.settings.update({'_id': ObjectId(collection_id)}, {"$rename": {old_key: new_key}})
        return update

    def drop_collection(self, collection):
        self.db[collection].drop()
        return True

    def delete_document(self, collection, cid):
        if type(cid) != bson.objectid.ObjectId:
            cid = ObjectId(cid)
        delete = self.db[collection].delete_one({'_id': cid})
        return delete
