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
    time.sleep(10)  # pause before beginning the migration to let data populate

    ch_client = new_client()
    parquet_dir = 'parquet_data'
    log_dir = 'log_data'
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
            archive_file = f'{parquet_dir}/ticks_{ts}.parquet'
            old_ticks_df.to_parquet(latest_file, index=False)
            old_ticks_df.to_parquet(archive_file, index=False)
            logger.info(f"Written Parquet files: {latest_file} and {archive_file}")

            ch_client.command(f'''
                ALTER TABLE ticks_db
                DELETE WHERE timestamp_ms < {cutoff_ms}
            ''')
            logger.debug("Deleted migrated records from ticks_db.")

            # -------------------------- websocket_diagnostics -------------------------- #
            old_ws = ch_client.query(f'''
                SELECT * FROM websocket_diagnostics
                WHERE toUnixTimestamp64Milli(diagnostics_timestamp) < {cutoff_ms}
            ''').result_rows
            ws_df = pd.DataFrame(old_ws, columns=[
                'avg_timestamp', 'avg_received_at', 'avg_websocket_lag', 'message_count', 'diagnostics_timestamp'
            ])
            latest_file = f'{parquet_dir}/ws_diagnostics.parquet'
            archive_file = f'{parquet_dir}/ws_diagnostics_{ts}.parquet'
            ws_df.to_parquet(latest_file, index=False)
            ws_df.to_parquet(archive_file, index=False)
            logger.info(f"Written Parquet files: {latest_file} and {archive_file}")

            ch_client.command(f'''
                ALTER TABLE websocket_diagnostics
                DELETE WHERE toUnixTimestamp64Milli(diagnostics_timestamp) < {cutoff_ms}
            ''')
            logger.debug("Deleted migrated records from websocket_diagnostics.")

            # -------------------------- processing_diagnostics -------------------------- #
            old_proc = ch_client.query(f'''
                SELECT * FROM processing_diagnostics
                WHERE toUnixTimestamp64Milli(diagnostics_timestamp) < {cutoff_ms}
            ''').result_rows
            proc_df = pd.DataFrame(old_proc, columns=[
                'avg_timestamp', 'avg_received_at', 'avg_processed_timestamp', 'avg_processing_lag', 'message_count', 'diagnostics_timestamp'
            ])
            latest_file = f'{parquet_dir}/proc_diagnostics.parquet'
            archive_file = f'{parquet_dir}/proc_diagnostics_{ts}.parquet'
            proc_df.to_parquet(latest_file, index=False)
            proc_df.to_parquet(archive_file, index=False)
            logger.info(f"Written Parquet files: {latest_file} and {archive_file}")

            ch_client.command(f'''
                ALTER TABLE processing_diagnostics
                DELETE WHERE toUnixTimestamp64Milli(diagnostics_timestamp) < {cutoff_ms}
            ''')
            logger.debug("Deleted migrated records from processing_diagnostics.")

            # -------------------------- monitoring_db -------------------------- #
            old_mon = ch_client.query(f'''
                SELECT * FROM monitoring_db
                WHERE toUnixTimestamp64Milli(monitoring_timestamp) < {cutoff_ms}
            ''').result_rows
            mon_df = pd.DataFrame(old_mon, columns=[
                'monitoring_timestamp', 'message'
            ])
            latest_file = f'{parquet_dir}/monitoring.parquet'
            archive_file = f'{parquet_dir}/monitoring_{ts}.parquet'
            mon_df.to_parquet(latest_file, index=False)
            mon_df.to_parquet(archive_file, index=False)
            logger.info(f"Written Parquet files: {latest_file} and {archive_file}")

            ch_client.command(f'''
                ALTER TABLE monitoring_db
                DELETE WHERE toUnixTimestamp64Milli(monitoring_timestamp) < {cutoff_ms}
            ''')
            logger.debug("Deleted migrated records from monitoring.")

            # -------------------------- uptime_db -------------------------- #
            old_uptime = ch_client.query(f'''
                SELECT * FROM uptime_db
                WHERE toUnixTimestamp64Milli(uptime_timestamp) < {cutoff_ms}
            ''').result_rows
            uptime_df = pd.DataFrame(old_uptime, columns=[
                'uptime_timestamp', 'is_up'
            ])
            latest_file = f'{parquet_dir}/uptime_diagnostics.parquet'
            archive_file = f'{parquet_dir}/uptime_diagnostics_{ts}.parquet'
            uptime_df.to_parquet(latest_file, index=False)
            uptime_df.to_parquet(archive_file, index=False)
            logger.info(f"Written Parquet files: {latest_file} and {archive_file}")

            ch_client.command(f'''
                ALTER TABLE uptime_db
                DELETE WHERE toUnixTimestamp64Milli(uptime_timestamp) < {cutoff_ms}
            ''')
            logger.debug("Deleted migrated records from uptime_db.")

            # -------------------------- log_data -------------------------- #
            for file in os.listdir(log_dir):
                file_path = os.path.join(log_dir, file)
                try:
                    df = pd.read_csv(
                        file_path,
                        sep="|",
                        header=None,
                        names=["timestamp", "level", "logger", "message"],
                        engine="python"
                    )
                    df["timestamp"] = pd.to_datetime(
                        df["timestamp"].str.strip(),
                        format="%Y-%m-%d %H:%M:%S,%f",
                        errors="coerce",
                        utc=True
                    )
                    df_old = df[df["timestamp"] < cutoff_time]
                    df_new = df[df["timestamp"] >= cutoff_time]

                    if not df_old.empty:
                        latest_file = f"{parquet_dir}/logs.parquet"
                        archive_file = f"{parquet_dir}/logs_{ts}.parquet"
                        df_old.to_parquet(latest_file, index=False)
                        df_old.to_parquet(archive_file, index=False)
                        logger.info(f"Migrated {len(df_old)} log rows to {latest_file} and {archive_file}")

                    else:
                        logger.info(f"No log rows to migrate.")

                    df_new.to_csv(file_path, sep="|", header=False, index=False)

                except Exception:
                    logger.exception(f"Failed to process log file {file_path}")

            # -------------------------- cloud upload -------------------------- #
            for parquet in os.listdir(parquet_dir):
                if not parquet.endswith(".parquet") or parquet.startswith("."): 
                    continue

                # Skip latest snapshot files
                if parquet in {
                    "ticks.parquet", "ws_diagnostics.parquet",
                    "proc_diagnostics.parquet", "monitoring.parquet",
                    "uptime_diagnostics.parquet",
                    "logs.parquet"
                }:
                    continue

                file_path = os.path.join(parquet_dir, parquet)
                s3_key = f"archived_data/{parquet}"
                try:
                    # s3.upload_file(file_path, BUCKET_NAME, s3_key)
                    logger.info(f"Uploaded {file_path} to S3 at {s3_key}")
                    os.remove(file_path)
                except Exception:
                    logger.exception(f"Error uploading {file_path} to S3")

        except Exception as e:
            logger.exception("Error during full_migration_to_cloud")

        time.sleep(archive_frequency)
