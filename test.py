import pandas as pd

c = pd.read_csv('../csv/issues.csv', delimiter=',,,,', header=None)
print(c)
for row in c:
    print(row)
