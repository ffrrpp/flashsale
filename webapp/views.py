""" This file largely follows the steps outlined in the Insight Flask tutorial, except data is stored in a
flat csv (./assets/births2012_downsampled.csv) vs. a postgres database. If you have a large database, or
want to build experience working with SQL databases, you should refer to the Flask tutorial for instructions on how to
query a SQL database from here instead.

May 2019, Donald Lee-Brown
"""

from flask import render_template
from webapp import app
from webapp.a_model import ModelIt
import pandas as pd
import numpy as np
from flask import request
import pickle
import datetime
import sklearn


# here's the homepage
@app.route('/')
def homepage():
	camera_catalog = pd.read_csv('./webapp/static/data/df_fix_summary.csv')
	camera_list = (camera_catalog['brand'].apply(lambda x:x.capitalize())+' '+camera_catalog['model']).tolist()
	return render_template("webapp_input.html",camera_list=camera_list)


# now let's do something fancier - take an input, run it through a model, and display the output on a separate page

@app.route('/webapp_input')
def cam_price_input():
	camera_catalog = pd.read_csv('./webapp/static/data/df_fix_summary.csv')
	camera_list = (camera_catalog['brand'].apply(lambda x:x.capitalize())+' '+camera_catalog['model']).tolist()
	return render_template("webapp_input.html",camera_list=camera_list)

@app.route('/webapp_output')
def cam_price_output():
	# pull 'cam_model' from input field and store it
	cam_model = request.args.get('cam_model')
	brand = cam_model.split(' ', 1)[0]
	model = cam_model.split(' ', 1)[1]

	df_fix_summary = pd.read_csv('./webapp/static/data/df_fix_summary.csv')
	model_summary = df_fix_summary[(df_fix_summary['brand']==brand.lower())&(df_fix_summary['model']==model)].iloc[0]

	# random forest model
	model_rf = pickle.load(open('./webapp/static/data/rf_fixedprice_binary_classification.pkl','rb'))
	year = model_summary['year']
	isDSLR = model_summary['isDSLR']
	model_median = model_summary['model_median']
	numAucListing = model_summary['numAucListing_median']
	numFixListing = model_summary['numFixListing_median']
	pricePercentile = 0.5
	auc_median = model_summary['auc_median']
	now = datetime.datetime.now()
	startDayInWeek = now.isoweekday()
	startHourInDay = now.hour
	now_string = now.strftime("%Y-%m-%d %H:%M")
	freeShipping = True
	returnsAccepted = True


	test_features = np.array([year,isDSLR,model_median,startDayInWeek,startHourInDay,
	            numAucListing,numFixListing,pricePercentile,
	            freeShipping,returnsAccepted,auc_median])

	# make suggestion
	if auc_median>=1.2 or not (np.argmax(model_rf.predict(test_features.reshape(1, -1)),axis=1)[0]):
	    selling_option = 'auc'
	    price = round(model_median*auc_median)
	else:
	    prices = 1.2+range(11)*(auc_median-1.2)/10
	    for price in prices:
	        test_features = np.array([year,isDSLR,model_median,startDayInWeek,startHourInDay,
	                    numAucListing,numFixListing,pricePercentile,
	                    freeShipping,returnsAccepted,price])
	        if np.argmax(model_rf.predict(test_features.reshape(1, -1)),axis=1)[0]:
	            selling_option = 'fix'
	            price = round(model_median*price)
	            break
	return render_template("webapp_output.html",cam_model=cam_model, now_string =now_string, selling_option=selling_option, price=price)
