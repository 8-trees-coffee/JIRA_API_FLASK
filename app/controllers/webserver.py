from datetime import datetime
import logging

from flask import flash
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from jiraapi.jiraapi import APIClient
from app.models.accout import Account
from app.models.issues import JiraIssue
from app.models.forms import LoginForm
import settings


logger = logging.getLogger(__name__)
app = Flask(__name__,static_folder='../static', template_folder='../views')
app.config['SECRET_KEY'] = b'\xe0\x9ed\\\xbaP\xfd\xba\x8b\xcdC\x1bV:p\xef\x0fp\xa2\x0cI\xb3k\xd3\r\x9a\x8a\xbc\x9e/;\xb1'

@app.teardown_appcontext
def remove_session(ex=None):
    from app.models.base import Session
    Session.remove()

@app.route('/login', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def login():
    app.logger.info('login')
    form = LoginForm(request.form)
    if request.method == 'POST':
        id = request.form["login_id"]
        pw = request.form["password"]
        app.logger.info({'id': id, 'pw': pw})
        jira = APIClient(id=id, pw=pw)
        if jira:
            app.logger.info({'action': 'login', 'status': 'access'})
            is_id = Account.get(id)

            if is_id is None:
                # register accounts db
                is_create = Account.create(id=id, pw=pw)
                if is_create:
                    app.logger.info({'action': 'login', 'status': 'success'})
                else:
                    app.logger.warning({'action': 'login', 'status': 'failed create date'})
                    return render_template('/login.html', form=form)
            else:
                # account data update if password changed
                if is_id.pw != pw:
                    is_id.pw = pw
                    is_id.update_at = datetime.now()
                    is_id.save()

            return redirect(url_for('home', id=id))
        else:
            app.logger.warning({'action': 'login', 'status': 'failed login'})
            return render_template('/login.html', form=form)
    return render_template('/login.html', form=form)


@app.route('/home/<string:id>')
def home(id):
    app.logger.info('home')
    account = Account.get(id)
    jira = APIClient(id=account.id, pw=account.pw)
    if jira:
        limit = request.args.get('limit', type=int)
        app.logger.info({'limit': limit})
        if limit is None or limit < 1:
            limit = 50
        issues = jira.filter_issuetype(
                    jira.remove_one_status(
                        jira.get_issues(limit=limit), 'Closed'), 'Bug')
        if issues:
            len_issues = len(issues)
        else:
            len_issues = 0
        agn_story_point = jira.agn_story_point(issues)
        app.logger.info(f'agn_story_point: {agn_story_point}')
        base_issues = JiraIssue.get_all()
        return render_template(
            './home.html',
            id=id,
            issues=issues,
            limit=limit,
            len_issues=len_issues,
            base_issues=base_issues,
            agn_story_point=agn_story_point)
    else:
        logger.warning({'action': 'home', 'status': 'failed login'})
        return redirect(url_for('login'))

@app.route('/update/prev_prog/<string:id>')
def update_prev_prog(id):
    # get the latest JIRA issues data
    account = Account.get(id)
    jira = APIClient(id=account.id, pw=account.pw)
    if jira:
        # reset all prev progress data
        JiraIssue.delete_all()
        app.logger.info('delete all data')
        limit = request.args.get('prev_prog_limit', type=int)
        app.logger.info({'prev_prog_limit': limit})
        if limit is None or limit < 1:
            limit = 50
        issues = jira.filter_issuetype(
                    jira.remove_one_status(
                        jira.get_issues(limit=limit), 'Closed'), 'Bug')
        flash(f'prov preg rate updated: {len(issues)}(num of searches: {limit})')
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

@app.errorhandler(401)
def unauthorized_error(e):
    return render_template('401.html'), 401

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(503)
def service_unavailable(e):
    return render_template('503.html'), 503

def start():
    app.run(host='0.0.0.0', port=settings.web_port, threaded=True, debug=False)