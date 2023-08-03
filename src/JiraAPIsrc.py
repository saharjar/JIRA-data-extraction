import requests
import mysql.connector
from requests.auth import HTTPBasicAuth


class JiraAPI:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.auth = HTTPBasicAuth(username, password)

    def make_request(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params, auth=self.auth)
            response.raise_for_status()
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def getProjects(self, raw=False):
        endpoint = "rest/api/2/project"
        data = self.make_request(endpoint)
        Projects = []
        for project in data:
            if raw:
                Projects.append(project)
            else:
                Projects.append(
                    ({"Name": project["key"], "Description": project["name"]})
                )
        return Projects

    def getAllFields(self):
        endpoint = "rest/api/2/field"
        return self.make_request(endpoint)

    def getIssueTypes(self, project_key):
        endpoint = f"rest/api/2/issue/createmeta/{project_key}/issuetypes"
        return self.make_request(endpoint)

    def getIssueTypesIds(self, project_key):
        endpoint = f"rest/api/2/issue/createmeta/{project_key}/issuetypes"
        data = self.getIssueTypes(project_key)
        Ids = []
        for issuetype in data["values"]:
            Ids.append(issuetype["id"])
        return Ids

    def getIssueFields(self, project_key, issue_type_id):
        endpoint = (
            f"rest/api/2/issue/createmeta/{project_key}/issuetypes/{issue_type_id}"
        )
        data = self.make_request(endpoint)
        fields = data["values"]
        return fields

    def getProjectIssues(self, project_key, max_results=50, raw=False):
        endpoint = f"rest/api/2/search"
        params = {"jql": f"project={project_key}", "maxResults": max_results}
        data = self.make_request(endpoint, params)

        return data

    def get_field_values_per_issue(self, project_key):
        project_issues = self.getProjectIssues(project_key)
        issues_fields = []
        if project_issues and "issues" in project_issues:
            issues_list = project_issues["issues"]

            for issue in issues_list:
                issue_fields = []
                fields = issue.get("fields", {})
                for field_id, field_value in fields.items():
                    issue_fields.append(
                        {f"Field ID: {field_id}, Field Value: {field_value}"}
                    )
                issues_fields.append(issue_fields)
        return issues_fields

    def getProjectFields(self, project_key, raw=False):
        issue_types_ids = self.getIssueTypesIds(project_key)
        fields = []
        fields_ids = []
        for issue_type_id in issue_types_ids:
            data = self.getIssueFields(project_key, issue_type_id)
            for field in data:
                if field["fieldId"] not in fields_ids:
                    if raw:
                        fields.append(field)
                    else:
                        fields.append(
                            {"fieldId": field["fieldId"], "schema": field["schema"]}
                        )
                    fields_ids.append((field["fieldId"]))
        return fields

    def CreteProjectTabels(self, db_connection):
        Projects = self.getProjects()
        for project in Projects:
            fields = self.getProjectFields(project_key=project["Name"])
            table_name = f"table_{project['Name'].lower()}"
            sql_query = f"CREATE TABLE IF NOT EXISTS {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, "

            # Create a dictionary to store field types keyed by field ID
            field_types = {}

            for field in fields:
                field_id = field["fieldId"]
                field_type = field["schema"]["type"]
                field_types[field_id] = field_type
                type = self.get_mysql_field_type(field_type)

                sql_query += f"{field_id} {type}, "
            sql_query = sql_query.rstrip(", ") + ");"

            try:
                cursor = db_connection.cursor()
                cursor.execute(sql_query)
                db_connection.commit()
                print(f"Table {table_name} created successfully.")
            except mysql.connector.Error as e:
                print(f"Error creating table {table_name}: {e}")
            finally:
                cursor.close()

            # Retrieve the field values of each issue for the project
            issue_field_values = self.get_field_values_per_issue(project["Name"])

            for field_values in issue_field_values:
                self.store_issue_data_in_table(
                    project["Name"], field_values, db_connection
                )

    def store_issue_data_in_table(self, project_key, field_values, db_connection):
        table_name = f"table_{project_key.lower()}"
        field_types = self.getProjectFields(project_key, raw=True)

        insert_query = f"INSERT INTO {table_name} ("

        for field_id in field_values:
            # Check if the field ID exists in the project table
            if field_id in field_types:
                insert_query += f"{field_id}, "

        insert_query = insert_query.rstrip(", ") + ") VALUES ("

        values = []

        for field_id in field_values:
            # Check if the field ID exists in the project table
            if field_id in field_types:
                insert_query += "%s, "
                values.append(field_values[field_id])

        insert_query = insert_query.rstrip(", ") + ");"

        try:
            cursor = db_connection.cursor()
            cursor.execute(insert_query, values)
            db_connection.commit()
            print(f"Data for project '{project_key}' stored successfully.")
        except mysql.connector.Error as e:
            print(f"Error storing data for project '{project_key}': {e}")
        finally:
            cursor.close()

    def get_mysql_field_type(self, field_type):
        # Map Jira field types to MySQL field types
        if field_type == "string":
            return "VARCHAR(255)"
        elif field_type == "array":
            return "TEXT"
        elif field_type == "priority":
            return "VARCHAR(50)"
        elif field_type == "issuetype":
            return "VARCHAR(50)"
        elif field_type == "date":
            return "DATE"
        elif field_type == "number":
            return "INT"
        else:
            return "TEXT"
