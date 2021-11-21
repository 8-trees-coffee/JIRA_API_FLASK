from datetime import datetime
import logging
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from jiraapi.jiraapi import APIClient
from app.models.accout import Account
from app.models.issues import JiraIssue
import settings


logger = logging.getLogger(__name__)
app = Flask(__name__,static_folder='../static', template_folder='../views')


@app.teardown_appcontext
def remove_session(ex=None):
    from app.models.base import Session
    Session.remove()

@app.route('/login', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def login():
    app.logger.info('login')
    if request.method == 'POST':
        id = request.form["login_id"]
        pw = request.form["password"]
        limit = 0
        app.logger.info({'id': id, 'pw': pw})
        jira = APIClient(id=id, pw=pw)
        if jira:
            app.logger.info({'action': 'login', 'status': 'access'})
            is_id = Account.get(id)

            if is_id is None:
                # registe db of account
                is_create = Account.create(id=id, pw=pw)
                if is_create:
                    app.logger.info({'action': 'login', 'status': 'success'})
                else:
                    app.logger.warning({'action': 'login', 'status': 'failed create date'})
                    return render_template('/login.html')
            else:
                # account data update if password changed
                if is_id.pw != pw:
                    is_id.pw = pw
                    is_id.update_at = datetime.now()
                    is_id.save()

            return redirect(url_for('home', id=id, limit=limit))
        else:
            app.logger.warning({'action': 'login', 'status': 'failed login'})
            return render_template('/login.html')
    return render_template('/login.html')


@app.route('/home/<string:id>')
def home(id):
    app.logger.info('home')
    account = Account.get(id)
    jira = APIClient(id=account.id, pw=account.pw)
    if jira:
        # TODO(r.yagi) get limit from front end.
        # limit = request.args.get('limit', type=int)
        # app.logger.info({'limit': limit})
        # if limit is None or limit < 1:
        #     limit = 50
        issues = jira.filter_issuetype_by_task(
                    jira.remove_closed_status(
                        jira.get_issues(limit=limit)))
        len_issues = len(issues)
        agn_story_point = jira.agn_story_point(issues)
        app.logger.info(f'agn_story_point: {agn_story_point}')
        base_issues = JiraIssue.get_all()
        return render_template(
            './home.html',
            id=id,
            issues=issues,
            len_issues=len_issues,
            base_issues=base_issues,
            agn_story_point=agn_story_point)
    else:
        logger.warning({'action': 'home', 'status': 'failed login'})
        return render_template('./login.html')

@app.route('/update/prev_prog/<string:id>')
def update_prev_prog(id):
    # get the latest JIRA issues data
    account = Account.get(id)
    jira = APIClient(id=account.id, pw=account.pw)
    if jira:
        # reset all prev progress data
        JiraIssue.delete_all()
        app.logger.info('delete all data')
        issues = jira.filter_issuetype_by_task(
                    jira.remove_closed_status(
                        jira.get_issues()))
    else:
        logger.warning({'action': 'update_prev_prog', 'status': 'failed login'})
        return redirect(url_for('login'))

    # create prev progress data
    if issues:
        for issue in issues:
            JiraIssue.create(issue['key'], issue['version'])
            app.logger.info('create {} data'.format(issue['key']))
        return redirect(url_for('home', id=id))
    else:
        app.logger.warning({'action': 'update_prev_prog', 'issues': None})
        return redirect(url_for('home', id=id))

def start():
    app.run(host='0.0.0.0', port=settings.web_port, threaded=True)