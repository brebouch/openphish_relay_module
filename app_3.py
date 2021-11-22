from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify
from schemas import DashboardTileDataSchema, DashboardTileSchema
from utils import get_json, get_jwt, jsonify_data,current_date_time,date_plus_x_days,epoch_date,epoch_datetime
import os
from crayons import *
import requests
import json
from datetime import datetime, timedelta
import time
from get_openphish_index_page import update_database,create_connection,get_number_of_items,gen_bar_chart_data_list # Update the sqlite database during SecureX Health Check


'''
    Now based on the app_2.py template, we are going to generate dynamically JSON Payload to be displayed
'''

app = Flask(__name__)

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
                    "last_hour",
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
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)