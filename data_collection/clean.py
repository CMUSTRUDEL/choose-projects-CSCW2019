# cleans up the README file

import os
import re
import glob

def stylerepl(matchobj):
    word = matchobj.group(0)
    word = re.sub(r'^(\*|_|~)+', '', word)
    word = re.sub(r'(\*|_|~)+$', '', word)
    return word

def linkrepl(matchobj):
    word = matchobj.group(0)
    word = re.sub(r'\(.*\)', '', word)
    if word.startswith("!"):
        return word[2:-1]
    return word[1:-1]

def clean_line(line):
    if re.search(r'^ {4}[^\s]+', line):
        return "CODE\n"
    # whitespace
    line = re.sub(r'^ +', '', line)
    # blockquotes
    line = re.sub(r'^> *', '', line)
    # headers
    if (re.match(r'^#+ ', line)):
        line = re.sub(r'^#+ ', '', line)
        line = line.strip() + ".\n"
    # lists
    line = re.sub(r'^ *(\*|\+|-) +', '', line)
    line = re.sub(r'^ *(\d)+. +', '', line)
    # inline code
    line = re.sub(r'`[^`]*`', 'CODE', line)
    # image
    line = re.sub(r'!\[[^\]\[]*\]\([^\)]*\)', 'IMAGE', line)
    # links
    line = links(line)
    # html
    line = re.sub(r'<[^>]*>', '', line)
    return style(line)

def links(line):
    if re.search(r'\[[^\]\[]*\]\([^\)]*\)', line):
        return links(re.sub(r'\[[^\]\[]*\]\([^\)]*\)', linkrepl, line))
    elif re.search(r'\[[^\]]*\]\[[^\)\*]*\]', line):
        return links(re.sub(r'\[[^\]*\]\[[^\]]*\]', linkrepl, line))
    return line
    
def style(line):
    # bold, italics, underline
    if re.search(r'((\*|_|~)+)([^\1])*\1', line) is not None:
        return style(re.sub(r'((\*|_|~)+)([^\1])*\1', stylerepl, line))
    return line

for file in glob.glob("files/readmes/*"):
#with open('/data2/yucenl/files/readmes/13921166$nknapp_html5-media-converter') as f:
    #file = '/data2/yucenl/files/readmes/13921166$nknapp_html5-media-converter'
    clean_file = re.sub(r'/readmes/', '/readmes_clean/', file)
    clean_file = clean_file + "$clean"
    with open(file) as f:
        with open(clean_file, 'w') as w:
            comment = False
            for line in f.readlines():
                # comments
                if re.search(r'^ *`{3}', line):
                    comment = not comment
                    continue
    
                if re.search(r'^=*$', line) or re.search(r'^-*$', line):
                    continue
    
                if not comment:
                    line = clean_line(line)
                    w.write(line)
