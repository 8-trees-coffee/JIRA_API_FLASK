import configparser


conf = configparser.ConfigParser()
conf.read('settings.ini')

jira_server = conf['jira']['server']
jira_proj = conf['jira']['project']

db_name = conf['db']['name']
db_driver = conf['db']['driver']

web_port = int(conf['web']['port'])