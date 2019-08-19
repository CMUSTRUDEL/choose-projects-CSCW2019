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

def homepage(slug, g):
    
    print 'Processing:', slug
    
    try:
        repo = g.get_repo(slug)
        url = repo.homepage
        if url is not None:
            return len(url) > 0
        
    except Exception as e:
        return False

    return False

with open('top50k_projects.csv') as f:
    reader = csv.reader(f)
    lst = list(reader)
    z = [item[1] for item in lst]
    
writer = open('homepage.csv', 'w')
slug_index = 0
while slug_index < len(z):
    for token in tokens.iterator():
        g = Github(token)
        while slug_index < len(z):
            print(slug_index)
            slug = z[slug_index]
            if canCheckInfo(g):
                page = homepage(z[slug_index], g)
                writer.write(slug+","+str(page)+"\n")
                slug_index += 1
            else:
                break
        continue
