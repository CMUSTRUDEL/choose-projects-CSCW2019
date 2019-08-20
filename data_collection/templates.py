from github import Github
import github.GithubObject
from myTokens import Tokens
import csv
import urllib2
import os
import re
from time import sleep
import datetime

class Project:
    def __init__(self, id):
        self.id = id
        db = MySQLdb.connect(host="localhost",user="anita",passwd="github",db="ghtorrent")
        cursor = db.cursor()
        cursor.execute("select url,language from projects where id=%d"%\
        self.id)
        data = cursor.fetchone()
        if data == None:
            self.url = ''
            self.slug = ''
            self.lang = ''
        else:
            self.url = data[0]
            self.slug = '/'.join(data[0].split('/')[-2:])
            self.lang = data[1]
        db.close()


    def pprint(self):
        print 'Project:',self.id,self.lang,self.url

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

proj = list()
with open("/data2/yucenl/top50k_projects.csv") as proj_list:
     lines = csv.reader(proj_list, delimiter=',')
     for line in lines:
         proj.append(line[0])

z = list()
with open("/data2/yucenl/default-branch.csv") as branch_list:
     lines = csv.reader(branch_list, delimiter=',')
     for line in lines:
         z.append((line[0], line[1]))

z = zip(proj, z)

read_dest_folder = "/data2/yucenl/files/readmes"
con_dest_folder = "/data2/yucenl/files/contribs"

con_name = ["CONTRIBUTING", "Contributing", "contributing"]
con_ext = ["", ".md", ".rdoc", ".markdown"]
con_urls = list()
for name in con_name:
    for ext in con_ext:
        con_urls.append("https://raw.githubusercontent.com/%s/%s/" + name + ext)

def download(z, g):
    (id, (slug, default)) = z
    print(z)
    issue_t = False
    pr_t = False

    dirs = [".github/", "", "docs/"]
    try:
        repo = g.get_repo(slug)
    except:
        return (False, False)
        
    for d in dirs:
        if issue_t:
            break
        try:
            issues = repo.get_contents(d + "ISSUE_TEMPLATE")
            for i in issues:
                issue_t = True
                break
        except:
            continue
    if not issue_t:
        for d in dirs:
            try:
                issue = repo.get_contents(d + "issue_template.md")
                if issue is not None:
                    issue_t = True
                    break
                issue = repo.get_contents(d + "ISSUE_TEMPLATE.md")
                if issue is not None:
                    issue_t = True
                    break
            except:
                continue
    
    for d in dirs:
        if pr_t:
            break
        try:
            prs = repo.get_contents(d + "PULL_REQUEST_TEMPLATE")
            for pr in prs:
                pr_t = True
                break
        except:
            continue
    if not pr_t:
        for d in dirs:
            try:
                pr = repo.get_contents(d + "pull_request_template.md")
                if pr is not None:
                    pr_t = True
                    break
                pr = repo.get_contents(d + "PULL_REQUEST_TEMPLATE.md")
                if pr is not None:
                    pr_t = True
                    break
            except:
                continue

    return (issue_t, pr_t)

writer = open("templates.csv", 'w')
slug_index = 0
while slug_index < len(z):
    for token in tokens.iterator():
        g = Github(token)
        while slug_index < len(z):
            print(slug_index)
            if canCheckInfo(g):
                (i, pr) = download(z[slug_index], g)
                (_, (slug, _)) = z[slug_index]
                print(i, pr)
                writer.write(slug+","+str(i) + "," + str(pr) +"\n")
                slug_index += 1
            else:
                break
        continue
