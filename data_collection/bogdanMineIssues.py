from github import Github, RateLimitExceededException
import github.GithubObject
from apiTokens import Tokens
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

import sys
import urllib.request
import json
from csv import reader, writer
# from unicodeManager import UnicodeReader, UnicodeWriter
import hashlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unidecode import unidecode
from caseyDB import Base, initDB, GhIssue, GhIssueComment, Repo, GhIssueCount
# from travisDB import repo_decoder #, Base, initDB cleanStart,
# from travisDB import TravisRepo #, TravisCommit, TravisJob, TravisBuild, GhIssue
from dateutil import parser

# tokens = Tokens()
# tokens_iter = tokens.iterator()
#
# for token in tokens_iter:
#     g = Github(token)
#     try:
#         repo = g.get_repo("CMUSTRUDEL/cmustrudel.github.io")
#         print(token)
#         print('\t' + repo.has_issues)
#         print('\t' + g.rate_limiting)
#     except RateLimitExceededException:
#         print(token)
#         print('\t' + "API rate limit exceeded")
#
# exit()

engine = create_engine('mysql://bogdanv@localhost/casey_szz?charset=utf8mb4')

# Create the table structure
initDB(engine)

# Create an engine and get the metadata
# Base = declarative_base(engine)
metadata = Base.metadata

# Create a session for this conference
Session = sessionmaker(engine)
session = Session()


class NoDaemonProcess(multiprocessing.Process):
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass

    daemon = property(_get_daemon, _set_daemon)


class MyPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess


# token = tokens[0]

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
    #     created_by_name = None
    #     created_by_email = None
    if created_by is not None:
        #         created_by = g.get_user(issue.user.login)
        created_by_login = created_by.login
    #         created_by_name = created_by.name
    #         created_by_email = created_by.email

    closed_by = issue.closed_by  # NamedUser
    closed_by_login = None
    #     closed_by_name = None
    #     closed_by_email = None
    if closed_by is not None:
        #         closed_by = g.get_user(issue.closed_by.login) # NamedUser
        closed_by_login = closed_by.login
    #         closed_by_name = closed_by.name
    #         closed_by_email = closed_by.email

    assignee = issue.assignee  # NamedUser
    assignee_login = None
    #     assignee_name = None
    #     assignee_email = None
    if assignee is not None:
        #         assignee = g.get_user(issue.assignee.login) # NamedUser
        assignee_login = assignee.login
    #         assignee_name = assignee.name
    #         assignee_email = assignee.email

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
                 # created_by_name,
                 # created_by_email,
                 closed_by_login,
                 # closed_by_name,
                 # closed_by_email,
                 assignee_login,
                 # assignee_name,
                 # assignee_email,
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

    if slug in seen:
        print('  Skipping: ' + slug)
        return (repo_id, slug, pid, None, issues, issueComments, 'Skipped')

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

                for comment in issue.get_comments():
                    commentData = [issue_id] + parseComment(g, comment)

                    waitIfDepleted(g)

                    reactions = []
                    for reaction in comment.get_reactions():
                        reactions.append(str(reaction.content))

                        waitIfDepleted(g)

                    commentData.append(','.join(reactions))

                    issueComments.append(commentData)


                # with open('issue-bodies/%d.txt' % issue_id, 'w') as f:
                #     f.write(body.encode("utf-8"))

            for issue in repo.get_issues(state=u"open"):
                issueData = parseIssue(g, issue)

                issue_id = issueData[0]
                issues.append(issueData)

                waitIfDepleted(g)

                for comment in issue.get_comments():
                    commentData = [issue_id] + parseComment(g, comment)

                    waitIfDepleted(g)

                    reactions = []
                    for reaction in comment.get_reactions():
                        reactions.append(str(reaction.content))

                        waitIfDepleted(g)

                    commentData.append(','.join(reactions))

                    issueComments.append(commentData)

                # with open('issue-bodies/%d.txt' % issue_id, 'w') as f:
                #     f.write(body.encode("utf-8"))

    except Exception as e:
        return (repo_id, slug, pid, None, issues, issueComments, str(e).strip().replace("\n", " ").replace("\r", " "))

    #     print token, getRateLimit(g)

    return (repo_id, slug, pid, token, issues, issueComments, None)


manager = Manager()
tokens_map = manager.dict()


def initializer():
    token = tokens_queue.get()
    pid = current_process().pid
    tokens_map[pid] = token


output_folder = os.path.abspath('/ssd1/bogdan/issues/')
log_writer = writer(open(os.path.join(output_folder, 'mineissues-casey-log.csv'), 'a'))
writer = writer(open(os.path.join(output_folder, 'issues-casey.csv'), 'a'))

seen = {}
for (issue, issueCount) in session.query(GhIssue,GhIssueCount).filter(GhIssue.repo_id == GhIssueCount.id).all():
    #print(issue)
    seen[issueCount.slug] = True
print(str(len(seen)) + ' DB projects with issues')

# exit()

# slugs = ["CMUSTRUDEL/cmustrudel.github.io"]
# slugs = ["tue-mdse/genderComputer"]

# slugs = []
# projects_list = 'projects.csv'
# f = open(projects_list, 'r')
# import csv
# reader = csv.reader(f)
# for row in reader:
#     slug = row[0]
#     slugs.append(slug)

slugs = []
for repo in session.query(GhIssueCount):
    if repo.num_issues <= 100:
        slugs.append((repo.id, repo.slug))

print(len(slugs))
# exit()

# slugs = ["palantir/atlasdb"]
# slugs = ["squaresLab/BugZoo"]

pool = MyPool(processes=tokens.length(), initializer=initializer, initargs=())

# writer = UnicodeWriter(open('issues.csv', 'w'))

for result in pool.imap_unordered(fetchIssues, slugs):  # session.query(TravisRepo)
    (repo_id, slug, pid, token, issues, issueComments, err) = result
    # slug = repo.slug
    # repo_id = repo.id
    if err is not None:
        log_writer.writerow([slug, err])
    else:
        # try:
        #     # old_repo = session.query(Repo).filter_by(slug=slug).one()
        #     old_repo = session.query(Repo).filter_by(id=repo.id).one()
        #     repo_id = old_repo.id
        # except:
        #     new_repo = Repo(None, None, slug)
        #     session.add(new_repo)
        #     session.commit()
        #     repo_id = new_repo.id


        for issue in issues:
            [issue_id, issue_number, state, created_at, closed_at,
             created_by_login, closed_by_login, assignee_login, title,
             body, num_comments, labels, pr_num] = issue
            #print(issue)

            try:
                old_issue = session.query(GhIssue).filter_by(issue_id=int(issue_id)).one()
            except:
                gi = GhIssue(repo_id, int(issue_id), issue_number, state,
                             created_at, closed_at, created_by_login,
                             closed_by_login, assignee_login, title,
                             body, num_comments, labels, pr_num)
                session.add(gi)

        session.commit()

        for comment in issueComments:
            [issue_id, comment_id, created_at, updated_at, created_by_login, body, reactions] = comment
            # print(comment)

            try:
                old_comment = session.query(GhIssueComment).filter_by(comment_id=int(comment_id)).one()
            except:
                gic = GhIssueComment(int(comment_id), int(issue_id),
                                     created_at, updated_at,
                                     created_by_login, body, reactions)
                session.add(gic)

        session.commit()

