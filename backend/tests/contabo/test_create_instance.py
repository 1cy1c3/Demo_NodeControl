import unittest
from unittest.mock import patch, MagicMock
import requests
import queue
from src.contabo.create_instance import (
    get_access_token, create_instance, setup_instance_async, setup_instance,
    check_instance_status, cancel_instance, ContaboAuthError, ContaboInstanceCreationError,
    InstanceCancellationError
)


class TestCreateInstance(unittest.TestCase):

    @patch('src.contabo.create_instance.requests.post')
    def test_get_access_token_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_response

        token = get_access_token()

        self.assertEqual(token, 'test_token')
        mock_post.assert_called_once()

    @patch('src.contabo.create_instance.requests.post')
    def test_get_access_token_failure(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        with self.assertRaises(ContaboAuthError):
            get_access_token()

    @patch('src.contabo.create_instance.get_access_token')
    @patch('src.contabo.create_instance.requests.post')
    @patch('src.contabo.create_instance.generate_password_and_key')
    @patch('src.contabo.create_instance.create_user_project')
    @patch('src.contabo.create_instance.save_encrypted_password')
    def test_create_instance_success(self, mock_save_password, mock_create_project, mock_generate_password, mock_post,
                                     mock_get_token):
        mock_get_token.return_value = 'test_token'
        mock_generate_password.return_value = ('password', 'key')
        mock_create_project.return_value = 'user_project_id'
        mock_save_password.return_value = True

        mock_response = MagicMock()
        mock_response.json.return_value = {'data': [{'instanceId': 'test_instance_id'}]}
        mock_post.return_value = mock_response

        data = {
            'imageId': 'test_image',
            'productId': 'test_product',
            'region': 'EU',
            'period': 1,
            'displayName': 'test_instance',
            'project_id': 'test_project',
            'user_id': 'test_user'
        }

        result = create_instance(data)

        self.assertEqual(result, {'user_project_id': 'user_project_id', 'instance_id': 'test_instance_id'})
        mock_post.assert_called_once()
        mock_create_project.assert_called_once()
        mock_save_password.assert_called_once()

    @patch('src.contabo.create_instance.get_access_token')
    @patch('src.contabo.create_instance.requests.post')
    def test_create_instance_failure(self, mock_post, mock_get_token):
        mock_get_token.return_value = 'test_token'
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        data = {
            'imageId': 'test_image',
            'productId': 'test_product',
            'region': 'EU',
            'period': 1,
            'displayName': 'test_instance',
            'project_id': 'test_project',
            'user_id': 'test_user'
        }

        with self.assertRaises(ContaboInstanceCreationError):
            create_instance(data)

    def test_setup_instance_async(self):
        mock_queue = MagicMock(spec=queue.Queue)
        data = {'test': 'data'}

        with patch('src.contabo.create_instance.create_instance') as mock_create_instance:
            mock_create_instance.return_value = {'instance_id': 'test_id', 'user_project_id': 'test_project_id'}

            setup_instance_async(data, mock_queue)

            mock_create_instance.assert_called_once_with(data)
            mock_queue.put.assert_called_once_with({'instance_id': 'test_id', 'user_project_id': 'test_project_id'})

    @patch('src.contabo.create_instance.threading.Thread')
    def test_setup_instance_success(self, mock_thread):
        mock_queue = MagicMock(spec=queue.Queue)
        mock_queue.get.return_value = {'instance_id': 'test_id', 'user_project_id': 'test_project_id'}

        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        data = {'test': 'data'}
        result = setup_instance(data)

        self.assertEqual(result, {'instance_id': 'test_id', 'user_project_id': 'test_project_id'})
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        mock_thread_instance.join.assert_called_once()

    @patch('src.contabo.create_instance.get_access_token')
    @patch('src.contabo.create_instance.requests.get')
    @patch('src.contabo.create_instance.update_instance_ip')
    def test_check_instance_status_running(self, mock_update_ip, mock_get, mock_get_token):
        mock_get_token.return_value = 'test_token'
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': [{'status': 'running', 'ipConfig': {'v4': {'ip': '1.1.1.1'}}}]}
        mock_get.return_value = mock_response
        mock_update_ip.return_value = True

        result = check_instance_status(123)

        self.assertEqual(result, {'status': 'running', 'ip_address': '1.1.1.1'})
        mock_get.assert_called_once()
        mock_update_ip.assert_called_once_with(instance_id=123, ip_address='1.1.1.1')

    @patch('src.contabo.create_instance.get_access_token')
    @patch('src.contabo.create_instance.requests.post')
    def test_cancel_instance_success(self, mock_post, mock_get_token):
        mock_get_token.return_value = 'test_token'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = cancel_instance(123)

        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('src.contabo.create_instance.get_access_token')
    @patch('src.contabo.create_instance.requests.post')
    def test_cancel_instance_failure(self, mock_post, mock_get_token):
        mock_get_token.return_value = 'test_token'
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        with self.assertRaises(InstanceCancellationError):
            cancel_instance(123)


if __name__ == '__main__':
    unittest.main()