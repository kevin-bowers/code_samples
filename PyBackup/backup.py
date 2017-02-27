#!/usr/bin/env python
import argparse
from pybackup import PyBackup


def main(args):
    action = args['action']
    bucket = args['bucket']
    directory = args['directory']
    file_to_restore = args['restore']
    s3_access_key = args['s3_access_key']
    s3_secret_access_key = args['s3_secret_access_key']

    pybackup = PyBackup(s3_access_key, s3_secret_access_key, bucket, directory, action)
    if action == 'backup':
        return pybackup.backup()
    elif action == 'restore':
        return pybackup.restore(file_to_restore)
    elif action == 'cleanup':
        return pybackup.cleanup()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='A Backup Utility'
    )
    available_actions = ['backup', 'cleanup', 'restore']
    parser.add_argument(
        '--action', '-a',
        required=True,
        choices=available_actions,
        help='--action -a: action',
        dest='action',
    )
    parser.add_argument(
        '--bucket', '-b',
        required=True,
        help='--bucket, -b: Bucket',
        dest='bucket',
    )
    parser.add_argument(
        '--directory', '-d',
        required=True,
        help='--directory -d: Directory to backup',
        nargs='+',
        dest='directory',
    )
    parser.add_argument(
        '--file', '-f',
        required=False,
        help='Path of File to restore',
        nargs='+',
        dest='restore',
    )
    parser.add_argument(
        '--s3-access-key',
        required=True,
        help='--s3-access-key: S3 Access Key',
        dest='s3_access_key',
    )
    parser.add_argument(
        '--s3-secret-access-key',
        required=True,
        help='--s3-secret-access-key: S3 Access Key',
        dest='s3_secret_access_key',
    )

    args = vars(parser.parse_args())
    print main(args)
