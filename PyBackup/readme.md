# PyBackup
A library used to backup and restore files using S3

## Requirements
- requests
- sqlite3
- tinys3

## Usage
Note: The S3 access key and secret access key arguments can be omitted if the following environment variables are set:
- s3_access_key
- s3_secret_access_key

### Backup
```backup.py -a backup --bucket 'bucket_name' -d '/backup/directory/one' '/another/directory' --s3-access-key 's3_access_key' --s3-secret-access-key 's3_secret_access_key'```

### Restore
```./backup.py -a restore --bucket 'bucket_name' -d '/directory/to/restore/to/' --s3-access-key 's3_access_key' --s3-secret-access-key 's3_secret_access_key' --file '/file/to/restore/1' '/file/to/restore/2'```

### Example Help
    ./backup.py
    usage: backup.py [-h] --action {backup,restore} --bucket BUCKET
    --directory DIRECTORY [DIRECTORY ...]
    [--file RESTORE [RESTORE ...]] [--verbose]
    [--s3-access-key S3_ACCESS_KEY]
    [--s3-secret-access-key S3_SECRET_ACCESS_KEY]
