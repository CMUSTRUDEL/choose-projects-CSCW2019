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
from unicodeManager import UnicodeReader, UnicodeWriter
import hashlib

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
from unidecode import unidecode
#from travisDB import cleanStart, Base, initDB, repo_decoder
#from travisDB import TravisRepo, TravisCommit, TravisJob, TravisBuild, GhIssue
from dateutil import parser

readme_cap = ["README", "Readme", "ReadMe", "readme"]
readme_ext = ["", ".md", ".rdoc", ".markdown"]
readme_all = list()
for name in readme_cap:
    for ext in readme_ext:
        readme_all.append(name+ext)

# token = tokens[0]

tokens = Tokens()
tokens_iter = tokens.iterator()

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

def fetchIssues(slug, g):
    
    issues = []
    
    print 'Processing:', slug
    
    try:
        print("before")
        repo = g.get_repo(slug)
        readme = repo.get_readme()
        return (slug, token, readme.size, None)
        
    except Exception as e:
        return (slug, None, 0, str(e).strip().replace("\n"," ").replace("\r"," "))


def initializer():
    token = tokens_queue.get()
    pid = current_process().pid
    tokens_map[pid] = token


output_folder = os.getcwd()

writer = open('readme_sizes_mined.csv', 'a')

try:
    with open('readme_sizes_info.txt', 'r') as info:
        start = int(info.readline().strip())
except Exception as e:
    start = 0

with open('../proj/top10k_projects.csv') as f:
    reader = csv.reader(f)
    lst = list(reader)
    slugs = [item[1] for item in lst]

start = 0
slug_index = start
for token in tokens.iterator():
    g = Github(token)
    while slug_index < len(slugs):
        print(slug_index)
        slug = slugs[slug_index]
        if canCheckInfo(g):
            (slug, token, size, err) = fetchIssues(slug, g)
            if err is not None:
                writer.write(slug + ",NA\n")
            else:
                print(size)
                writer.write(slug + "," + str(size) + "\n")
            slug_index += 1
        else:
            break
    continue

with open('readme_sizes_info.txt', 'w') as info:
    info.write(str(slug_index) + '\n')
    info.write(str(last) + '\n')

