import atexit
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Dict, List

from src.contabo.contabo_exceptions import BatchProcessError
from src.contabo.create_instance import check_instance_status
from src.database.database import fetch_pending_instances
from src.vps.connect_vps import setup_vps


logger = logging.getLogger(__name__)


def batch_check_instance_status() -> Dict[str, int]:
    """
    Batch process to check instance statuses and update database.

    :return: Dictionary with counts of checked and running instances
    :raises BatchProcessError: If there's an error during the batch process
    """
    try:
        pending_instances = fetch_pending_instances()
        running_instances: List[int] = []

        for instance in pending_instances:
            try:
                status = check_instance_status(instance['instance_id'])
                if status['status'].lower() == "running":
                    running_instances.append(instance['user_project_id'])
            except Exception as e:
                logger.error(f"Error checking status for instance {instance['instance_id']}: {e}")
                # Continue with the next instance

        for user_project_id in running_instances:
            try:
                setup_vps(int(user_project_id))
            except Exception as e:
                logger.error(f"Error setting up VPS for user project {user_project_id}: {e}")
                # Continue with the next instance

        logger.info(
            f"Batch process completed. Checked {len(pending_instances)} instances, {len(running_instances)} are now running.")

        return {
            "checked_instances": len(pending_instances),
            "running_instances": len(running_instances)
        }

    except Exception as e:
        logger.error(f"Unexpected error during batch check process: {e}")
        raise BatchProcessError(f"Batch check process failed: {str(e)}") from e


def initialize_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(
        func=batch_check_instance_status,
        trigger=IntervalTrigger(minutes=15),
        id='batch_check_job',
        name='Check instance status every 15 minutes',
        replace_existing=True)

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())


if __name__ == '__main__':
    batch_check_instance_status()
