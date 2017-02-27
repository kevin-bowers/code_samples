#!/usr/bin/env python
import hashlib
import os
import sqlite3
import time
import tinys3
import urllib
from functools import partial


class PyBackup:
    def __init__(self, s3_access_key, s3_secret_key, s3_bucket, backup_directory):
        self.s3_access_key = s3_access_key
        self.s3_secret_key = s3_secret_key
        self.bucket = s3_bucket
        self.backup_directory = backup_directory
        self.restore_directory = backup_directory
        self.s3pool = tinys3.Pool(self.s3_access_key, self.s3_secret_key, tls=True, size=10)
        self.c, self.conn = self.db_connect()

    def db_connect(self):
        conn = sqlite3.connect('backup.db')
        c = conn.cursor()
        sql = 'create table if not exists files (file text, MD5 text)'
        c.execute(sql)
        return c, conn

    def gen_file_list(self):
        filelist = []
        for directory in self.backup_directory:
            for root, subFolders, files in os.walk(directory):
                for file in files:
                    filelist.append(os.path.join(root, file))
        return filelist

    def md5sum(self, filename):
        with open(filename, mode='rb') as f:
            d = hashlib.md5()
            for buf in iter(partial(f.read, 128), b''):
                d.update(buf)
        return d.hexdigest()

    def cleanup(self):
        removed = []
        self.c.execute('SELECT file FROM files;')
        for result in self.c.fetchall():
            if os.path.isfile(result[0]) is False:
                print '%s is no longer present. Removing from database and backups' % (result[0])
                delete_query = "DELETE from files where file = '{}'".format(result[0])
                self.c.execute(delete_query)
                self.conn.commit()
                self.s3pool.delete(result, self.bucket)
                removed.append(result[0])
        return removed

    def backup(self):
        """
        The goal here is to evaluate the files in the backup_directory
        and the files in the SQLite database.
        If the MD5 hash is different than the database, upload the file to S3
        and update the database with the new hash.
        """
        matches = []
        additions = []
        changes = []
        file_list = self.gen_file_list()
        for file in file_list:
            query = self.c.execute('SELECT MD5 FROM files WHERE file = ?', (file,))
            file_hash = self.md5sum(file)
            query = query.fetchone()
            if query:
                for results in query:
                    if file_hash not in results:
                        self.c.execute('UPDATE files SET MD5 = ? WHERE file = ?', (file_hash, file))
                        self.conn.commit()
                        changes.append(file)
                        print 'Detected change in %s. New hash: %s' % (file, file_hash)
                    elif file_hash in results:
                        print '{} matches the database'.format(file)
                        matches.append(file)
            else:
                self.c.execute('INSERT INTO files VALUES (?,?)', (file, file_hash))
                self.conn.commit()
                additions.append(file)
                print "{} wasn't in inventory. Added to upload list.".format(file)
        removed = self.cleanup()
        uploads = additions + changes
        for file in uploads:
            f = open(file, 'rb')
            upload = self.s3pool.upload(file, f, self.bucket)
        if len(uploads) > 0:
            while True:
                if not upload.done():
                    print "Uploading isn't complete yet. Please wait..."
                    time.sleep(5)
                else:
                    print 'Upload Complete!'
                    break
        print '\nChanges: {}\nMatches: {}\nAdditions: {}\nRemoved: {}'.format(len(changes), len(matches),
                                                                              len(additions), len(removed))
        return 'Backup Complete'

    def restore(self, files_to_restore):
        restored_files = []
        requests = []
        self.restore_directory = self.restore_directory[0]
        if not os.path.exists(self.restore_directory):
            os.makedirs(self.restore_directory)
        for file in files_to_restore:
            requests.append(self.s3pool.get(bucket=self.bucket, key=file))
            self.s3pool.all_completed(requests)
        for file in self.s3pool.as_completed(requests):
            file_to_restore = self.restore_directory + '/' + urllib.unquote(file.url.split('/')[-1:][0])
            print "Writing File: {}".format(file_to_restore)
            with open(file_to_restore, 'w') as f:
                f.write(file.content)
                f.close()
            if int(file.headers['Content-Length']) == os.stat(file_to_restore).st_size:
                restored_files.append(file)
        return 'Successfully restored {} files'.format(len(restored_files))
