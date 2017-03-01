<snippet>
  <content><![CDATA[
# sqlorm
Object-Relational Mapper For Python Sqlite3

# On Progress

author:
	surajsinghbisht054@gmail.com

## Contributing
1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D


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

## Examples:
	'''
	# Creating A Database Models Structure
	class TestingDataBase(Model):
    	# Creating New Table. Name="AboutTeachers"
    	class AboutTeachers:
        	# Creating 4 Columns. Name = Name, Age, Income, Phone
        	#
        	#Columns     Datatype
	        Name    =   Field.String
    	    Age     =   Field.Integer
    	    Income  =   Field.Integer
    	    Phone   =   Field.LongInt
    	    #
	
	    # Creating New Table. Name="AboutBooks"
	    class AboutBooks:
	        # Creating 4 Columns. Name = Name, Price, Class
    	    #
        	# Columns   DataType
        	Name    =   Field.String
        	Price   =   Field.Integer
        	Class   =   Field.String
        	#                   

	    # Creating New Table. Name="AboutStudents"
    	class AboutStudents:
        	# Creating 4 Columns. Name = Name, Age, Class, Phone
       		 #
        	#Columns     Datatype
        	Name    =   Field.String
        	Age     =   Field.Integer
        	Class  =   Field.String
        	Phone   =   Field.LongInt
        	#



	# Create Object For InterFace        
	DBase = TestingDataBase()

	# Connect To DataBase
	DBase.connect(dbname="Testing_DataBase")
	# or Use Only DBase.connect() 

	# Get All Available Tables Names as list
	print DBase.get_all_tables_name()

	# Get All Columns Names From Tables
	for table in DBase.get_all_tables_name():
    	print "\nTable Name : {}\n".format(table) 
    	print DBase.get_all_columns_(table) # As List

	# Get All Tables With Interface Object In Dictionery
	print DBase.get_tables()

	# Default Database Name 
	print DBase.get_db_names()


	# Get Table Interface
	t = DBase.Table(name="AboutTeachers")
	# or
	t = DBase.get_tables()["AboutTeachers"]


	# Create New Row Interface
	n = t.new()
	# Set Values


	# Get All Values as Dictionery
	print n.get_all()

	# Save Row InterFace 
	n.save()
	# Get Row Interface
	r = t.get(id)


	# Close database
	DBase.save()
	'''
]]></content>
  <tabTrigger>readme</tabTrigger>
</snippet>
