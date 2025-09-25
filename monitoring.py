# monitoring.py
# records notable events and handles crashes

from setup import new_client
import time, logging
from datetime import datetime, timezone, timedelta
import pandas as pd
logger = logging.getLogger(__name__)

def ticks_monitoring(stop_event,duration):

    time.sleep(duration)
    ch = new_client()

    while not stop_event.is_set():
        logger.debug("Starting ticks monitoring cycle.")
        try:
            current_time = datetime.now(timezone.utc)
            current_time_ms = int(current_time.timestamp() * 1000)
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=duration)
            cutoff_time_ms = int(cutoff_time.timestamp() * 1000)

            diagnostic_rows = ch.query(f'''
                SELECT * FROM ticks_db
                WHERE toUnixTimestamp64Milli(insert_time) > {cutoff_time_ms} AND toUnixTimestamp64Milli(insert_time) <= {current_time_ms}
            ''').result_rows

            df = pd.DataFrame(diagnostic_rows, columns=[
                'timestamp', 'timestamp_ms', 'symbol', 'price', 'volume', 'received_at', 'insert_time'
                ])

            #if the system is down, we still want to record diagnostics data to show lag
            if df.empty:
                avg_timestamp = None
                avg_received_at = None
                avg_insert_time = None
                message_count = 0
                ws_lag = None
                proc_lag = None

            else:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['received_at'] = pd.to_datetime(df['received_at'])
                df['insert_time'] = pd.to_datetime(df['insert_time'])

                avg_timestamp = df['timestamp'].mean()
                avg_received_at = df['received_at'].mean()
                avg_insert_time = df['insert_time'].mean()
                ws_lag = (avg_received_at - avg_timestamp).total_seconds()
                proc_lag = (avg_insert_time - avg_received_at).total_seconds()
                message_count = len(df)

            # ----- diagnostics  ----- #
            ch.insert('websocket_diagnostics',
                [(avg_timestamp, avg_received_at, ws_lag, message_count)],
                column_names=['avg_timestamp', 'avg_received_at', 'avg_websocket_lag', 'message_count'])
            
            ch.insert('processing_diagnostics',
                [(avg_timestamp, avg_received_at, avg_insert_time, proc_lag, message_count)],
                column_names=['avg_timestamp', 'avg_received_at', 'avg_processed_timestamp', 'avg_processing_lag', 'message_count'])

            logger.info(f"Inserted ticks monitoring data for {message_count} messages.")

        except Exception as e:
            logger.exception(f"Error inserting ticks monitoring data.")

        time.sleep(duration)