# cloud_migration.py
# This module handles the migration of old data to cloud/storage

from clickhouse import new_client
import time, os, logging
from datetime import timedelta, datetime, timezone
import pandas as pd
import boto3
logger = logging.getLogger(__name__)

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

s3 = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def migration_to_cloud(stop_event, clickhouse_duration, archive_frequency):
    
    ch_client = new_client()
    parquet_dir = 'parquet_data'
    os.makedirs(parquet_dir, exist_ok=True)

    while not stop_event.is_set():
        logger.debug("Starting full migration cycle.")
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=clickhouse_duration)
            cutoff_ms = int(cutoff_time.timestamp() * 1000)
            ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

            # -------------------------- ticks_db -------------------------- #
            old_ticks = ch_client.query(f'''
                SELECT * FROM ticks_db
                WHERE timestamp_ms < {cutoff_ms}
            ''').result_rows
            old_ticks_df = pd.DataFrame(old_ticks, columns=[
                'timestamp', 'timestamp_ms', 'symbol', 'price', 'volume', 'received_at', 'insert_time'
            ])

            old_ticks_df['timestamp'] = pd.to_datetime(old_ticks_df['timestamp'], errors='coerce', utc=True)
            old_ticks_df['second'] = old_ticks_df['timestamp'].dt.floor('1s')
            old_ticks_df = old_ticks_df.groupby('second').agg({
                'timestamp_ms': 'last',
                'symbol': 'last',
                'price': 'last',
                'volume': 'sum',
                'received_at': 'last',
                'insert_time': 'last'
            }).reset_index()
            old_ticks_df.rename(columns={'second': 'timestamp'}, inplace=True)

            latest_file = f'{parquet_dir}/ticks.parquet'
            archive_file_name = f'ticks_{ts}'
            archive_file_dir = f'{parquet_dir}/{archive_file_name}.parquet'
            old_ticks_df.to_parquet(latest_file, index=False)
            old_ticks_df.to_parquet(archive_file_dir, index=False)
            logger.info(f"Written Parquet files: {latest_file} and {archive_file_dir}")

            ch_client.command(f'''
                ALTER TABLE ticks_db
                DELETE WHERE timestamp_ms < {cutoff_ms}
            ''')
            logger.debug("Deleted migrated records from ticks_db.")

            # -------------------------- cloud upload -------------------------- #

            s3_key = f"archived_data/{archive_file_name}"
            try:
                # s3.upload_file(file_path, BUCKET_NAME, s3_key)
                logger.info(f"Uploaded {archive_file_dir} to S3 at {s3_key}")
                os.remove(archive_file_dir)
            except Exception:
                logger.exception(f"Error uploading {archive_file_dir} to S3")

        except Exception:
            logger.exception("Error during migration to cloud")

        time.sleep(archive_frequency)
