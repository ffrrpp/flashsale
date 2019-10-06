""" This file largely follows the steps outlined in the Insight Flask tutorial, except data is stored in a
flat csv (./assets/births2012_downsampled.csv) vs. a postgres database. If you have a large database, or
want to build experience working with SQL databases, you should refer to the Flask tutorial for instructions on how to
query a SQL database from here instead.

May 2019, Donald Lee-Brown
"""

from flask import render_template
from flask import request
from webapp import app
import pandas as pd
import numpy as np
from webapp.check_current_listings import check_current_listings
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
	camera_catalog = pd.read_csv('./webapp/static/data/df_fix_summary.csv')
	camera_list = (camera_catalog['brand'].apply(lambda x:x.capitalize())+' '+camera_catalog['model']).tolist()
	err_message = "Camera model not supported. Please try again."
	if len(cam_model.split(' ', 1)) != 2:
		return render_template("webapp_input.html",camera_list=camera_list,error_message=err_message)

	brand = cam_model.split(' ', 1)[0]
	model = cam_model.split(' ', 1)[1]
	df_fix_summary = pd.read_csv('./webapp/static/data/df_fix_summary.csv')
	df_model = df_fix_summary[(df_fix_summary['brand']==brand.lower())&(df_fix_summary['model']==model)]

	if df_model.empty:
		return render_template("webapp_input.html",camera_list=camera_list,error_message=err_message)
	model_summary = df_model.iloc[0]
	model_summary = df_fix_summary[(df_fix_summary['brand']==brand.lower())&(df_fix_summary['model']==model)].iloc[0]


	# random forest model
	model_rf = pickle.load(open('./webapp/static/data/rf_fixedprice_binary_classification.pkl','rb'))
	year = model_summary['year']
	isDSLR = model_summary['isDSLR']
	model_median = model_summary['model_median']
	# numAucListing = model_summary['numAucListing_median']
	# numFixListing = model_summary['numFixListing_median']
	# pricePercentile = 0.5

	df_realtime = check_current_listings(brand,model)

	if df_realtime.empty:
		numAucListing=0
		numFixListing=0
		fixedPrice_list=[]
	else:
		numAucListing=df_realtime[df_realtime['listingType']=='auction']['modelId'].count()
		numFixListing=df_realtime[df_realtime['listingType']=='fixedprice']['modelId'].count()
		fixedPrice_list=(df_realtime[df_realtime['listingType']=='fixedprice']['price']/model_median).tolist()
	
	auc_median = model_summary['auc_median']
	# heroku server apparently 4 hours ahead of EDT
	now = datetime.datetime.now() - datetime.timedelta(hours=4)
	startDayInWeek = now.isoweekday()
	startHourInDay = now.hour
	now_string = now.strftime("%Y-%m-%d %H:%M")
	freeShipping = True
	returnsAccepted = True

	price = auc_median
	pricePercentile = sum(p<price for p in fixedPrice_list)/numFixListing if numFixListing>0 else 0.0
	test_features = np.array([year,isDSLR,model_median,startDayInWeek,startHourInDay,
	            numAucListing,numFixListing,pricePercentile,
	            freeShipping,returnsAccepted,price])

	# make suggestion
	if auc_median>=1.2 or not (np.argmax(model_rf.predict(test_features.reshape(1, -1)),axis=1)[0]):
	    selling_option = 'auc'
	    price = round(model_median*auc_median)
	else:
	    prices = 1.2+range(11)*(auc_median-1.2)/10
	    for price in prices:
	        pricePercentile = sum(p<price for p in fixedPrice_list)/numFixListing if numFixListing>0 else 0.0
	        test_features = np.array([year,isDSLR,model_median,startDayInWeek,startHourInDay,
	        	numAucListing,numFixListing,pricePercentile,
	        	freeShipping,returnsAccepted,price])
	        if np.argmax(model_rf.predict(test_features.reshape(1, -1)),axis=1)[0]:
	            selling_option = 'fix'
	            price = round(model_median*price)
	            break
	return render_template("webapp_output.html",cam_model=cam_model, now_string =now_string, numFixListing=numFixListing, selling_option=selling_option, price=price)

# faqs
@app.route('/faq')
def faq():
	return render_template("faq.html")

# about me
@app.route('/about')
def about():
	return render_template("about.html")