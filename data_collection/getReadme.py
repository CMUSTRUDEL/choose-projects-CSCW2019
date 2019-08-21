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
with open("top50k_projects.csv") as proj_list:
     lines = csv.reader(proj_list, delimiter=',')
     for line in lines:
         proj.append(line[0])

z = list()
with open("default-branch.csv") as branch_list:
     lines = csv.reader(branch_list, delimiter=',')
     for line in lines:
         z.append((line[0], line[1]))

z = zip(proj, z)

read_dest_folder = "files/readmes"
con_dest_folder = "files/contribs"

con_name = ["CONTRIBUTING", "Contributing", "contributing"]
con_ext = ["", ".md", ".rdoc", ".markdown"]
con_urls = list()
for name in con_name:
    for ext in con_ext:
        con_urls.append("https://raw.githubusercontent.com/%s/%s/" + name + ext)

def download(z, g):
    (id, (slug, default)) = z
    print(z)
    if default == "NA":
        return

    name = slug.replace('/', '_').replace('.', '')
    dest_path = '%s$%s' % (id, name)

    try:
        con = False
        for url in con_urls:
            try:
                resp = urllib2.urlopen(url % (slug, default))
            except urllib2.HTTPError as e:
                pass
            except urllib2.URLError as e:
                pass
            else:
                with open(os.path.join(con_dest_folder, dest_path), 'wb') as f:
                    f.write(resp.read())
                con = True
                break
        
        try:
            repo = g.get_repo(slug)
            readme = repo.get_readme()
            trial = "https://raw.githubusercontent.com/%s/%s/%s" % (slug, default, readme.path)
            resp = urllib2.urlopen(trial)
        except urllib2.HTTPError as e:
            print(slug + " NO README")
        except urllib2.URLError as e:
            print(slug + " NO README")
        else:
            with open(os.path.join(read_dest_folder, dest_path), 'wb') as f:
                for line in resp.readlines():
                    f.write(line)
                    if re.match(r'^#{1,2} ', line):
                        header = re.sub(r'^#* ', '', line).rstrip()
                        if "contributing" in header.lower() or "contribute" in header.lower():
                            con = True
        return con
    except:
        return None

writer = open("contrib_section.csv", 'w')
slug_index = 33080
while slug_index < len(z):
    for token in tokens.iterator():
        g = Github(token)
        while slug_index < len(z):
            print(slug_index)
            if canCheckInfo(g):
                 res = download(z[slug_index], g)
                 (_, (slug, _)) = z[slug_index]
                 if res is not None:
                     writer.write(slug+","+str(res)+"\n")
                 else:
                     writer.write(slug+",NA\n")
                 slug_index += 1
            else:
                break
        continue
