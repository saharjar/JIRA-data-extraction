from src.jirasrc import Jira

jira_instance = Jira(username="sjarboui", password="123321")
print("Jira_instance+\n")
print(jira_instance)
print('\n')
print("Projects+\n")
print(jira_instance.getProjects(False))

Issues = jira_instance.getIssues(maxResults=10, project="CRMST")
for issue in Issues:
    print(issue['Name'])
    for key , value in issue.items():
        print("{} : {}".format(key, value))
allfields = jira_instance.getAllFields()
issue  = jira_instance.getIssues(maxResults=50,raw=True, project="CRMST")

fild = issue[0].raw['fields'].keys()
project_fields_info = [field for field in allfields if field['id'] in fild]
print(project_fields_info)
project = jira_instance.getProject("CRMST")
issue_types = project.issueTypes
issue_types_name = [issue_type.id for issue_type in issue_types]
print(issue_types_name)
fields = set()



