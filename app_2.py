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
from get_openphish_index_page import update_database # Update the sqlite database

app = Flask(__name__)

'''
    Now based on the app_1.py template, we are going to add JSON data to be graphed into tiles

    First as en example we create 2 json data example to display
    
    Second we add the /tiles/tile-data route
'''
json_data_for_bar_charts_v={
    "valid_time": {
        "start_time": "2021-04-27T18:06:26.000Z",
        "end_time": "2021-04-28T18:06:26.000Z"
    },
    "tile_id": "vertical_histogram_tile",
    "keys": [
        {
            "key": "something",
            "label": "something label"
        },
        {
            "key": "somethingelse",
            "label": "somethingelse label"
        },
        {
            "key": "andsomethingelse",
            "label": "andsomethingelse label"
        }        
    ],
    "cache_scope": "user",
    "key_type": "string",
    "period": "last_24_hours",
    "observed_time": {
        "start_time": "2021-04-27T18:06:26.000Z",
        "end_time": "2021-04-28T18:06:26.000Z"
    },
    "data": [
        {
            "key": "FIRST",
            "label": "19:00:00",
            "value": 30,
            "values": [
                {
                    "key": "something",
                    "value": 30,
                    "tooltip": "something: 30",
                    "link_uri": "https://www.google.com"
                },
                {
                    "key": "somethingelse",
                    "value": 50,
                    "tooltip": "somethingelse: 50",
                    "link_uri": "https://www.google.com"
                },
                {
                    "key": "andsomethingelse",
                    "value": 10,
                    "tooltip": "andsomethingelse: 10",
                    "link_uri": "https://www.google.com"
                }  
                
            ]
        },     
        {
            "key": "SECOND",
            "label": "19:00:00",
            "value": 10,
            "values": [
                {
                    "key": "something",
                    "value": 10,
                    "tooltip": "something: 10",
                    "link_uri": "https://www.google.com"
                },                
                {
                    "key": "somethingelse",
                    "value": 50,
                    "tooltip": "somethingelse: 50",
                    "link_uri": "https://www.google.com"
                },
                {
                    "key": "andsomethingelse",
                    "value": 10,
                    "tooltip": "andsomethingelse: 10",
                    "link_uri": "https://www.google.com"
                }  
            ]
        },    
        {
            "key": "THIRD",
            "label": "19:00:00",
            "value": 20,
            "values": [
                {
                    "key": "something",
                    "value": 20,
                    "tooltip": "something: 20",
                    "link_uri": "https://www.google.com"
                },
                {
                    "key": "somethingelse",
                    "value": 50,
                    "tooltip": "somethingelse: 50",
                    "link_uri": "https://www.google.com"
                },
                {
                    "key": "andsomethingelse",
                    "value": 10,
                    "tooltip": "andsomethingelse: 10",
                    "link_uri": "https://www.google.com"
                }  
            ]
        }
    ]
}

json_data_for_donuts = {
    "labels": [
        [
            "Open",
            "New",
            "Closed"
        ],
        [
            "Assigned",
            "Unassigned"
        ]
    ],
    "valid_time": {
        "start_time": "2021-04-28T16:48:18.000Z",
        "end_time": "2021-04-28T17:48:18.000Z"
    },
    "tile_id": "donut_tile",
    "cache_scope": "user",
    "period": "last_hour",
    "observed_time": {
        "start_time": "2021-04-28T16:48:18.000Z",
        "end_time": "2021-04-28T17:48:18.000Z"
    },
    "data": [
        {
            "key": 0,
            "value": 2,
            "segments": [
                {
                    "key": 0,
                    "value": 10
                },
                {
                    "key": 1,
                    "value": 20
                }
            ]
        },
        {
            "key": 1,
            "value": 10,
            "segments": [
                {
                    "key": 0,
                    "value": 8
                },
                {
                    "key": 1,
                    "value": 0
                }
            ]
        },
        {
            "key": 2,
            "value": 5,
            "segments": [
                {
                    "key": 0,
                    "value": 0
                },
                {
                    "key": 1,
                    "value": 0
                }
            ]
        }
    ]
}

@app.route('/tiles/tile-data', methods=['POST'])
def tile_data():
    _ = get_jwt() # we will use this later for authentication to third party solution
    req = get_json(DashboardTileDataSchema())
    print (green(req,bold=True))
    print (green(req["tile_id"],bold=True))
    if req['tile_id'] == 'vertical_histogram':
        if req['period'] == 'last_7_days':
            data_to_graph=json_data_for_bar_charts_v # we will change this later
        elif req['period'] == 'last_30_days':
            data_to_graph=json_data_for_bar_charts_v # # we will change this later    
        else:
            data_to_graph=json_data_for_bar_charts_v # we will change this later
        #print(cyan(donnees,bold=True))
        return jsonify_data(data_to_graph)
    if req['tile_id'] == 'donut':      
        data_to_graph=json_data_for_donuts
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