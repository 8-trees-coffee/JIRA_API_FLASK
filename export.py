import csv
from datetime import datetime
from jira import JIRA
import sqlite3
from typing import List, Dict, Optional


COLUMN_KEY = 'KEY'
COLUMN_SUMMARY = 'SUMMARY'
COLUMN_PREV_PROG_RATE = 'PREV PROG RATE'
COLUMN_PROG_RATE = 'PROG RATE'
COLUMN_STATUS = 'STATUS'
# COLUMN_VER = 'VER'
COLUMN_PRIORITY = 'PRIORITY'
COLUMN_DUEDATE = 'DUEDATE'
COLUMN_STORY_POINT = 'STORY POINT'
COLUMN_ASSIGNEE = 'ASSIGNEE'
COLUMN_LAST_CMT = 'LAST CMT'
COLUMN_CMT_UPDATED = 'CMT UPDATED'
COLUMN_PREV_UPDATED = 'PREV UPDATED'
COLUMN_ISSUE_UPDATED = 'ISSUE UPDATED'

column = [
    COLUMN_KEY, COLUMN_SUMMARY, COLUMN_PREV_PROG_RATE, COLUMN_PROG_RATE,
    COLUMN_STATUS, COLUMN_PRIORITY, COLUMN_DUEDATE, COLUMN_STORY_POINT,
    COLUMN_ASSIGNEE, COLUMN_LAST_CMT, COLUMN_CMT_UPDATED, COLUMN_PREV_UPDATED,
    COLUMN_ISSUE_UPDATED
]


def remove_one_status(issues: List[Dict], remove_status: str) -> Optional[Dict]:
    if issues:
        removed_list = [issue for issue in issues if issue['status'] != remove_status]
        return removed_list
    return None

def filter_issuetype(issues: List[Dict], issuetype: str) -> Optional[Dict]:
    if issues:
        filtered_list = [issue for issue in issues if issue['issuetype'] == issuetype]
        return filtered_list
    return None

def get_issues(limit=50):
    jira = JIRA(server='https://jira.atlassian.com')
    if jira:
        issues_in_proj = jira.search_issues(f'project=JRASERVER', maxResults=limit)
        issues_array = []
        for issue in issues_in_proj:
            status = issue.fields.status.name
            
            # issuetype
            issuetype = issue.fields.issuetype.name
            # summary
            summary = issue.fields.summary
            # comment and comment updated
            if len(jira.comments(issue)) > 0:
                comment = jira.comment(issue.key, jira.comments(issue)[-1]).body
                comment_dt = datetime.strptime(
                    jira.comment(issue.key, jira.comments(issue)[-1]).updated,
                    '%Y-%m-%dT%H:%M:%S.%f%z')
                comment_updated = datetime.strftime(comment_dt, '%m/%d')
            else:
                comment = None
                comment_updated = None
            # discription
            # discription = issue.fields.description
            # TODO(r.yagi) add story point
            story_point = 1
            # TODO(r.yagi) add priority
            if issuetype == 'Bug':
                priority = issue.fields.priority.name
            else:
                priority = None
            # duedate
            if issue.fields.duedate:
                duedate_dt = datetime.strptime(issue.fields.duedate, '%Y-%m-%dT%H:%M:%S.%f%z')
                duedate = datetime.strftime(duedate_dt, '%m/%d')
            else:
                duedate = None
            # assignee
            if issue.fields.assignee:
                assignee = issue.fields.assignee.displayName
            else:
                assignee = None
            # TODO(r.yagi) to change progress
            # version
            version = float(issue.fields.customfield_19430) if issue.fields.customfield_19430 else None
            # updated
            updated_dt = datetime.strptime(issue.fields.updated, '%Y-%m-%dT%H:%M:%S.%f%z')
            updated = datetime.strftime(updated_dt, '%m/%d')

            issues_array.append({
                    "key": issue.key,
                    "url": f'https://jira.atlassian.com/browse/{issue.key}',
                    "issuetype": issuetype,
                    "summary": summary,
                    "version": version,
                    "status": status,
                    "priority": priority,
                    "duedate": duedate,
                    "assignee": assignee,
                    # "discription": discription,
                    "story_point": story_point,
                    "comment": comment,
                    "comment_updated": comment_updated,
                    "updated": updated,
                    })
        return issues_array
    return None
 
if __name__ == '__main__':

    conn = sqlite3.connect('jiradata.sql')
    c = conn.cursor()

    # TODO(r.yagi) change sever and id, pw
    jira = JIRA(server='https://jira.atlassian.com')
    issues = filter_issuetype(remove_one_status( get_issues(30), "Closed"), "Bug")

    csv_data = []
    for issue in issues:
        issue['prev_prog_rate'] = None
        issue['prev_updated'] = None
        for prev_data in c.execute("select * from JIRA_ISSUES"):
            if prev_data[0] == issue['key']:
                issue['prev_prog_rate'] = prev_data[1]
                issue['prev_updated'] = prev_data[3]
                csv_data.append(issue)

    file_name = 'jira_table_' + datetime.now().strftime('%Y%m%d') + '.csv'

    with open(file_name, 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=column)
        writer.writeheader()

        for data in csv_data:
            writer.writerow({
                COLUMN_KEY: data['key'],
                COLUMN_SUMMARY: data['summary'],
                COLUMN_PREV_PROG_RATE: data['prev_prog_rate'],
                COLUMN_PROG_RATE: data['version'],     # TODO(r.yagi) change prog_rate
                COLUMN_STATUS: data['status'],
                COLUMN_PRIORITY: data['priority'],
                COLUMN_DUEDATE: data['duedate'],
                COLUMN_STORY_POINT: data['story_point'],
                COLUMN_ASSIGNEE: data['assignee'],
                COLUMN_LAST_CMT: data['comment'],
                COLUMN_CMT_UPDATED: data['comment_updated'],
                COLUMN_PREV_UPDATED: data['prev_updated'],
                COLUMN_ISSUE_UPDATED: data['updated']
            })
    print(f'{len(csv_data)} done')