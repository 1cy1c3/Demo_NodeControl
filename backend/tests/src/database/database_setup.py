import pyodbc
from datetime import datetime
import os
from dotenv import load_dotenv


# Get the APP_SECRET from the .env file
load_dotenv()
MSSQL_CONNECTION_STRING = os.getenv('MSSQL_CONNECTION_STRING')


def add_project(project_name, project_image, project_instance_type):
    conn = pyodbc.connect(MSSQL_CONNECTION_STRING)
    cursor = conn.cursor()

    try:
        current_time = datetime.now()
        query = """
        INSERT INTO Projectdata (Project_Name, Project_Image, Project_InstanceType, Project_CreationDate, Project_LastModifiedDate)
        OUTPUT INSERTED.ProjectId_Key
        VALUES (?, ?, ?, ?, ?);
        """

        cursor.execute(query, (project_name, project_image, project_instance_type, current_time, current_time))

        row = cursor.fetchone()
        print(f"Inserted row ID: {row}")

        project_id = row[0] if row else None

        conn.commit()
        print("Transaction committed")
    except pyodbc.Error as e:
        print(f"Error in add_project: {str(e)}")
        project_id = None

    finally:
        cursor.close()
        conn.close()

    return project_id


if __name__ == "__main__":
    try:
        project_id = add_project('Test Project 3', 'test-image-3.iso', 'V3')
        if project_id is not None:
            print(f"Test project added successfully with ID: {project_id}")
        else:
            print("Failed to get project ID after insertion")
    except pyodbc.Error as e:
        print(f"Error adding test project: {str(e)}")
