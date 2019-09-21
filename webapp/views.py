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
from flask import request

# here's the homepage
@app.route('/')
def homepage():
    return render_template("webapp_input.html")

# example page for linking things
@app.route('/example_linked')
def linked_example():
    return render_template("example_linked.html")


# now let's do something fancier - take an input, run it through a model, and display the output on a separate page

@app.route('/webapp_input')
def cam_price_input():
   return render_template("webapp_input.html")

@app.route('/webapp_output')
def cam_price_output():
   # pull 'cam_model' from input field and store it
   cam_model = request.args.get('cam_model')

   # read in our csv file
   auc_db = pd.read_csv('./webapp/static/data/auc_price.csv')
   fix_db = pd.read_csv('./webapp/static/data/fix_price.csv')

   auc_prices = auc_db[auc_db['model'] == cam_model].values
   fix_prices = fix_db[fix_db['model'] == cam_model].values

   return render_template("webapp_output.html", auc_prices=auc_prices, fix_prices=fix_prices)
