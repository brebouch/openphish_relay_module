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
	Now based on hte  app_0.py template, we add 2 tiles 
	A vertical Bar Chart
	A DONUT
	We do this in the /tiles route bellow	
'''

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