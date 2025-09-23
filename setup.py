# setup.py

# one off container to run at the start
# docker compose run --rm db_setup

from clickhouse import create_ticks_db, create_diagnostics_db, create_diagnostics_monitoring_db, delete_tables
import logging
logger = logging.getLogger(__name__)

try:
    logger.info("Deleting tables.")
    delete_tables()
except Exception:
    logger.warning("Error when deleting tables.")

try:
    logger.info("Creating tables.")
    create_ticks_db(), create_diagnostics_db(), create_diagnostics_monitoring_db()
except Exception:
    logger.warning("Error when creating tables.")

# add table modification