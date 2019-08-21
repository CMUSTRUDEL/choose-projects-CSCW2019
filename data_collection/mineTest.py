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
import numpy as np

import sys
import json
from csv import reader, writer
import hashlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dateutil import parser

import random
import numpy as np

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
        # session.commit()
        sleep(sleep_duration)

def waitAndGetRepo(g, slug):
    waitIfDepleted(g)
    return g.get_repo(slug)

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

    try:
        token = tokens_map[pid]

        g = Github(token)

        waitIfDepleted(g)
        repo = g.get_repo(slug)

        count = 0
        if repo.has_issues:
            for issue in repo.get_issues(state=u"closed"):
                waitIfDepleted(g)

                if count >= 30:
                    break

                if (issue.closed_at > datetime.datetime(2018, 6, 1)):
                    continue
                if issue.pull_request is not None:
                    continue

                count += 1

                comments = issue.get_comments()
                
                for comment in comments:
                    waitIfDepleted(g)

                    issue_id = issue.id  # int

                    commentData = [issue_id] + parseComment(g, comment)

                    waitIfDepleted(g)

                    reactions = []
                    for reaction in comment.get_reactions():
                        reactions.append(str(reaction.content))

                        waitIfDepleted(g)

                    commentData.append(','.join(reactions))

                    issueComments.append(commentData)

    except Exception as e:
        return (repo_id, slug, pid, None, issues, issueComments, str(e).strip().replace("\n", " ").replace("\r", " "))

    return (repo_id, slug, pid, token, issues, issueComments, None)

manager = Manager()
tokens_map = manager.dict()
files = manager.dict()
proc = manager.dict()

def initializer():
    token = tokens_queue.get()
    pid = current_process().pid
    tokens_map[pid] = token
    files[pid] = 'comments_try.' + str(pid) + '.csv'
    proc[pid] = 'comments_try.' + str(pid) + '.txt'

proj = list()
with open("error_try.csv") as proj_list:
    lines = csv.reader(proj_list, delimiter=',')
    for line in lines:
        proj.append((int(line[1]), line[0]))

pool = MyPool(processes=tokens.length(), initializer=initializer, initargs=())

logwriter = open('comments_error_try.csv', 'w')

for result in pool.imap_unordered(fetchIssues, proj):
    (repo_id, slug, pid, token, issues, issueComments, err) = result

    with open(proc[pid], 'a') as f:
        f.write("Processing: " + slug + "\n")

    # slug = repo.slug
    # repo_id = repo.id
    if err is not None:
        logwriter.write(slug + "," + err + "\n")
    else:
        with open(files[pid], 'a') as f:
            for comment in issueComments:
                [issue_id, comment_id, created_at, updated_at, created_by_login, body, reactions] = comment
                delim = ",:,:"
                commentline = "" 
                for (_, x) in enumerate(comment):
                    if not isinstance(x, unicode):
                        x = str(x)
                    else:
                        x = repr(x)
                    commentline += x + delim
                commentline = commentline[0:-len(delim)] + "\n"
                f.write(commentline)

print("done!!")
