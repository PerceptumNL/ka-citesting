from flask import Flask, Response
from flask import render_template, send_from_directory
from config import *
import logging
import subprocess
import time
import json
import os
from os import listdir
from datetime import datetime
from os.path import isfile, join
app = Flask(__name__)
app.debug = True

#import utils
import sys
sys.path.insert(0, KHAN_REPO_PATH)
from tools import runtests 

TEST_REPORTS_PATH = os.path.join(KHAN_REPO_PATH, "test_reports")

def get_test_reports():
    mypath = TEST_REPORTS_PATH
    onlyfiles = [ f.replace(".html", "") for f in listdir(mypath) if isfile(join(mypath,f)) and "html" in f]
    return onlyfiles

def load_json_report(t):
    try:
        f=open(os.path.join(TEST_REPORTS_PATH, "%s.json" % t)) 
        return json.load(f)
    except:
        return {}

def get_test_reports_dict():
    from git import Repo
    repo = Repo(KHAN_REPO_PATH)
    commits = repo.iter_commits('master', max_count=100)

    test_reports=get_test_reports()

    reports = []
    for c in commits:
        if not c.hexsha in test_reports: continue
        reports.append({"author_name": c.author.name,
                        "author_email": c.author.email,
                        "authored_date": datetime.fromtimestamp(c.authored_date),
                        "message": c.message,
                        "commit": c.hexsha,
                        "results": load_json_report(c.hexsha)} )
    return reports

@app.route('/')
def index():
    return render_template('index.html', test_reports_dict=get_test_reports_dict())

@app.route('/report/<string:filename>')
def report(filename):
    return send_from_directory(TEST_REPORTS_PATH, filename)

@app.route('/git_pull')
def git_pull():
    from git import Repo
    import json
    repo = Repo(KHAN_REPO_PATH)
    repo.heads.master.checkout() 
    repo.remotes.origin.pull()
    repo.heads.master.checkout() 
    base_filename = repo.head.commit.hexsha

    os.system("/home/ubuntu/citesting/app/runtests %s" % base_filename)
    try:
        f=open(os.path.join(TEST_REPORTS_PATH, base_filename + ".json"))
        ret=json.load(f)
        ret["json_exists"] = True
        f.close
    except:
        f=open(os.path.join(TEST_REPORTS_PATH, base_filename + ".json"), "wb")
        ret={"json_exists": False}
        f.write(json.dumps(ret))
        f.close()

    return json.dumps(ret)
        

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
