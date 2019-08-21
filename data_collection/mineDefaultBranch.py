# mines the default branches of the projects
# some projects don't use master as their default branch

from github import Github
import github.GithubObject
from myTokens import Tokens
import datetime
from math import ceil
import os
import csv
# We must import this explicitly, it is not imported by the top-level
# multiprocessing module.
import time
import itertools
from copy import deepcopy

import sys
import urllib2
import json

tokens = Tokens()
last = datetime.datetime.now()

def getRateLimit(g):
    return g.rate_limiting

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

def default_branch(slug, g):
    
    print 'Processing:', slug
    
    try:
        repo = g.get_repo(slug)
        print(repo.default_branch)
        
    except Exception as e:
        return None

    return repo.default_branch

with open('top50k_projects.csv') as f:
    reader = csv.reader(f)
    lst = list(reader)
    z = [item[1] for item in lst]
    
writer = open('default-branch.csv', 'w')
slug_index = 24127
while slug_index < len(z):
    for token in tokens.iterator():
        g = Github(token)
        while slug_index < len(z):
            print(slug_index)
            slug = z[slug_index]
            if canCheckInfo(g):
                df = default_branch(z[slug_index], g)
                if df is not None:
                    try:
                        writer.write(slug+","+df+"\n")
                    except:
                        writer.write(slug+",NA\n")
                else:
                    writer.write(slug+",NA\n")
                slug_index += 1
            else:
                break
        continue
