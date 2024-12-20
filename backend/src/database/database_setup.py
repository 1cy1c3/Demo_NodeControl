import pyodbc
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
# from src.database.database_exceptions import ProjectCreationError


# Get the APP_SECRET from the .env file
load_dotenv()
MSSQL_CONNECTION_STRING = os.getenv('MSSQL_CONNECTION_STRING')
logger = logging.getLogger(__name__)


class ProjectCreationError(Exception):
    """Custom exception for project creation errors"""
    pass


def add_project(project_name: str, project_image: str, project_instance_type: str, project_version: str, project_network: str):
    try:
        print(type(project_name))

        conn = pyodbc.connect(MSSQL_CONNECTION_STRING)
        cursor = conn.cursor()

        current_time = datetime.now()
        query = """
        INSERT INTO Projectdata (Project_Name, Project_Image, Project_Version, Project_Network, Project_InstanceType, Project_CreationDate, Project_LastModifiedDate)
        OUTPUT INSERTED.Project_IdKey
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """

        cursor.execute(query, (project_name, project_image, project_version, project_network, project_instance_type, current_time, current_time))

        row = cursor.fetchone()
        if not row:
            raise ProjectCreationError("Failed to retrieve project ID after insertion")

        project_id = row[0]

        conn.commit()
        logger.info(f"Project added successfully with ID: {project_id}")
        return project_id

    except pyodbc.Error as e:
        logger.error(f"Database error in add_project: {str(e)}")
        raise ProjectCreationError(f"Database error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error in add_project: {str(e)}")
        raise ProjectCreationError(f"Unexpected error: {str(e)}") from e
    

if __name__ == "__main__":
    try:
        project_id = add_project("elixir", "d64d5c6c-9dda-4e38-8174-0ee282474d8a",
                                 "V46", "1.0.0", "ethereum")
        if project_id is not None:
            print(f"Test project added successfully with ID: {project_id}")
        else:
            print("Failed to get project ID after insertion")
    except pyodbc.Error as e:
        print(f"Error adding test project: {str(e)}")
