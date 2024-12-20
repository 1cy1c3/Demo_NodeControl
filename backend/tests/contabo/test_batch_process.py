import unittest
from unittest.mock import patch, MagicMock
from src.contabo.batch_process import batch_check_instance_status, initialize_scheduler
from src.contabo.contabo_exceptions import BatchProcessError


class TestBatchProcess(unittest.TestCase):

    @patch('src.contabo.batch_process.fetch_pending_instances')
    @patch('src.contabo.batch_process.check_instance_status')
    @patch('src.contabo.batch_process.setup_vps')
    def test_batch_check_instance_status_success(self, mock_setup_vps, mock_check_status, mock_fetch_instances):
        # Setup
        mock_fetch_instances.return_value = [
            {'instance_id': '1', 'user_project_id': '101'},
            {'instance_id': '2', 'user_project_id': '102'}
        ]
        mock_check_status.side_effect = [
            {'status': 'running'},
            {'status': 'pending'}
        ]

        # Execute
        result = batch_check_instance_status()

        # Assert
        self.assertEqual(result, {"checked_instances": 2, "running_instances": 1})
        mock_fetch_instances.assert_called_once()
        self.assertEqual(mock_check_status.call_count, 2)
        mock_setup_vps.assert_called_once_with(101)

    @patch('src.contabo.batch_process.fetch_pending_instances')
    @patch('src.contabo.batch_process.check_instance_status')
    @patch('src.contabo.batch_process.setup_vps')
    def test_batch_check_instance_status_with_errors(self, mock_setup_vps, mock_check_status, mock_fetch_instances):
        # Setup
        mock_fetch_instances.return_value = [
            {'instance_id': '1', 'user_project_id': '101'},
            {'instance_id': '2', 'user_project_id': '102'}
        ]
        mock_check_status.side_effect = [
            Exception("API Error"),
            {'status': 'running'}
        ]
        mock_setup_vps.side_effect = Exception("Setup Error")

        # Execute
        result = batch_check_instance_status()

        # Assert
        self.assertEqual(result, {"checked_instances": 2, "running_instances": 1})
        mock_fetch_instances.assert_called_once()
        self.assertEqual(mock_check_status.call_count, 2)
        mock_setup_vps.assert_called_once_with(102)

    @patch('src.contabo.batch_process.fetch_pending_instances')
    def test_batch_check_instance_status_fail(self, mock_fetch_instances):
        # Setup
        mock_fetch_instances.side_effect = Exception("Database Error")

        # Execute and Assert
        with self.assertRaises(BatchProcessError):
            batch_check_instance_status()

    @patch('src.contabo.batch_process.BackgroundScheduler')
    def test_initialize_scheduler(self, mock_scheduler):
        # Setup
        mock_scheduler_instance = MagicMock()
        mock_scheduler.return_value = mock_scheduler_instance

        # Execute
        initialize_scheduler()

        # Assert
        mock_scheduler_instance.start.assert_called_once()
        mock_scheduler_instance.add_job.assert_called_once()
        self.assertEqual(mock_scheduler_instance.add_job.call_args[1]['func'], batch_check_instance_status)

        # Check the total seconds instead of minutes
        interval = mock_scheduler_instance.add_job.call_args[1]['trigger'].interval
        self.assertEqual(interval.total_seconds(), 15 * 60)  # 15 minutes in seconds


if __name__ == '__main__':
    unittest.main()
