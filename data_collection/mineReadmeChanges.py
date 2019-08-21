from github import Github
import github.GithubObject
from myTokens import Tokens
import datetime
from math import ceil
import os
import csv
import multiprocessing
# We must import this explicitly, it is not imported by the top-level
# multiprocessing module.
import multiprocessing.pool
import time
import itertools
from copy import deepcopy

import sys
import urllib2
import json
import hashlib

from unidecode import unidecode
from dateutil import parser

tokens = Tokens()
tokens_iter = tokens.iterator()

last = datetime.datetime.now()

def getRateLimit(g):
    return g.rate_limiting

def computeSleepDuration(g):
    reset_time = datetime.datetime.fromtimestamp(g.rate_limiting_resettime)
    curr_time = datetime.datetime.now()
    return int(ceil((reset_time - curr_time).total_seconds()))

def waitIfDepleted(g):
    (remaining, _limit) = getRateLimit(g)
    print(remaining)
    sleep_duration = computeSleepDuration(g)
    if not remaining > 50:
        sleep(sleep_duration)
    
def waitAndGetRepo(g, slug):
    waitIfDepleted(g)
    return g.get_repo(slug)

def canCheckInfo(g):
    global last
    (remaining, _limit) = getRateLimit(g)
    print(remaining)
    enough = remaining > 100
    if not enough:
        reset_time = datetime.datetime.fromtimestamp(g.rate_limiting_resettime)
        print(reset_time)
        if last < datetime.datetime.now() or last > reset_time:
            last = reset_time
    return enough

def fetchIssues(slug, g):
    
#     slug = tr.slug
    issues = []
    changes = 0
    
    print 'Processing:', slug
    
    try:
        repo = g.get_repo(slug)
        readme = repo.get_readme()
        
        begin = datetime.datetime(2018, 6, 1)
        end = datetime.datetime.now()
        commits = repo.get_commits(path=readme.path, since=begin, until=end)
        for commit in commits:
            for file in commit.files:
                if (file.filename == readme.name):
                    c = file.changes
                    changes += c
    
    except Exception as e:
        return (slug, None, changes, str(e).strip().replace("\n"," ").replace("\r"," "))
    
    return (slug, token, changes, None)

def initializer():
    token = tokens_queue.get()
    pid = current_process().pid
    tokens_map[pid] = token


output_folder = os.getcwd()

seen = {}

#### Make list_of_slugs somewhere before this next call 
#### I was pulling mine from a db

writer = open('readme_changes.csv', 'a')

try:
    with open('readme_changes_info.txt', 'r') as info:
        start = int(info.readline().strip())
except Exception as e:
    start = 0

with open('top50k_projects.csv') as f:
    reader = csv.reader(f)
    lst = list(reader)
    slugs = [item[1] for item in lst]

slug_index = start
for token in tokens.iterator():
    g = Github(token)
    while slug_index < len(slugs):
        print(slug_index)
        slug = slugs[slug_index]
        if canCheckInfo(g):
            (slug, token, changes, err) = fetchIssues(slug, g)
            if err is not None:
                writer.write(slug + ",NA\n")
            else:
                writer.write(slug + "," + str(changes) + "\n")
            slug_index += 1
        else:
            break
    continue

print("BREAK\n\n")

for token in tokens.iterator():
    g = Github(token)
    while slug_index < len(slugs):
        print(slug_index)
        slug = slugs[slug_index]
        if canCheckInfo(g):
            (slug, token, changes, err) = fetchIssues(slug, g)
            if err is not None:
                writer.write(slug + ",NA\n")
            else:
                writer.write(slug + "," + str(changes) + "\n")
            slug_index += 1
        else:
            break
    continue

with open('readme_changes_info.txt', 'w') as info:
    info.write(str(slug_index) + '\n')
    info.write(str(last) + '\n')
