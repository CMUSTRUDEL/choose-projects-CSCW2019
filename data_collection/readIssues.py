import pandas as pd
from datetime import datetime

df = pd.read_csv("issues.csv", delimiter=",,,,")
df_id = df.groupby('repo_id')

cdf = pd.read_csv("comments.csv", delimiter=",:,:")

with open("resp/summary_resp1.csv", 'w') as s:
    with open("resp/comment_resp1.csv", 'w') as f:
        for (repo_id, repo) in df_id:
            print(repo_id)
            times = list()
        
            for r in repo.itertuples():
                comments = cdf[cdf['issue_id'] == r.issue_id]
            
                created = datetime.strptime(r.created_at, '%Y-%m-%d %H:%M:%S')
                resp = datetime.strptime(r.closed_at, '%Y-%m-%d %H:%M:%S')
                for c in comments.itertuples(): 
                    if r.created_by_login == c.created_by_login:
                        continue
            
                    cresp = datetime.strptime(c.created_at, '%Y-%m-%d %H:%M:%S')
                    f.write(str(c.comment_id) + ",")
                    f.write(str(c.issue_id) + ",")
                    f.write(str(repo_id) + ",")
                    cresptime = cresp - created
                    f.write("%.2f\n" % (cresptime.total_seconds() / 60))
                    if cresp < resp:
                        resp = cresp
                resptime = resp - created
                times.append(resptime.total_seconds() / 60)
            
            times = pd.Series(times).describe()
            s.write("%d,%d,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n" % (repo_id, times['count'], times['mean'], times['std'], times['min'], times['25%'], times['50%'], times['75%'], times['max']))
