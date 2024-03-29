from github import Github, RateLimitExceededException
import github.GithubObject
from myTokens import Tokens
import datetime
from math import ceil
from multiprocessing import Pool, Queue, current_process
from multiprocessing.pool import ThreadPool
from multiprocessing import Process, Manager
from time import sleep
import os
import multiprocessing
# We must import this explicitly, it is not imported by the top-level
# multiprocessing module.
import multiprocessing.pool
import time
import itertools
from copy import deepcopy
import csv

import sys
import json
from csv import reader, writer
import hashlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dateutil import parser

class NoDaemonProcess(multiprocessing.Process):
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass

    daemon = property(_get_daemon, _set_daemon)

class MyPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess

tokens = Tokens()
tokens_iter = tokens.iterator()

tokens_queue = Queue()
for token in tokens_iter:
    tokens_queue.put(token)


def getRateLimit(g):
    return g.rate_limiting


def computeSleepDuration(g):
    reset_time = datetime.datetime.fromtimestamp(g.rate_limiting_resettime)
    curr_time = datetime.datetime.now()
    delta = int(ceil((reset_time - curr_time).total_seconds()))
    if delta > 0:
        return delta
    return 60


def waitIfDepleted(g):
    (remaining, _limit) = getRateLimit(g)
    sleep_duration = computeSleepDuration(g)
    if not remaining > 20:
        print(datetime.datetime.fromtimestamp(g.rate_limiting_resettime))
        # session.commit()
        sleep(sleep_duration)


def waitAndGetRepo(g, slug):
    waitIfDepleted(g)
    return g.get_repo(slug)


def parseIssue(g, issue):
    issue_id = issue.id  # int
    issue_number = issue.number  # int
    state = issue.state  # string
    created_at = str(issue.created_at)  # datetime
    closed_at = str(issue.closed_at)  # datetime
    # updated_at

    created_by = issue.user  # NamedUser
    created_by_login = None
    if created_by is not None:
        #         created_by = g.get_user(issue.user.login)
        created_by_login = created_by.login

    closed_by = issue.closed_by  # NamedUser
    closed_by_login = None
    if closed_by is not None:
        #         closed_by = g.get_user(issue.closed_by.login) # NamedUser
        closed_by_login = closed_by.login

    assignee = issue.assignee  # NamedUser
    assignee_login = None
    if assignee is not None:
        #         assignee = g.get_user(issue.assignee.login) # NamedUser
        assignee_login = assignee.login

    title = issue.title.strip().replace("\n", "").replace("\r", "")  # string
    body = issue.body  # string
    num_comments = issue.comments  # int
    # url
    # comments_url
    # events_url
    # html_url
    labels = ','.join([l.name for l in issue.labels])  # [Label]

    # labels_url =
    # milestone
    pull_request = issue.pull_request  # IssuePullRequest
    pr_html_url = None
    pr_num = None
    if pull_request is not None:
        pr_html_url = pull_request.html_url
        pr_num = pr_html_url.split('/')[-1]
    # repository

    issueData = [issue_id,
                 issue_number,
                 state,
                 created_at,
                 closed_at,
                 created_by_login,
                 closed_by_login,
                 assignee_login,
                 title,
                 body,
                 num_comments,
                 labels,
                 pr_num]

    waitIfDepleted(g)

    return issueData

def parseComment(g, comment):
    comment_id = comment.id  # int
    created_at = str(comment.created_at)  # datetime
    updated_at = str(comment.updated_at)  # datetime
    created_by = comment.user  # NamedUser
    created_by_login = None
    if created_by is not None:
        created_by_login = created_by.login
    body = comment.body  # string

    commentData = [comment_id,
                 created_at,
                 updated_at,
                 created_by_login,
                 body]

    waitIfDepleted(g)

    return commentData

def dec(g, func):
    while True:
        yield (g, next(func))


def fetchIssues(rs):
    # slug = dbrepo.slug
    (repo_id, slug) = rs
    pid = current_process().pid
    issues = []
    issueComments = []

    print('Processing: ' + slug)

    try:
        token = tokens_map[pid]

        g = Github(token)

        waitIfDepleted(g)
        repo = g.get_repo(slug)

        if repo.has_issues:
            for issue in repo.get_issues(state=u"closed"):
                issueData = parseIssue(g, issue)

                issue_id = issueData[0]
                issues.append(issueData)

                waitIfDepleted(g)

            for issue in repo.get_issues(state=u"open"):
                issueData = parseIssue(g, issue)

                issue_id = issueData[0]
                issues.append(issueData)

                waitIfDepleted(g)

    except Exception as e:
        return (repo_id, slug, pid, None, issues, str(e).strip().replace("\n", " ").replace("\r", " "))


    return (repo_id, slug, pid, token, issues, None)


manager = Manager()
tokens_map = manager.dict()


def initializer():
    token = tokens_queue.get()
    pid = current_process().pid
    tokens_map[pid] = token


proj = list()
with open("top50k_projects.csv") as proj_list:
    lines = csv.reader(proj_list, delimiter=',')
    for line in lines:
        proj.append((line[0], line[1]))
list.reverse(proj)

pool = MyPool(processes=tokens.length(), initializer=initializer, initargs=())

logwriter = open('issue_error.csv', 'w')

for result in pool.imap_unordered(fetchIssues, proj):
    (repo_id, slug, pid, token, issues, err) = result
    # slug = repo.slug
    # repo_id = repo.id
    if err is not None:
        logwriter.write(slug+","+err)
    else:
            for issue in issues:
                [issue_id, issue_number, state, created_at, closed_at,
                 created_by_login, closed_by_login, assignee_login, title,
                 body, num_comments, labels, pr_num] = issue
                delim = ",,,,"
                issueline = repo_id + delim
                for (_, x) in enumerate(issue):
                    if not isinstance(x, unicode):
                        x = str(x)
                    else:
                        x = repr(x)
                    issueline += x + delim
                issueline = issueline[0:-len(delim)] + "\n"
                f.write(issueline)
    count += 1
    print(count)
