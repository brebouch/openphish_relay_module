import sys
import sqlite3

def create_db_and_table():
    sql_create=f"CREATE TABLE IF NOT EXISTS observables ( id text PRIMARY KEY, url text, judgment text, targeted_brand text, date text,hour text,min text);" 
	#with sqlite3.connect(':memory:') as conn:
    with sqlite3.connect('database.db') as conn:
        c=conn.cursor()
        try:
            c.execute(sql_create)
        except:
            sys.exit("couldn't create database")
    return()

if __name__ == "__main__":	
	create_db_and_table()
	print('DONE\ndatabase.db was created\ntable [observables] with column was created')