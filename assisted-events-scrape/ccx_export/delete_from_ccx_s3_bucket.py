#!/bin/env python3

from datetime import datetime, timezone
import os
import boto3


def delete_s3_objects():
    bucket = os.getenv('AWS_S3_BUCKET')
    dry_run = os.getenv('DRYRUN', '0')
    dry_run = int(dry_run)

    delete_until = os.getenv('DELETE_UNTIL_DATE')
    if delete_until:
        delete_until = datetime.strptime(delete_until, '%Y-%m-%d %H:%M:%S')
    else:
        delete_until = datetime.now()

    delete_until = delete_until.replace(tzinfo=timezone.utc)

    print(f"Deleting all objects from s3 bucket {bucket} until {delete_until} (dry-run: {dry_run})")
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket)

    for obj in bucket.objects.all():
        if obj.last_modified < delete_until:
            if dry_run > 0:
                print(f"(dry-run) deleting {obj.key}")
            else:
                print(f"deleting {obj.key}")
                obj.delete()


if __name__ == '__main__':
    delete_s3_objects()
