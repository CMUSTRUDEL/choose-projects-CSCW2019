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
    print(remaining)
    enough = remaining > 100
    if not enough:
        reset_time = datetime.datetime.fromtimestamp(g.rate_limiting_resettime)
        print(reset_time)
        if last < datetime.datetime.now() or last > reset_time:
            last = reset_time
    return enough


read_dest_folder = "/data2/yucenl/files/readmes"
con_dest_folder = "/data2/yucenl/files/contribs"
log = csv.writer(open("/data2/yucenl/script/readme_log", "a"))

con_name = ["CONTRIBUTING", "Contributing", "contributing"]
con_ext = ["", ".md", ".rdoc", ".markdown"]
con_urls = list()
for name in con_name:
    for ext in con_ext:
        con_urls.append("https://raw.githubusercontent.com/%s/%s/" + name + ext)

info = list()
with open("/data2/yucenl/top50k_projects.csv") as top:
    top = csv.reader(top, delimiter=',')
    for line in top:
        info.append(line[1])

branch = list()
with open("/data2/yucenl/default_branch.csv") as branch_list:
    branch_list = csv.reader(branch_list, delimiter=',')
    for line in branch_list:
        branch.append(line[1])

z = zip(range(10000), info)
z = zip(z, branch)
f404 = open("top10_f_404", "w")

f404.write("hi")

def download(z, g):

  index = z[0][0]
  slug = z[0][1]
  default = z[1]
  print(index)
  print(slug)
  print(default)
    
  try:
    con = False
    for url in con_urls:
      
      try:
        resp = urllib2.urlopen(url % (slug, default))
      except urllib2.HTTPError as e:
        if e.code == 404:
          f404.write(url%(slug,default) + " 404")
          pass
      except urllib2.URLError as e:
        return [str(pr.id), dest_path]
      else:
        con = True
    if not con:
        try:
          repo = g.get_repo(slug)
          readme = repo.get_readme()
          trial = "https://raw.githubusercontent.com/%s/%s/%s" % (slug, default, readme.path)
          print(trial)
          resp = urllib2.urlopen(trial)
        except urllib2.HTTPError as e:
          if e.code == 404:
            f404.write(resp + " 404")
            pass
        except urllib2.URLError as e:
          # Not an HTTP-specific error (e.g. connection refused)
          f404.write(resp + " not an HTTP-specific error")
          return [str(pr.id), dest_path]
        else:
          # 200
          for line in resp.readlines():
              if re.match(r'^#{1,2} ', line):
                header = re.sub(r'^#* ', '', line).rstrip()
                if "contributing" in header.lower() or "contribute" in header.lower():
                    con = True
                    return (slug, con)
    
    return (slug, con)
  except:
    return (slug,None) 

tokens = Tokens()

writer = open("contrib_section.csv", 'w')

slug_index = 0
for token in tokens.iterator():
    g = Github(token)
    while slug_index < len(z):
        print(slug_index)
        if canCheckInfo(g):
            (slug,res) = download(z[slug_index], g)
            if res is not None:
                writer.write(slug+","+str(res)+"\n")
            else:
                writer.write(slug+",NA\n")
            slug_index += 1
        else:
            break
    continue

