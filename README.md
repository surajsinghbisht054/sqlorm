# sqlorm
Object-Relational Mapper For Python Sqlite3

# On Progress

author:
	surajsinghbisht054@gmail.com
	
## ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
##       Object InterFace Manual
## ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
## author:
##   S.S.B
##   surajsinghbisht054@gmail.com
##   https://bitforestinfo.blogspot.com
##
##
## About sqlorm:  
##       A Python object relational mapper for SQLite3.
##
## Reference:  https://www.sqlite.org/lang.html
##            https://docs.python.org/3/library/sqlite3.html
##
## Import:
##   from sqlorm import Model, Field
##
##
## =====================================
## =========== DataBase ================
## =====================================
##
##   connect(path="", dbname=None)   --> Connect To Database
##   close()                         --> Close Database    
##   save()                          --> Save All Changes
##   get_db_names()                  --> Get Default Database Name
##   get_all_columns_(TableName)     --> Get All Columns Name List
##   get_all_table_with_class()      --> Get All Tables With Class Object As Dictonery
##   get_all_tables_name()           --> Get All Tables Name
##   get_tables()                    --> Get All Tables Object
##   Table(name=None)                --> Get Table Object
##
##
## =====================================
## ============= Table =================   
## =====================================
##
##   new()               --> New Row Interface
##   insert(**kwargs)    --> Insert New Values Into Row, id argument Required
##   update(id=None, data={}) --> Update Values Into Row
##   delete(id)          --> Delete Row , Id argument Required
##   search(**kwargs)    --> Search Row Object InterFace
##   get_all()           --> Get All Row Object InterFace as list
##   has(id)             --> Check Row
##   columns_name()      --> Get All Columns Names As List
##   save()              --> Save All Changes
##   get_tables_name()   --> Get Current Object Table Name
##   table_access(TableName) --> Change Current Object Table Access
##
##
## =====================================
## ============= Row ===================
## =====================================
##
##   get_all()           --> Get All Values In Dictionery
##   set_all(**kwargs)   --> Set Values
##   save()              --> Save Changes Into Database
##