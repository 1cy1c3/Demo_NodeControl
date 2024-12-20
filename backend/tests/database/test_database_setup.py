import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.database.database_setup import add_project
from src.database.database_exceptions import ProjectCreationError


class TestDatabaseSetup(unittest.TestCase):

    @patch('src.database.database_setup.pyodbc.connect')
    def test_add_project_success(self, mock_connect):
        # Setup
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1]  # Simulating the returned project ID
        mock_connect.return_value.cursor.return_value = mock_cursor

        # Execute
        project_id = add_project('Test Project', 'test-image.iso', 'V1')

        # Assert
        self.assertEqual(project_id, 1)
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_connect.return_value.commit.assert_called_once()

    @patch('src.database.database_setup.pyodbc.connect')
    def test_add_project_database_error(self, mock_connect):
        # Setup
        mock_connect.side_effect = ProjectCreationError("Database error occurred")

        # Execute and Assert
        with self.assertRaises(ProjectCreationError) as context:
            add_project('Test Project', 'test-image.iso', 'V1')

        self.assertEqual(str(context.exception), "Database error occurred")

    @patch('src.database.database_setup.pyodbc.connect')
    def test_add_project_no_id_returned(self, mock_connect):
        # Setup
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Simulating no project ID returned
        mock_connect.return_value.cursor.return_value = mock_cursor

        # Execute and Assert
        with self.assertRaises(ProjectCreationError) as context:
            add_project('Test Project', 'test-image.iso', 'V1')

        self.assertEqual(str(context.exception), "Failed to retrieve project ID after insertion")

    @patch('src.database.database_setup.pyodbc.connect')
    @patch('src.database.database_setup.datetime')
    def test_add_project_correct_query(self, mock_datetime, mock_connect):
        # Setup
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1]
        mock_connect.return_value.cursor.return_value = mock_cursor
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)

        # Execute
        add_project('Test Project', 'test-image.iso', 'V1')

        # Assert
        expected_query = """
        INSERT INTO Projectdata (Project_Name, Project_Image, Project_InstanceType, Project_CreationDate, Project_LastModifiedDate)
        OUTPUT INSERTED.ProjectId_Key
        VALUES (?, ?, ?, ?, ?);
        """
        mock_cursor.execute.assert_called_once_with(
            expected_query,
            ('Test Project', 'test-image.iso', 'V1', datetime(2023, 1, 1, 12, 0, 0), datetime(2023, 1, 1, 12, 0, 0))
        )


if __name__ == '__main__':
    unittest.main()
