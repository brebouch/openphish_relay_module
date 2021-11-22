import requests
import sys
import time
from crayons import *
from datetime import datetime, timedelta
import json
import sqlite3
import time
sqlite_data=[]

i=0	

def current_date_time():
	'''
		get current date time in yy-mm-dd-H:M:S:fZ format 
	'''
	current_time = datetime.utcnow()
	current_time = current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
	return(current_time)
	
def date_plus_x_days(nb): 
	'''
		calculate current date + nb day in yy-mm-dd-H:M:S:fZ format 
	'''
	current_time = datetime.utcnow()
	start_time = current_time + timedelta(days=nb)
	timestampStr = start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
	return(timestampStr)
	
def add_observable(observable):
	'''
		generate SecureX judgment payload for secureX
	'''
	print('===>')
	print(yellow('Prepare new Judgment for :',bold=True))
	print(green(observable,bold=True))
	start_time=current_date_time()
	end_time=date_plus_x_days(7)
	
	payload = {
  "valid_time": {
	"start_time": start_time,
	"end_time": end_time
  },
  "schema_version": "0",
  "observable": {
	"value": observable,
	"type": "url"
  },
  "reason_uri": "string",
  "type": "judgement",
  "source": "SecureX OPENPHISH",
  "disposition": 2,
  "reason":"",
  "source_uri":"https://openphish.com/",
  "disposition_name": "Malicious",
  "priority":90,
  "severity": "Medium",
  "tlp": "green",
  "id":"transient:976191af-21c7-42e0-bceb-79dc28d47834",
  "timestamp": start_time,
  "confidence": "Medium",
	"groups": [
	  "41603826-608e-4a4e-8b62-b17f9064f9bd"
	],  
  "owner": "bb4c07d3-3b8c-41a6-b0ea-a86e5f95d7a0"
}  
	add_to_judgment=0
	if add_to_judgment:
		payload = json.dumps(payload)
		url = 'https://private.intel.eu.amp.cisco.com/ctia/judgement'
		headers = {'Authorization':'Bearer {}'.format(access_token), 'Content-Type':'application/json', 'Accept':'application/json'}	
		response = requests.post(url, headers=headers, data=payload)
		print(green(response.json(),bold=True))
	return payload		

def create_connection(db_file):
	""" create a database connection to the SQLite database
		specified by db_file
	:param db_file: database file
	:return: Connection object or None
	"""
	conn = None
	try:
		conn = sqlite3.connect(db_file)
	except Error as e:
		print(e)
	return conn
	
def insert_data_to_db(conn,data):
	sql_add="INSERT into observables (id, url, judgment, targeted_brand) VALUES (?,?,?,?)"			
	print(green(data,bold=True))
	try:
		c=conn.cursor()
		c.executemany(sql_add, data)
		conn.commit()
	except:
		print('========')
		sys.exit("Error adding data to db")
	return()
	
def get_last_index():
	conn=create_connection('database.db') # open connection to database
	if conn:
		# connection to database is OK
		c=conn.cursor()
		sql_query="select count(*) from observables"
		c.execute(sql_query)
		numberOfRows = c.fetchone()[0]
		print('numberOfRows '+str(numberOfRows))		
	else:
		sys.exit('can not open sqlite database')
	return(numberOfRows)
	
def is_observable_in_database(url_to_check):
	conn=create_connection('database.db') # open connection to database
	#print(red(url_to_check,bold=True))
	if conn:
		# connection to database is OK
		c=conn.cursor()
		sql_query=f"select count(*) from observables where url like '%{url_to_check}%'"
		print(sql_query)
		c.execute(sql_query)
		numberOfRows = c.fetchone()[0]
		print('numberOfRows '+str(numberOfRows))		
	else:
		sys.exit('can not open sqlite database')
	return(numberOfRows)	
	
def get_number_of_items():
	conn=create_connection('database.db') # open connection to database
	if conn:
		# connection to database is OK
		c=conn.cursor()
		sql_query="select count(*) from observables"
		c.execute(sql_query)
		numberOfRows = c.fetchone()[0]
		print('numberOfRows '+str(numberOfRows))
	return(numberOfRows)

def gen_bar_chart_data_list(days):	
	liste=[]
	with sqlite3.connect('database.db') as conn:
		cursor=conn.cursor()	  
		'''
		example of sql request
		sql_request = "SELECT *,count(*) from obsevables where source = 'Patrick HoneyPot' and disposition_name = 'Suspicious' group by `date`"
		''' 
		sql_request = "SELECT *,count(*) from observables group by `date`"
		cursor.execute(sql_request)
		rows = cursor.fetchall()
		nombre=len(rows)
		nombre0=int(nombre-days)
		print(red('Number of days in DB : '+str(nombre),bold=True))
		print(red('Start from Nombre0: '+str(nombre0),bold=True))
		data=[]
		dict_items={}	
		index=0
		for i in range(0,days):
			the_date=rows[nombre0+i][4]
			print(cyan(the_date))
			sql_query="select count(*) from observables where date = ?"
			cursor.execute(sql_query, (the_date,))
			numberOfRows = cursor.fetchone()[0]
			print('	-> number Of BAD URLs '+str(numberOfRows))	 
			list_items=[]
			if the_date not in dict_items:
				suspicious_nb='0'
			else:
				suspicious_nb=numberOfRows
			#print(cyan(rows[nombre0+i]))
			#print(red(suspicious_nb))			
			#list_items.append(index)
			url=f"https://openphish.com/"
			list_items.append(the_date)
			list_items.append(url)
			list_items.append("Bad URL")
			list_items.append(numberOfRows)
			print(cyan(list_items))
			data.append(list_items)
			index+=1

	print(yellow(data))
	return(data)		

		
def update_database():
	# get the index of the last item stored into the sqlite database
	i=get_last_index()+1
	# connect to openphish index and get the index html page in html format
	resp = requests.get('https://openphish.com/index.html')
	print(resp.status_code)
	#sys.exit()
	if resp.status_code==200:
		final_result_txt='' # create a text variable for receiving urls
		# then parse the html page and extract all urls and assoicated targeted brand names
		html_txt=''
		html_txt=resp.text # put all the html data into the html_txt variable
		html_line_list=html_txt.split('\n') # create a lis that contains every single line of the html result
		get_targeted_brand=0 # a flog used to trigger item storing into the database
		conn=create_connection('database.db') # open connection to database
		if conn:
			# connection to database is OK
			c=conn.cursor()
			# let's go to every lines one by one and let's extract url, targeted brand	
			nb=0
			for single_line in html_line_list:		
				if get_targeted_brand:  # if the flag had been set to 1 prior, that means that an URL had been parsed in the previous line and then we can parse the targeted brand
					targeted_brand_temp=single_line.split('>') # parsing for extracting targeted_brand
					targeted_brand=targeted_brand_temp[1].split('<') # parsing for extracting targeted_brand
					print(red(targeted_brand[0],bold=True)) 
					get_targeted_brand=0 # reset the flag			
					# Check if this observable is already in the database
					sql_query="select count(*) from observables where url = ?"
					c.execute(sql_query, (url[0],))
					numberOfRows = c.fetchone()[0]
					print('numberOfRows '+str(numberOfRows))			
					if not numberOfRows:
						# this observable is not already in the database
						sqlite_data=(i, url[0], judgment_definition, targeted_brand[0])
						sql_add="INSERT OR IGNORE into observables (id, url, judgment, targeted_brand) VALUES (?,?,?,?)"
						c.execute(sql_add, sqlite_data)
						conn.commit()
						i += 1	
						print(green('   Adding this row ',bold=True))
						nb+=1
					else:
						print(red('   This item already exists',bold=True))		
				if "url_entry" in single_line and "<td" in single_line: # this line contains a URL to parse
					url=single_line.split('>') # parsing for extracting the URL
					if url[1]:
						url=url[1].split('<') # parsing for extracting the URL					
						judgment_definition=json.dumps(add_observable(url[0])) # let's create a SecureX Judgmernt in case we want to store the URL in the our private intell
						print()					
						get_targeted_brand=1 # set flag to one in order to trigger targeted brand parsing in next line
			#let's return the last sqlite item index in the database
			return(i,nb)
		else:
			#sys.exit('can not open sqlite database')	
			return (0,0)
	else:
		return (0,0)
		
if __name__ == "__main__":
	go=1
	while go:		
		# body of the loop ...	break it with a ctrl+C	
		new_index,nombre=update_database()
		print(new_index)
		if new_index!=0:
			with open('log.txt','a+') as log:
				info=current_date_time()+' new db index :'+str(new_index)+' number of new entries : '+str(nombre)
				log.write(info)
				log.write('\n')		
			print()
			print(yellow('============================',bold=True))
			print()
			print(info)
			print()
			print(yellow('Waiting for next poll in 300 seconds ',bold=True))
			print(yellow('============================',bold=True))
			print()				
			time.sleep(300)
		else:
			go=0
			print(red('ERROR',bold=True))

		
