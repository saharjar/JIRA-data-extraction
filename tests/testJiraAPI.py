from src.JiraAPIsrc import JiraAPI
import mysql.connector
base_url = "http://localhost:8080"
username = "sjarboui"
password = "123321"
instance = JiraAPI(base_url, username, password)
# print("Issue types data")
# print(instance.getIssueTypes("CRMST"))
# print("Issue types Ids  ")
# print(instance.getIssueTypesIds("CRMST"))
# print("Project fields ")
# print(instance.getProjectFields("CRMST"))
Projects = instance.getProjects()

#conn = mysql.connector.connect(
    #host="localhost",
    #user="root",

    #database="test_db"
#)
#instance.CreteProjectTabels(conn)
#conn.close
print(instance.get_field_values_per_issue("CRMST"))




