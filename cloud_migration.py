# cloud_migration.py
# This module handles the migration of old data to cloud/storage

from setup import s3, new_client
from config import BUCKET_NAME
import time, os, logging
from datetime import timedelta, datetime, timezone
import pandas as pd
logger = logging.getLogger(__name__)

def migration_to_cloud(stop_event, clickhouse_duration, archive_frequency):
    
    ch_client = new_client()
    parquet_dir = 'parquet_data'
    os.makedirs(parquet_dir, exist_ok=True)

    while not stop_event.is_set():
        logger.debug("Starting full migration cycle.")
        try:
            # establish cutoff time
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=clickhouse_duration)
            cutoff_ms = int(cutoff_time.timestamp() * 1000)

            # get all old ticks and downsample
            old_ticks = ch_client.query(f'''
                SELECT * FROM ticks_db
                WHERE timestamp_ms < {cutoff_ms}
            ''').result_rows
            old_ticks_df = pd.DataFrame(old_ticks, columns=[
                'timestamp', 'timestamp_ms', 'symbol', 'price', 'volume', 'received_at', 'insert_time'
            ])

            old_ticks_df['timestamp'] = pd.to_datetime(old_ticks_df['timestamp'], errors='coerce', utc=True)

            # save parquet locally, then upload to cloud
            latest_file = f'parquet_data/ticks.parquet'
            old_ticks_df.to_parquet(latest_file, index=False)
            s3_key = "ticks_data"
            try:
                s3.upload_file(latest_file, BUCKET_NAME, s3_key)
                logger.info(f"Uploaded {latest_file} to S3 at {s3_key}")
            except Exception:
                logger.exception(f"Error uploading to S3")

            # delete old data
            ch_client.command(f'''
                ALTER TABLE ticks_db
                DELETE WHERE timestamp_ms < {cutoff_ms}
            ''')
            logger.info("Deleted migrated records from ticks_db.")

        except Exception:
            logger.exception("Error during migration to cloud")

        time.sleep(archive_frequency)
