import MySQLdb
import sys

class Mydb:
    def __init__(self,host,user,password,charset="utf8"):
        self.host=host
        self.user=user
        self.password=password
        self.charset=charset

        try:
#            print("connecting ...");
            self.conn=MySQLdb.connect(host=self.host,user=self.user,passwd=self.password)
            self.conn.set_character_set(self.charset)
            self.cur=self.conn.cursor()

        except MySQLdb.Error as e:
            print("Mysql Error %d: %s" % (e.args[0], e.args[1]))
            sys.exit()

    def selectDb(self,db):
        try:
            self.conn.select_db(db)
        except MySQLdb.Error as e:
            print("Mysql Error %d: %s" % (e.args[0], e.args[1]))
            sys.exit()
        

    def query(self,sql):
        try:
            n=self.cur.execute(sql)
            return n
        except MySQLdb.Error as e:
            print("Mysql Error:%s\\nSQL:%s" %(e,sql))
            sys.exit()


    def queryRow(self,sql):
        self.query(sql)
        result = self.cur.fetchone()
        return result


    def queryAll(self,sql):
        self.query(sql)
        result=self.cur.fetchall()
        desc =self.cur.description
        d = []
        for inv in result:
             _d = {}
             for i in range(0,len(inv)):
                 _d[desc[i][0]] = str(inv[i])
             d.append(_d)
        return d


    def insert(self,p_table_name,p_data):
        for key in p_data:
            p_data[key] = "'"+str(p_data[key])+"'"
        key   = ','.join(p_data.keys())
        value = ','.join(p_data.values())
        real_sql = "INSERT INTO " + p_table_name + " (" + key + ") VALUES (" + value + ")"
        #self.query("set names 'utf8'")
        return self.query(real_sql)


    def getLastInsertId(self):
        return self.cur.lastrowid


    def rowcount(self):
        return self.cur.rowcount


    def commit(self):
        self.conn.commit()


    def close(self):
         self.cur.close()
         self.conn.close()



host = '112.124.98.113'
user = 'tkp'
password = 'qepapap'

mysql = Mydb(host, user, password)
mysql.selectDb('phpcms')

'''
result = mysql.queryAll("select * from wraith_mo");
print result
'''

