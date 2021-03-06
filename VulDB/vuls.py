import json as js
import os
import sys

# path = 'snyk'
path = sys.argv[1]
vuldict = {}
files= os.listdir(path)
cnt = 0
for fname in files:
    # f = file('snyk/'+fname)
    f = open(path+'/'+fname, 'r')
    s = js.load(f)
    num = len(s['vulnerabilities'])
    cnt += num
    for i in range(num):
        package = s['vulnerabilities'][i]['from'][1]
        infodict = {}
        infodict["identifiers"] = s['vulnerabilities'][i]["identifiers"]
        infodict["references"] = s['vulnerabilities'][i]["references"]
        infodict["title"] = s['vulnerabilities'][i]["title"]
        infodict["from"] = s['vulnerabilities'][i]["from"]
        try:
            vuldict[package].append(infodict)
        except:
            vuldict[package] = []
            vuldict[package].append(infodict)

vuljs = js.dumps(vuldict)
vulfile = open('./vuls/vuls.json', 'w')
vulfile.write(vuljs)
vulfile.close()
