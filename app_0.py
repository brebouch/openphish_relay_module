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
	Everytime SecureX send an Health check to the relay module on the /health API, then we trigger a sqlote database update.
	Meaning that we read the openphish index page and we add into the sqlite database all new bad URLs.
	If everything is successfull we send back a success message to SecureX
'''

@app.route('/health', methods=['POST'])
def health():   
    health_result=update_database()
    if health_result!=0:
        data = {'status': 'ok'}
    else:
        data = {'status': 'error'}
    return jsonify({'data': data}) 

@app.route('/tiles', methods=['POST'])
def tiles():
    try:
        auth = get_jwt()
        return jsonify_data([])
    except:
        return jsonify_data([])	
	
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)