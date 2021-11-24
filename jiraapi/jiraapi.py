import logging
from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional

from flask import abort
from jira import JIRA
from jira.exceptions import JIRAError

import settings


logger = logging.getLogger(__name__)


class APIClient(object):
    def __init__(self, id, pw):
        self.id = id
        self.pw = pw
        self.jira = self.access()

    def access(self):
        try:
            jira = JIRA(server=settings.jira_server)
            logger.info({'id': self.id, 'pw': self.pw})
        except JIRAError as e:
            logger.error({'action': 'access', 'error': e})
            if e.status_code == 401:
                abort(401)
            if e.status_code == 404:
                abort(404)
            if e.status_code == 500:
                abort(500)
            if e.status_code == 503:
                abort(503)
            return False
        return jira

    def get_issues(self, limit=50):
        if self.jira:
            issues_in_proj = self.jira.search_issues(f'project={settings.jira_proj}', maxResults=limit)
            issues_array = []
            for issue in issues_in_proj:
                status = issue.fields.status.name
                
                # issuetype
                issuetype = issue.fields.issuetype.name
                # summary
                summary = issue.fields.summary
                # comment and comment updated
                if len(self.jira.comments(issue)) > 0:
                    comment = self.jira.comment(issue.key, self.jira.comments(issue)[-1]).body
                    comment_dt = datetime.strptime(
                        self.jira.comment(issue.key, self.jira.comments(issue)[-1]).updated,
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
                        "url": f'{settings.jira_server}/browse/{issue.key}',
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
           
    def agn_story_point(self, issues: List[Dict]) -> Optional[Dict]:
        """aggregate story point"""
        if issues:
            story_point = {}
            for issue in issues:
                if not issue['assignee'] in story_point.keys():
                    story_point[issue['assignee']] = issue['story_point']
                else:
                    story_point[issue['assignee']] += issue['story_point']
            return story_point
        return None

    def remove_one_status(self, issues: List[Dict], remove_status: str) -> Optional[Dict]:
        if issues:
            removed_list = [issue for issue in issues if issue['status'] != remove_status]
            return removed_list
        return None

    def filter_issuetype(self, issues: List[Dict], issuetype: str) -> Optional[Dict]:
        if issues:
            filtered_list = [issue for issue in issues if issue['issuetype'] == issuetype]
            return filtered_list
        return None

# https://jira.atlassian.com/rest/api/latest/search?jql=project=JRASERVER&maxResults=10
# https://jira.atlassian.com/rest/api/latest/issue/JRA-8 