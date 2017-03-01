#!/usr/bin/python

import sqlite3
import os


class Field:
    """Fields For Model"""
    Null    = "NULL"
    Integer = "INTEGER"
    LongInt = "INTEGER"
    Float   = "REAL"
    String  = "TEXT"
    Unicode = "TEXT"
    Buffer  = "BLOB"

def column_arrangements_for_inputs(*args):
    data=""
    for i in args:
        data = data + "{},".format(i)
    data = data[:-1]
    return "({})".format(data)

def value_arrangements_for_inputs(*args):
    data=""
    for i in args:
        data = data + "'{}',".format(i)
    data = data[:-1]
    return "({})".format(data)

class Row:
    def __init__(self, submaster, master,tablename, id):
        self.__SUBMASTER__ = submaster
        self.__MASTER__ = submaster.master
        self.__TableHook__ = tablename
        self.__id__ = id
        self.__assign_value__()
            
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return "< Row-ID:{} >".format(self.__id__)
        
    def __assign_value__(self):
        column =[i for (i,j) in self.__MASTER__.get_all_columns_(self.__TableHook__)]
        for i in column:
            self.__dict__[i]=None
            
        if self.__id__!="NEW":
            sql = "SELECT * from {} WHERE id = {};".format(self.__TableHook__, str(self.__id__))
            result = self.__MASTER__.cur.execute(sql)
            column = ["__id__"]+column
            values = [zip(column,i) for i in result.fetchall()]
            for value in values:
                for col, data in value:
                    self.__dict__[col]=data
        return 
    
    def get_all(self):
        data = []
        column = [i for (i,j) in self.__MASTER__.get_all_columns_(self.__TableHook__)]
        for i in column:
            data.append((i,self.__dict__[i]))
        data=data+[('id', self.__id__)]
        return dict(data)
    
    def set_all(self, **kwargs):
        for col, data in kwargs.iteritems():
                    self.__dict__[col]=data
        return
        
    
    def save(self):
        data = []
        column = [i for (i,j) in self.__MASTER__.get_all_columns_(self.__TableHook__)]
        for i in column:
            if self.__dict__[i]:
                data.append((i,self.__dict__[i]))
        data=data+[('id', self.__id__)]
        print data
        if dict(data)['id']=="NEW":
            kwargs = dict(data)
            kwargs.pop('id')
            print kwargs
            self.__SUBMASTER__.insert(**kwargs)
            
        elif self.__SUBMASTER__.has(dict(data)['id']):
            self.__SUBMASTER__.update(data=dict(data))
        else:
            return False
        return True

    
   
class Table:
    def __init__(self, master,tablename):
        self.dbase = master.dbase
        self.cursor = master.cur
        self.TableHook = tablename
        self.master = master
        
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return "< TableControls:{} >".format(self.TableHook)
        
    def Row(self, id):
        return Row(self,self.master, self.TableHook, id)
        
    
    def get(self, id):
        sql = "SELECT * from {} WHERE id = {};".format(self.TableHook, str(id))
        self.master.cur.execute(sql)
        #return self.master.cur.fetchall()
        return [self.Row(i[0]) for i in self.master.cur.fetchall()]
    
    def new(self):
        return self.Row("NEW")
    
    def insert(self, **kwargs):
        if kwargs:
            column =[]
            value = []
            for i,j in kwargs.iteritems():
                column.append(i)
                value.append(j)
        if "id" not in kwargs.keys():
            sql = "INSERT INTO {} {} VALUES {};".format(self.TableHook, column_arrangements_for_inputs(*tuple(column)), value_arrangements_for_inputs(*tuple(value)))
            print sql, column, value
        else:
            if self.has(kwargs['id']):
                self.update(id=kwargs['id'], data=kwargs)
                return
            else:
                sql = "INSERT INTO {} {} VALUES {};".format(self.TableHook, column_arrangements_for_inputs(*tuple(column)), value_arrangements_for_inputs(*tuple(value)))
        self.master.cur.execute(sql)
        return self.master.save()
        
    
    def update(self, id=None, data={}):
        sql = "UPDATE {} SET {} WHERE id = {}"
        if id==None:
            if "id" in data.keys():
                id=data.pop('id')
            else:
                raise "Please Provide ID"
                return 
        sentence = ""
        if "id" in data.keys():
                id=data.pop('id')
        for i,j in data.iteritems():
            sentence = sentence + " {} = '{}',".format(i,j)
        self.master.cur.execute(sql.format(self.TableHook,sentence[:-1], id))
        print sql.format(self.TableHook,sentence[:-1], id)
        return self.master.save()
    
    def get_all(self):
        sql = "SELECT * from {}".format(self.TableHook)
        self.master.cur.execute(sql)
        columns = tuple(['id']+[i for i,j in self.columns_name()])
        return [self.Row(i[0]) for i in self.master.cur.fetchall()]
    
    def search(self, **kwargs):
        sentence = ""
        for i,j in kwargs.iteritems():
            sentence = sentence + " {} = '{}' AND".format(i,j)
        sql = "SELECT * from {} WHERE{};".format(self.TableHook,sentence[:-3])
        self.master.cur.execute(sql)
        columns = tuple(['id']+[i for i,j in self.columns_name()])
        return [dict(zip(columns, i)) for i in self.master.cur.fetchall()]
    
    def delete(self, id):
        if type(id)==type(1) or type(id)==type('1'):
            sql = 'DELETE from {} WHERE id = {};'.format(self.TableHook, str(id))
            self.master.cur.execute(sql)
            return
        sql = 'DELETE from {} WHERE id = {};'.format(self.TableHook, str(id.__id__))
        self.master.cur.execute(sql)
        return self.master.save()
    
    def has(self, id):
        result = self.get(id)
        return True if result else False
    
    def columns_name(self):
        return self.master.get_all_columns_(self.TableHook)
    
    def save(self):
        return self.master.save()
        
     
    def get_tables_name(self):
        return self.master.get_all_tables_name()
    
    def table_access(self, table):
        self.TableHook = table
        return self.TableHook

    
class Model(object):
    def __init__(self):
        pass
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return "< DataBase:{} >".format(self.get_db_names())
    
    def connect(self, path="", dbname=None):
        if not dbname:
            dbname = self.get_db_names()
        dbpath = os.path.join(path, dbname+".sqlite.db")
        db_is_new = not os.path.exists(dbpath)
        if db_is_new:
            print "[Info] Creating New Database .... ",
        else:
            print "[Info] Accessing Database .... ",
        self.dbase = sqlite3.connect(dbpath)#, isolation_level=None)
        self.cur = self.dbase.cursor()
        print "Done!"
        if db_is_new:
            self.create_new_tables()
        self.check_for_new_tables()
        return
    
    def check_for_new_tables(self):
        print "[*] Checking Tables And Columns"
        (match, unmatch ) = self.check_available_tables()
        for i in unmatch:
            self.create_new_table(i)
        return
    
    def Table(self, name=None):
        if name:
            return Table(self,name) 
        return Table(self,self.get_all_table_with_class()[0][0]) 
    
    
    def close(self):
        return self.dbase.close()
    
    def save(self):
        return self.dbase.commit()
    
    def get_db_names(self):
        return self.__class__.__name__.__str__() 
    
    def get_all_columns_(self, TableName):
        return [i for i in dict(self.__class__.__dict__[TableName].__dict__).iteritems() if "__" not in i[0]]
    
    def get_all_table_with_class(self):
        return [i for i in dict(self.__class__.__dict__).iteritems() if "__" not in i[0]]
    
    def get_all_tables_name(self):
        return [i[0] for i in self.get_all_table_with_class()]
    
    def get_tables(self):
        data={}
        for i in self.get_all_tables_name():
            data[i]=self.Table(name=i)
        return data
    
    
    def create_new_table(self, ntable):
        print "[Info] Creating New Table And Columns ..."
        data = ""
        for table,control in self.get_all_table_with_class():
            if table == ntable:
                print "\t Table {}".format(table)
                cmd = ""
                for field, fieldtype in self.get_all_columns_(table):
                    print "\t\t Column {}".format(field)
                    cmd = cmd + " {} {},".format(field, fieldtype)
                data = data + "CREATE TABLE {} ({});\n".format(table, cmd[:-1])
        self.cur.executescript(data)
        print "Done!"
        return self.save()

    def create_new_tables(self):
        print """[Info] Creating New Tables And Columns .... """
        data = ""
        for table,control in self.get_all_table_with_class():
            print "\t Table {}".format(table)
            cmd = 'id integer primary key autoincrement null, '
            for field, fieldtype in self.get_all_columns_(table):
                print "\t\t Column {}".format(field)
                cmd = cmd + " {} {},".format(field, fieldtype)
            data = data + "CREATE TABLE {} ({});\n".format(table, cmd[:-1])
        self.cur.executescript(data)
        print " Done!.."
        return self.save()
    
    def get_tables_from_db(self):
        data= []
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for i in self.cur.fetchall():
            data.append(i[0])
        return data
    
    def check_available_tables(self):
        match = []
        unmatch = []
        db = self.get_tables_from_db()
        fuct = self.get_all_tables_name()
        for i in fuct:
            if i in db:
                match.append(i)
            else:
                print "[Info] New Table Found ",i
                unmatch.append(i)
        return (match, unmatch)
    

