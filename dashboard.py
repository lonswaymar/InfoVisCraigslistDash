from flask import Flask, render_template, request, redirect, url_for
import pandas as pd


import os
import matplotlib.pyplot as plt
import numpy as np

from analysis.scrape import scrape_ads, make_interactive_plot, plot_histograms

app = Flask(__name__)

        
@app.route("/")
def home():
    # Get the zip_code from query parameters
    location = request.args.get("user_query", "Denver")
    
    scrape_results = scrape_ads(location)
    df = pd.DataFrame(scrape_results, columns=["price", "area", "url"])
    slope = make_interactive_plot(df)
    plot_histograms(df)
    
    return render_template("home.html", 
                            user_query=location,
                            slope=slope)

@app.route("/submit", methods=["POST"])
def submit():
    # Capture the ZIP code from the form
    location = request.form.get("user_query")
    print(f"Location entered: {location}")
    
    # Redirect to home with the ZIP code as a query parameter
    return redirect(url_for("home", user_query=location))
