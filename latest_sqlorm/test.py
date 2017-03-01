#!/usr/bin/python
from sqlorm import Model, Field


class test_db_name(Model):
    class Table_Name_1:
        Title = Field.String 
        Website = Field.String
        Url  = Field.String
        Username  = Field.String
        Password  = Field.String
        Email  = Field.String
        Phone  = Field.Integer
        Question  = Field.String
        Answer  = Field.String
        Note  = Field.String
    class Table_Name_2:
        Title = Field.String 
        Website = Field.String
        Url  = Field.String
        Username  = Field.String
        Password  = Field.String
        Email  = Field.String
        Phone  = Field.Integer
        Question  = Field.String
        Answer  = Field.String
        Note  = Field.String
    class Table_Name_3:
        Title = Field.String 
        Website = Field.String
        Url  = Field.String
        Username  = Field.String
        Password  = Field.String
        Email  = Field.String
        Phone  = Field.Integer
        Question  = Field.String
        Answer  = Field.String
        Note  = Field.String
    class Table_Name_4:
        Title = Field.String 
        Website = Field.String
        Url  = Field.String
        Username  = Field.String
        Password  = Field.String
        Email  = Field.String
        Phone  = Field.Integer
        Question  = Field.String
        Answer  = Field.String
        Note  = Field.String
    class Table_Name_5:
        Title = Field.String 
        Website = Field.String
        Url  = Field.String
        Username  = Field.String
        Password  = Field.String
        Email  = Field.String
        Phone  = Field.Integer
        Question  = Field.String
        Answer  = Field.String
        Note  = Field.String
        
post = test_db_name()
print post.get_db_names()
print post.get_table_name()
table = post.get_all_table()
post.connect()


post.save()
