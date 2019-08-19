from github import Github
import github.GithubObject
from myTokens import Tokens
import MySQLdb
from itertools import combinations
import multiprocessing
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

def getRateLimit(g):
    return g.rate_limiting

def canCheckInfo(g):
    global last
    (remaining, _limit) = getRateLimit(g)
    enough = remaining > 100
    return enough

con_dir = ["", "docs/", ".github/"]
con_name = ["CODE_OF_CONDUCT", "code_of_conduct"]
con_ext = ["", ".md", ".rdoc", ".markdown"]
con_urls = list()
for dir in con_dir:
    for name in con_name:
        for ext in con_ext:
            con_urls.append("https://raw.githubusercontent.com/%s/%s/" + dir + name + ext)

info = list()
with open("/data2/yucenl/top50k_projects.csv") as top:
    top = csv.reader(top, delimiter=',')
    for line in top:
        info.append((line[0], line[1]))

branch = list()
with open("/data2/yucenl/default-branch.csv") as branch_list:
    branch_list = csv.reader(branch_list, delimiter=',')
    for line in branch_list:
        branch.append(line[1])

z = zip(range(50000), info)
z = zip(z, branch)

def download(z, g):

  index = z[0][0]
  slug = z[0][1][1]
  id = z[0][1][0]
  default = z[1]
  print(index)
  print(slug)
    
  try:
    con = False
    for url in con_urls:
        try:
            resp = urllib2.urlopen(url % (slug, default))
        except urllib2.HTTPError as e:
            continue
        else:
            return (slug, True)
    if not con:
        name = slug.replace('/', '_').replace('.', '')
        name = id + "$" + name

        try:
            path = os.path.join(os.getcwd(), 'files', 'readmes', name)
            with open(path) as f:
                for line in resp.readlines():
                    if re.match(r'^#{1,2} ', line):
                      header = re.sub(r'^#* ', '', line).rstrip()
                      if "code of conduct" in header.lower():
                          return (slug, True)
        except:
            return (slug, False)

    return (slug, False)
  except:
    return (slug, False) 

tokens = Tokens()

writer = open("code_conduct.csv", 'w')

slug_index = 0
for token in tokens.iterator():
    g = Github(token)
    while slug_index < len(z):
        if canCheckInfo(g):
            (slug,res) = download(z[slug_index], g)
            print(res)
            writer.write(slug+","+str(res)+"\n")
            slug_index += 1
        else:
            break
    continue

