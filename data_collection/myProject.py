class Project:
    def __init__(self, id):
        self.id = id
        user = "user"
        passwd = "passwd"
        db = MySQLdb.connect(host="localhost",user=user ,passwd=passwd,db="ghtorrent")
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

