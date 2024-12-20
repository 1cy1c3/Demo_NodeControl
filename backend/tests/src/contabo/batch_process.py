import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.contabo.create_instance import check_instance_status
from src.database.database import fetch_pending_instances
from src.vps.connect_vps import setup_vps


def batch_check_instance_status():
    """
    Batch process to check instance statuses and update database.
    """
    pending_instances = fetch_pending_instances()
    running_instances = []

    for instance in pending_instances:
        print(instance)
        status = check_instance_status(instance['instance_id'])
        if status == "running":
            running_instances.append(instance['user_project_id'])

    for user_project_id in running_instances:
        setup_vps(int(user_project_id))

    print(
        f"Batch process completed. Checked {len(pending_instances)} instances, {len(running_instances)} are now running.")


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
