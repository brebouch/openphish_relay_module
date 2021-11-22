from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify,current_app, g
from schemas import DashboardTileDataSchema, DashboardTileSchema,ObservableSchema
from utils import get_json, get_jwt, jsonify_data,current_date_time,date_plus_x_days,epoch_date,epoch_datetime,format_docs
import os
from crayons import *
import requests
import json
from datetime import datetime, timedelta
import time
from get_openphish_index_page import update_database,create_connection,get_number_of_items,gen_bar_chart_data_list,is_observable_in_database # Update the sqlite database during SecureX Health Check

'''
	Now let's send back to SecureX enrichment result JSON data.
	add g to 
		from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify,current_app, g
		
	add format_docs in 
		from utils import get_json, get_jwt, jsonify_data,current_date_time,date_plus_x_days,epoch_date,epoch_datetime,format_docs
		
	add the get_verdict(observable_value, observable_type,disposition, valid_time) functions
	
	add additionnal activities to the : /deliberate/observables route
'''

app = Flask(__name__)


def get_verdict(observable_value, observable_type,disposition, valid_time):
	'''
		Format the observable disposition into the CTIM format
	'''
	if disposition[0]==1:
		disposition_name='Clean'
	elif disposition[0]==2:
		disposition_name='Malicious'
	elif disposition[0]==3:
		disposition_name='Suspicious'
	elif disposition[0]==4:
		disposition_name='Common' 
	elif disposition[0]==5:
		disposition_name='Unknown'		
	else:
		disposition_name='Unknown'		 
	return {
		'type': 'verdict',
		'observable': {'type': observable_type, 'value': observable_value},
		'disposition': disposition[0],
		'disposition_name': disposition_name,
		'valid_time': valid_time,
	}
	
	
def group_observables(relay_input):
	# Leave only unique observables ( deduplicate observables )  and select some specific observable types defined in the config.py file
	# return a list of observable to investigate (  type and values )
	result = []
	for observable in relay_input:
		o_value = observable['value']
		o_type = observable['type'].lower()
		# Get only supported types by this third party : and openphish support only urls
		if o_type=='url':
			obj = {'type': o_type, 'value': o_value}
			if obj in result:
				continue
			result.append(obj)
	return result

def build_input_api(observables):
	# formating and cleanup function for observables
	for observable in observables:
		o_value = observable['value']
		o_type = observable['type'].lower()
		o_value = o_value.split('://')[-1]#  let's extract only the url without https:// or http://
		observable['value'] = o_value
	return observables
	
	
def gen_json_for_bar_chart(data_in,tile_id,key_type):
	temps=current_date_time()
	tile_json={}
	tile_json["valid_time"]={
		"start_time": temps,
		"end_time": temps
	}
	tile_json["tile_id"] = tile_id
	tile_json["keys"] = []
	tile_json["cache_scope"] = "org"
	tile_json["key_type"] = key_type
	tile_json["period"] = "last_7_days"
	tile_json["observed_time"]= {
		"start_time": temps,
		"end_time": temps
	}	
	data_list=[]
	ii=0
	for item in data_in:
		print(cyan(item,bold=True)) 
		print(yellow(len(item),bold=True))
		data_dict_item={}
		if key_type=='timestamp':
			data_dict_item["key"]=epoch_date(item[0])
		else:
			data_dict_item["key"]=item[0]
		url=item[1]
		i=0
		data_dict_item["values"]=[]
		for sub_item in item:
			print(red(i,bold=True))
			entry={}
			if i>1 and i<len(item):
				entry["key"]= item[i]
				entry["value"]= item[i+1]
				entry["tooltip"]= f"{item[i]} : {item[i+1]}"
				entry["link_uri"]= url							 
				data_dict_item["values"].append(entry)
				if ii==0:
					new_key={}
					new_key={"key": item[i],"label": item[i]}
					tile_json["keys"].append(new_key)				
				i+=1
			i+=1			
		data_list.append(data_dict_item)
		ii+=1
	tile_json["data"]=data_list
	print(yellow(tile_json))
	return(tile_json)
	

def gen_json_for_line_chart(data_in,tile_id):
	start_time=current_date_time()
	end_time=current_date_time()	
	tile_json={}
	tile_json["valid_time"]={
		"start_time": start_time,
		"end_time": end_time
	}
	tile_json["tile_id"] = tile_id
	tile_json["keys"] = []
	tile_json["cache_scope"] = "user"
	tile_json["key_type"] = "timestamp"
	tile_json["period"] = "last_7_days"
	tile_json["observed_time"]= {
		"start_time": start_time,
		"end_time": end_time
	}	
	data_list=[]
	ii=0
	for item in data_in:
		print(cyan(item,bold=True)) 
		print(yellow(len(item),bold=True))
		data_dict_item={}
		data_dict_item["key"]=epoch_datetime(item[0])  
		data_dict_item["value"]=item[1]
		data_list.append(data_dict_item)
	tile_json["data"]=data_list
	return(tile_json)
	
def gen_json_for_donut(data_in,tile_id): 
	start_time=current_date_time()
	end_time=current_date_time()	
	tile_json={}
	tile_json["valid_time"]={
		"start_time": start_time,
		"end_time": end_time
	}
	tile_json["tile_id"] = tile_id
	tile_json["labels"] = []
	tile_json["labels"].append([])
	if len(data_in[0])>4:
		tile_json["labels"].append([])
	tile_json["cache_scope"] = "user"
	tile_json["period"] = "last_7_days"
	tile_json["observed_time"]= {
		"start_time": start_time,
		"end_time": end_time
	}	
	data_list=[]
	ii=0
	key_index=0
	for item in data_in:
		print(cyan(item,bold=True)) 
		print(yellow(len(item),bold=True))
		data_dict_item={}
		data_dict_item["key"]=key_index  
		data_dict_item["value"]=item[3]
		key_index+=1
		tile_json["labels"][0].append(item[2])
		url=item[1]
		i=0
		iii=0
		if len(item)>4:
			data_dict_item["segments"]=[]
			for sub_item in item:
				print(red(i,bold=True))
				entry={}
				if i>3 and i<len(item):
					entry["key"]= item[i]
					entry["value"]= item[i+1]
					entry["tooltip"]= f"{item[i]} : {item[i+1]}"
					entry["link_uri"]= url							 
					data_dict_item["segments"].append(entry)
					if item[i] not in tile_json["labels"][1]:
						tile_json["labels"][1].append(item[i])
					if ii==0:
						new_key={}
						new_key={"key": iii,"value": item[i]}  
						iii+=1
					i+=1
				i+=1			
		data_list.append(data_dict_item)
		ii+=1
	tile_json["data"]=data_list
	return(tile_json)

def gen_donut_data_list():
	number_of_items_in_sqlite_database=get_number_of_items()
	data_list_for_donut=[]
	data_list_for_donut.append([
		"OpenPhish Bad URLs",
		"https://openphish.com/",
		"OpenPhish Bad URLs",
		number_of_items_in_sqlite_database
	])
	#data_list_for_donut[0].append(number_of_items_in_sqlite_database)
	data_list_for_donut.append([
		"Threat Intell 2",
		"https://google.com",
		"Threat Intel Bad URLs 2",183,   
	])
	data_list_for_donut.append([
		"Threat Intell 3",
		"https://google.com", 
		"Threat Intel Bad URLs 3",20,   
	]
	)
	return(data_list_for_donut)

@app.route('/observe/observables', methods=['POST'])
def observe_observables():
	#_ = get_jwt()
	#_ = get_observables()
	return jsonify_data({})
	
@app.route('/deliberate/observables', methods=['POST'])
def deliberate_observables():
	# 0- retreive the third party API Key
	# api_key = get_jwt()  # we don't use authentication for Openphish
	data = {} # Let's create a data directory to be sent back to Threat Response
	g.verdicts = []   # Let's create a list into which we will store valid verdicts data results for every observables	
	# 1 - get observable sent by SecureX Threat Response and put them into the relay_input variable
	relay_input = get_json(ObservableSchema(many=True))
	# 2 - Select observable type and de ducplicate observables
	observables = group_observables(relay_input)   
	# 3 - if the obsvervables list is empty exit and return nothing
	if not observables:
		return jsonify_data({})
	# 4 - observables is not empty  then let's continue and format correctly observables
	observables = build_input_api(observables)
	# 5 -  go thru the observable list one by one and send an Query our third party solution ( in our case we query our sqlite database )
	for observable in observables:
		o_value = observable['value']
		o_type = observable['type'].lower()
		print(green(o_value,bold=True))
		# Send Reputation request to the Third Party
		# in our case we query the sqlite database in order to check if it contains the observable and create a disposition
		is_in_sqlite_db=is_observable_in_database(o_value)
		'''
		DISPOSITIONS_VALUES = {
			'clean': (1, 'Clean'),
			'malicious': (2, 'Malicious'),
			'suspicious': (3, 'Suspicious'),
			'common': (4, 'Common'),
			'unknown': (5, 'Unknown')
		}
		'''			
		disposition_tuple=()
		if is_in_sqlite_db:
			disposition_tuple=(2, 'Malicious')
		else:
			disposition_tuple=(5, 'Unknown')
		print(cyan(' OpenPhish Disposition is : ',bold=True))	
		print(cyan(disposition_tuple,bold=True))	
				
		# we have the disposition_tuple  then get the current date and calculate end date as an end of life date for judgment and verdicts
		# We need these information as mandatory information to return to Threat Response
		start_time = datetime.utcnow()
		end_time = start_time + timedelta(weeks=1)
		valid_time = {
			'start_time': start_time.isoformat() + 'Z',
			'end_time': end_time.isoformat() + 'Z',
		}
		# Let's append a new verdict item into the verdicts list with the minimum of information expected by the CTIM format
		g.verdicts.append(get_verdict(o_value, o_type, disposition_tuple, valid_time))	 

	# The g.verdicts list content all verdicts for every requested observable.  Let's add this list into the data dictionnary and do some formatting stuffs
	if g.verdicts:
		data['verdicts'] = format_docs(g.verdicts)
		
	# Let's get ready to send back a valid CTIM JSON result to the original Threat Response request . Let's put it into the result dictionnary
	result = {'data': data}  
	print(green(f"JSON result to be sent to Threat Response : \n{result}",bold=True))		
	return jsonify_data(data)
	
@app.route('/tiles/tile-data', methods=['POST'])
def tile_data():
	_ = get_jwt() # we will use this later for authentication to third party solution
	req = get_json(DashboardTileDataSchema())
	print (green(req,bold=True))
	print (green(req["tile_id"],bold=True))
	if req['tile_id'] == 'vertical_histogram':
		if req['period'] == 'last_7_days':
			data_list=gen_bar_chart_data_list(7)# we will change this later
		elif req['period'] == 'last_30_days':
			data_list=gen_bar_chart_data_list(30) # # we will change this later	
		else:
			data_list=gen_bar_chart_data_list(1) # we will change this later
		#print(cyan(donnees,bold=True))
		#key_type="timestamp"
		key_type="string"
		data_to_graph=gen_json_for_bar_chart(data_list,req['tile_id'],key_type)
		return jsonify_data(data_to_graph)
	if req['tile_id'] == 'donut':  
		data_list=gen_donut_data_list()		
		data_to_graph=gen_json_for_donut(data_list,req['tile_id'])
		print(data_to_graph)
		#data_to_graph=json_data_for_donuts3
		return jsonify_data(data_to_graph)		
	elif req['tile_id'] == 'other tile id':
		some_json_payload={}
		return jsonify_data(some_json_payload)	
				
@app.route('/tiles', methods=['POST'])
def tiles():
	try:
		auth = get_jwt()
		return jsonify_data([
			{
				"title": "OpenPhish Histogram",
				"description": "Vertical Histogram",
				"periods": [
					"last_24_hours",
					"last_7_days",
					"last_30_days"
				],
				"default_period": "last_7_days",
				"tags": [
					"pat",
					"url"
				],
				"type": "vertical_bar_chart",
				"short_description": "The number of bad URL per day",
				"id": "vertical_histogram"
			},			
			{
				"title": "OpenPhish Donut",
				"description": "OpenPhish Donut",
				"tags": [
					"pat"
				],
				"type": "donut_graph",
				"short_description": "DONUT Example",				
				"default_period": "last_7_days",
				"id": "donut"
			}			 
		])
	except:
		return jsonify_data([])

@app.route('/health', methods=['POST'])
def health():   
	health_result=update_database()
	if health_result!=0:
		data = {'status': 'ok'}
	else:
		data = {'status': 'error'}
	return jsonify({'data': data}) 

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=4000)