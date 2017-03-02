#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# ============================
# (^_^) Namaste.  Friend (^_^)
# ============================
#
#
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#        Read Me Notes
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# author:
#   S.S.B
#   surajsinghbisht054@gmail.com
#   https://bitforestinfo.blogspot.com
#
#
# About sqlorm:  
#       A Python object relational mapper for SQLite3.
#       Easy To Use And Easy To MainTain
#
# Reference:  https://www.sqlite.org/lang.html
#            https://docs.python.org/3/library/sqlite3.html
#
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#        Users Mannual
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# =====================================
# =========== DataBase ================
# =====================================
#
#   connect(path="", dbname=None)   --> Connect To Database
#   close()                         --> Close Database    
#   save()                          --> Save All Changes
#   get_db_names()                  --> Get Default Database Name
#   get_all_columns_(TableName)     --> Get All Columns Name List
#   get_all_table_with_class()      --> Get All Tables With Class Object As Dictonery
#   get_all_tables_name()           --> Get All Tables Name
#   get_tables()                    --> Get All Tables Object
#   Table(name=None)                --> Get Table Object
#
#
# =====================================
# ============= Table =================   
# =====================================
#
#   new()               --> New Row Interface
#   insert(**kwargs)    --> Insert New Values Into Row, id argument Required
#   update(id=None, data={}) --> Update Values Into Row
#   delete(id)          --> Delete Row , Id argument Required
#   search(**kwargs)    --> Search Row Object InterFace
#   get_all()           --> Get All Row Object InterFace as list
#   has(id)             --> Check Row
#   columns_name()      --> Get All Columns Names As List
#   save()              --> Save All Changes
#   get_tables_name()   --> Get Current Object Table Name
#   table_access(TableName) --> Change Current Object Table Access
#
#
# =====================================
# ============= Row ===================
# =====================================
#
#   get_all()           --> Get All Values In Dictionery
#   set_all(**kwargs)   --> Set Values
#   save()              --> Save Changes Into Database
#
__author__='''

######################################################
                By S.S.B Group                          
######################################################

    Suraj Singh
    Admin
    S.S.B Group
    surajsinghbisht054@gmail.com
    http://bitforestinfo.blogspot.com/

    Note: We Feel Proud To Be Indian
######################################################
'''

# Importing Module
import sqlite3
import os

# Python Sqlite Data Field
class Field:
    """Fields For Model"""
    Null    = "NULL"
    Integer = "INTEGER"
    LongInt = "INTEGER"
    Float   = "REAL"
    String  = "TEXT"
    Unicode = "TEXT"
    Buffer  = "BLOB"

# For Columns Inputs Arrangements
def column_arrangements_for_inputs(*args):
    """ For Columns Inputs Arrangements """
    data=""
    for i in args:
        data = data + "{},".format(i)
    data = data[:-1]
    return "({})".format(data)


# For Value INputs Arrangements
def value_arrangements_for_inputs(*args):
    """ For Value INputs Arrangements """
    data=""
    for i in args:
        data = data + "'{}',".format(i)
    data = data[:-1]
    return "({})".format(data)



# Row Object
class RowInterface:
    """ 
    Row Object Interface
    
    Act Like Dictonery Object. For Example:
    #
    #    row = table.new()  --> Creating Row Object Interface
    #    
    #    row.column_name = Values  --> assign value
    #    
    #    row.save()  --> Save Change Into Database {Automatic Reset}
    #    
    #    So, After Savig Value, No Need To Create New Row Object Interface 
    #
    
    Functions :
    
    #
    #    get_all()           --> Return All Values In Dictionery
    #
    #    set_all(**kwargs)   --> Set Values
    #
    #    save()              --> Save Changes Into Database
    #    
    """
    def __init__(self, submaster, master,tablename, id):
        """
        self.__SUBMASTER__  --> For Table Object Interface 
        self.__MASTER__     --> For Model Object Interface
        self.__TableHook__  --> Current Table Name
        self.__id__         --> Row Id
        """
        
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
        """ Return All Data In Dictonery With Columns With their Values
        """
        data = []
        column = [i for (i,j) in self.__MASTER__.get_all_columns_(self.__TableHook__)]
        for i in column:
            data.append((i,self.__dict__[i]))
        data=data+[('id', self.__id__)]
        return dict(data)
    
    def set_all(self, **kwargs):
        """ Set All Value As Arguments Given """
        for col, data in kwargs.iteritems():
                    self.__dict__[col]=data
        return
        
    
    def save(self):
        """ Save All Data Into Database"""
        data = []
        column = [i for (i,j) in self.__MASTER__.get_all_columns_(self.__TableHook__)]
        for i in column:
            if self.__dict__[i]:
                data.append((i,self.__dict__[i]))
        data=data+[('id', self.__id__)]
        if dict(data)['id']=="NEW":
            kwargs = dict(data)
            kwargs.pop('id')
            self.__SUBMASTER__.insert(**kwargs)
            self.__id__="NEW"
            self.__assign_value__()
            
        elif self.__SUBMASTER__.has(dict(data)['id']):
            self.__SUBMASTER__.update(data=dict(data))
        else:
            return False
        return True
    
   
class TableInterFace:
    """
    
    Table Object Interface
    
    #
    #   new()               --> New Row Object Interface
    #
    #   insert(**kwargs)    --> Insert New Values Into Row, id argument Required
    #
    #   update(id=None, data={}) --> Update Values Into Row
    #
    #   delete(id)          --> Delete Row , Id argument Required
    #
    #   search(**kwargs)    --> Search Row Object InterFace
    #
    #   get_all()           --> Get All Row Object InterFace as list
    #
    #   has(id)             --> Check Row
    #
    #   columns_name()      --> Get All Columns Names As List
    #
    #   save()              --> Save All Changes
    #
    #   get_tables_name()   --> Get Current Object Table Name
    #
    #   table_access(TableName) --> Change Current Object Table Access
    #
    """
    def __init__(self, master,tablename):
        """
        
        self.dbase     --> sqlite3.connect 
        self.cursor    --> sqlite3.connect().cursor
        self.TableHook --> Table Name
        self.master    --> Model Object Interface
        
        """
        self.dbase = master.dbase
        self.cursor = master.cur
        self.TableHook = tablename
        self.master = master
        
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return "< TableControls:{} >".format(self.TableHook)
        
    def Row(self, id):
        """ Get Row Object Interface Using Id"""
        # Print Row Triggered
        return RowInterface(self,self.master, self.TableHook, id)
        
    
    def get(self, id):
        """ Get Row Object Interface Using Id"""
        sql = "SELECT id from {} WHERE id = {};".format(self.TableHook, str(id))
        self.master.cur.execute(sql)
        return [self.Row(i[0]) for i in self.master.cur.fetchall()]
        
    
    def new(self):
        """ Create New Row Object Interface """
        return self.Row("NEW")
    
    def insert(self, **kwargs):
        """ Insert Values Into Row """
        if kwargs:
            column =[]
            value = []
            for i,j in kwargs.iteritems():
                column.append(i)
                value.append(j)
            if "id" not in column:
                sql = "INSERT INTO {} {} VALUES {};".format(self.TableHook, column_arrangements_for_inputs(*tuple(column)), value_arrangements_for_inputs(*tuple(value)))
            else:
                if self.has(kwargs['id']):
                    self.update(id=kwargs['id'], data=kwargs)
                    return
                else:
                    sql = "INSERT INTO {} {} VALUES {};".format(self.TableHook, column_arrangements_for_inputs(*tuple(column)), value_arrangements_for_inputs(*tuple(value)))

            self.master.cur.execute(sql)
        return self.master.save()
        
    
    def update(self, id=None, data={}):
        """ Update Row Values """
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
        #print sql.format(self.TableHook,sentence[:-1], id)
        return self.master.save()
    
    def get_all(self):
        """ Get All Row Object In List """
        sql = "SELECT id from {}".format(self.TableHook)
        result = self.master.cur.execute(sql)
        return [self.Row(i[0]) for i in result.fetchall()]
    
    def search(self, **kwargs):
        """ Search For Row Object Interface """
        sentence = ""
        for i,j in kwargs.iteritems():
            sentence = sentence + " {} = '{}' AND".format(i,j)
        sql = "SELECT id from {} WHERE{};".format(self.TableHook,sentence[:-3])
        result = self.master.cur.execute(sql)
        print "Search trgger"
        return [self.Row(i[0]) for i in result.fetchall()]
    
    def delete(self, id):
        """ Delete Row """
        if type(id)==type(1) or type(id)==type('1'):
            sql = 'DELETE from {} WHERE id = {};'.format(self.TableHook, str(id))
            self.master.cur.execute(sql)
            return
        sql = 'DELETE from {} WHERE id = {};'.format(self.TableHook, str(id.__id__))
        self.master.cur.execute(sql)
        return self.master.save()
    
    def has(self, id):
        """ Verify Row Available or Not """
        result = self.get(id)
        return True if result else False
    
    def columns_name(self):
        """ Get All Columns Name In List"""
        return self.master.get_all_columns_(self.TableHook)
    
    def save(self):
        """ Commit all Changes Into Database"""
        return self.master.save()
        
     
    def get_tables_name(self):
        """ Get All Tables Names In List"""
        return self.master.get_all_tables_name()
    
    def table_access(self, table):
        """ Change Working Table Access"""
        self.TableHook = table
        return self.TableHook


    
class Model(object):
    """ Model Object Interface
    #
    #
    #   connect(path="", dbname=None)   --> Connect To Database
    #
    #   close()                         --> Close Database
    #
    #   save()                          --> Save All Changes
    #
    #   get_db_names()                  --> Get Default Database Name
    #
    #   get_all_columns_(TableName)     --> Get All Columns Name List
    #
    #   get_all_table_with_class()      --> Get All Tables With Class Object As Dictonery
    #
    #   get_all_tables_name()           --> Get All Tables Name
    #
    #   get_tables()                    --> Get All Tables Object
    #
    #   Table(name=None)                --> Get Table Object
    #
    """
    def __init__(self):
        pass
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return "< DataBase:{} >".format(self.get_db_names())
    
    def connect(self, path="", dbname=None):
        """ Connect To Database And Get sqlite.connect object"""
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
        print "Database Ready!"
        if db_is_new:
            self.create_new_tables()
        self.check_for_new_tables()
        return
    
    def check_for_new_tables(self):
        """ Check For New Tables """
        print "[*] Checking Tables And Columns"
        (match, unmatch ) = self.check_available_tables()
        return [self.create_new_table(i) for i in unmatch]
            
        
    
    def Table(self, name):
        """ Get Table Object Using Name """
        return TableInterFace(self,name) 
    
    
    def close(self):
        """ Close Database """
        return self.dbase.close()
    
    def save(self):
        """ Commit All Changes Into Database """
        return self.dbase.commit()
    
    def get_db_names(self):
        """ Get Class Name From Proxy Main Class """
        return self.__class__.__name__.__str__() 
    
    def get_all_columns_(self, TableName):
        """ Get All Columns In List From Proxy Main Class """
        return [i for i in dict(self.__class__.__dict__[TableName].__dict__).iteritems() if "__" not in i[0]]
    
    def get_all_table_with_class(self):
        """Get All Tables With Class Object From Proxy Main Class """
        return [i for i in dict(self.__class__.__dict__).iteritems() if "__" not in i[0]]
    
    def get_all_tables_name(self):
        """ Get All Tables Name  From Proxy Main Class """
        return [i[0] for i in self.get_all_table_with_class()]
    
    def get_tables(self):
        """ Get All Tables Object """
        data={}
        for i in self.get_all_tables_name():
            data[i]=self.Table(name=i)
        return data
    
    
    def create_new_table(self, ntable):
        """ Create New Table """
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
        """ Create New Tables """
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
        """ Get Tables From Database """
        data= []
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for i in self.cur.fetchall():
            data.append(i[0])
        return data
    
    def check_available_tables(self):
        """ Check Available Tables Into Database """
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
    
#
# If You Really Like My Script.
#
# Then, You Can Give Me Complements
#
# ON Email, On Blog:
#
#    Name  : S.S.B
#    
#    Email : surajsinghbisht054@gmail.com
#
#    Blog  : https://bitforestinfo.blogspot.com
#
#    Github: https://github.com/surajsinghbisht054 
#
# ============================
# (^_^) HAVE A NICE DAY (^_^)
# ============================
#