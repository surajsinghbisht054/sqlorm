#!/usr/bin/python
# coding: utf-8

# In[1]:


#
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#       Object InterFace Manual
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   author:
#       surajsinghbisht054@gmail.com
#       https://bitforestinfo.blogspot.com
#
#
#    About sqlorm:  
#          A Python object relational mapper for SQLite3.
#
#    Reference:  https://www.sqlite.org/lang.html
#               https://docs.python.org/3/library/sqlite3.html
#
#    Import:
#      from sqlorm import Model, Field
#


# In[2]:

# Import Module
from sqlorm import Field, Model
import os

# In[3]:

# Creating A Database Models Structure
#
# Here, "TestingDataBase" is used as default Sqlite Database File Name 
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


# In[4]:

#
#    =====================================
#    =========== DataBase ================
#    =====================================
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
# Create Object For InterFace        
DBase = TestingDataBase()

# Connect To DataBase
DBase.connect()
# or 
# DBase.connect(dbname="Testing_DataBase")


# In[5]:

# Get All Available Tables Names as list
print DBase.get_all_tables_name()

# Get All Tables With Interface Object In Dictionery
print DBase.get_tables()


# In[6]:

# Get All Columns Names From Tables
for table in DBase.get_all_tables_name():
    print "Table Name : {}".format(table) 
    print DBase.get_all_columns_(table) # As List


# In[7]:

# Default Database Name 
print DBase.get_db_names()


# In[8]:

#
#
#    =====================================
#    ============= Table =================   
#    =====================================
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
# Get Table Interface
t = DBase.Table(name="AboutTeachers")
# or
t = DBase.get_tables()["AboutTeachers"]

print t


# In[9]:

#
# =====================================
# ============= Row ===================
# =====================================
#
#   get_all()           --> Get All Values In Dictionery
#   set_all(**kwargs)   --> Set Values
#   save()              --> Save Changes Into Database
#
#
# Create New Row Object Interface
nr = t.new()

print nr

for i in xrange(150):
	# In[10]:	
	
	# Set Values
	
	nr.Age = 10        # Column Age
	
	nr.Income = 45000  
	
	nr.Name = "Suraj"

	nr.save()
	
# In[11]:

# Print Assign Values
print nr.get_all()


# In[12]:

# Save Data Values In Database
nr.save()
#
# You Don't Need To Create New Row Object Again And Again.
# Because After Saving Data., 
# Row Object Interface Reset Automatically.
# And Then You Can Use Object 


# In[13]:

# Get All Values From Row Object Interface After Saving
print nr.get_all()


# In[14]:

# Set New Values Using set_all
nr.set_all(Age=10, Income = 45000, Name = "Sam")


# In[15]:

# Get All Assigned Values As Dictonery
print nr.get_all()


# In[16]:

# Save Changes
print nr.save()


# In[17]:

# Get All Row Object Interface As List
print t.get_all()


# In[18]:

# Get Row Object Interface, Using Id As List
print t.get(id=2)


# In[19]:

# For Accessing Row Object Interface
storeobj = t.get(id=1)[0]


# In[20]:

# Get All Values As Dictonery From Row Object Interface
print storeobj.get_all()


# In[21]:

# Updae Value
storeobj.Income = 50000


# In[22]:

# Save Update
storeobj.save()


# In[23]:

# Get All Row Object Interface 
for i in t.get_all():
    # Get All Values From Row OBject Interface As Dictonery
    print i.get_all()


# In[24]:

# Search Row Object Interface Using Any Values of column
obj = t.search(Income=45000)[0]

print obj


# In[25]:

# Delete Row Using Row OBject Interface Or Id 
t.delete(obj)


# In[26]:

# Again! Get All Row Object Interface
t.get_all()


# In[27]:

# Get All Column Names Of Current Selected Table Object Interface
t.columns_name()


# In[28]:

# Get All Table Names 
t.get_tables_name()


# In[29]:

# Change Current Table Object Interface
t.TableHook


# In[30]:

# Save Changes
DBase.save()

# Close Database
DBase.close()

# Remove Database
os.remove('TestingDataBase.sqlite.db')

raw_input("[+] Testing Complete. \n Done! \n Have A Nice Day!")

