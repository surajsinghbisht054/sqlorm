# Python SQL-ORM

Python SQLite Object-Relational Mapper 



	'   ________  ________  ___       ________  ________  _____ ______      
	'  |\   ____\|\   __  \|\  \     |\   __  \|\   __  \|\   _ \  _   \    
	'  \ \  \___|\ \  \|\  \ \  \    \ \  \|\  \ \  \|\  \ \  \\\__\ \  \   
	'   \ \_____  \ \  \\\  \ \  \    \ \  \\\  \ \   _  _\ \  \\|__| \  \  
	'    \|____|\  \ \  \\\  \ \  \____\ \  \\\  \ \  \\  \\ \  \    \ \  \ 
	'      ____\_\  \ \_____  \ \_______\ \_______\ \__\\ _\\ \__\    \ \__\
	'     |\_________\|___| \__\|_______|\|_______|\|__|\|__|\|__|     \|__|
	'     \|_________|     \|__|                                            
	'                                                                       
	'                                                                       


SQL-ORM Is a Python Object Relational Mapper for SQLite3. With These Script, We Can Use Python SQLite API Very Easly.

- Easy To Use

- Easy To Maintain


# Features


- Can Access More Than One Database At a Time.

- Can Access More Than One Table At a Time.

- Can Access More Than One Row At a Time.

- No External Dependencies



# Reference  


- https://www.sqlite.org/lang.html

- https://docs.python.org/3/library/sqlite3.html

# Under Development.


# Examples

1. Import Module Content.

```
	# Import Module
	from sqlorm import Field, Model
```
2. Define Model Structure.
```

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
	
    	class AboutBooks:
        	# Creating 4 Columns. Name = Name, Price, Class
       		 #
        	# Columns   DataType
        	Name    =   Field.String
        	Price   =   Field.Integer
        	Class   =   Field.String
        	#                   

```
3. Read Comments
```
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

	# Set New Values Using set_all
	n.set_all(Age=10, Income = 45000, Name = "Sam")



	# Get All Values as Dictionery
	print n.get_all()

	# Save Row InterFace 
	n.save()

	# Get Row Interface
	r = t.get(id)


	# Close database
	DBase.save()
	
```
# Documentation.
- Check Here :- http://bitforestinfo.blogspot.com/p/sql-orm-documentation.html


# Author.

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



# Development.


Want to Contribute? Great!


There Are 2 Methods.

1. Pull Request ( Github Account Required ).

2. Through Email.


### 1. Pull Request ( Github A/c Required ). 

1. Fork it!

2. Create your feature branch: `git checkout -b my-new-feature`

3. Commit your changes: `git commit -am 'Add some feature'`

4. Push to the branch: `git push origin my-new-feature`

5. Submit a pull request :D



### 2. Through Email.

1. Send Your Updated Version On My Email.

- surajsinghbisht054@gmail.com


-----

## Contributing

See [CONTRIBUTING](/CONTRIBUTING.md).

----

## License

Apache License



