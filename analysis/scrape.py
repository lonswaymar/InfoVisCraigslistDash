import plotly.graph_objects as go
from opencage.geocoder import OpenCageGeocode
from scipy.optimize import curve_fit
import requests
from bs4 import BeautifulSoup
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

def scrape_ads(userQuery, numToScrape=40):   
    # example query: query = u'99352 USA'

    # Use OpenCage to get location and city name off of a user query
    # Populate those values into a Craigslist URL
    key = os.getenv("OPENCAGE_API_KEY")
    geocoder = OpenCageGeocode(key)
    resultGC = geocoder.geocode(userQuery)

    lat = resultGC[0]['geometry']['lat']
    lng = resultGC[0]['geometry']['lng']
    
    components = resultGC[0].get("components", {})
    
    # Check for city or independent_city in components
    city = components.get("city") or components.get("independent_city")
    city = city.lower().replace(" ", "").replace(".", "")
    formattedStr = resultGC[0]["formatted"]
    url = f"https://{city}.craigslist.org/search/apa?housing_type=6&lat={lat}&lon={lng}&max_bedrooms=5&min_bedrooms=2&search_distance=30#search=1~gallery~0~0"

    # Now for the Craigslist Result

    resultCL = requests.get(url)
    parentPage = BeautifulSoup(resultCL.text, "html.parser")

    # Get all of the ads on the page by using the 'a' tag which in HTML
    # signifies a hyperlink. 
    hyperlinkTags = set(parentPage.find_all('a'))
    
    returnData = []
    for tag in hyperlinkTags:
        if "href" in tag.attrs:
            subURL = tag.attrs["href"]

            if ((subURL!="#") & (subURL!="/") & ("apa/" in subURL)):
            # Check if the user-provided keyword is in the URL. If
                # so, add subURL to the list of hyperlinks.
                
                resultAd = requests.get(subURL)
                houseAd = BeautifulSoup(resultAd.text, "html.parser")
                tag1 = houseAd.find_all("span", class_="price")[0]
                tag2 = houseAd.find_all("span", class_="housing")[0]
                
                price = tag1.text.replace("$", "").replace(",", "").strip()
                area = tag2.text.split("-")[1].strip().replace("ft2", "")
                
                if (((len(price)>2) & (len(price)<5)) & ((len(area)>2) & (len(area)<5))):
                    # print(f"${price}")
                    # print(f"{area}")
                    # print(subURL)
                    
                    link = f'<a href="{subURL}">L</a>'
                    returnData.append([float(price), float(area), link])
                    
                
                # Cease searching when number of hyperlinks equals
                # numRequests.
                if len(returnData) == numToScrape:
                    break

    return returnData
    
    
    
def make_interactive_plot(df):

    fig = go.Figure()
    fig.add_trace(
            go.Scatter(
                x=df["area"],
                y=df["price"],
                mode="markers+text",
                hovertext=df["url"],
                text=df["url"],
                textposition="top center",
                textfont_size=8,
                marker=dict(size=15, color="skyblue")
            )
        )
        
    # Line of best fit
    def line(x, m, b): return m * x + b
    
    p, _ = curve_fit(line, df["area"], df["price"])
    fit = df["area"] * p[0] + p[1]
    fig.add_trace(
        go.Scatter(
            x=df["area"],
            y=fit,
            mode="lines",
            line=dict(color="red"),
        )
    )
    
    fig.update_layout(
        showlegend=False,
        autosize=True,
        margin=dict(l=20, r=20, t=26, b=20),
        title=dict(
            text="Montly Rent vs. Area of 40 most recently published advertisements",
            font=dict(size=20, color="darkgrey")
        ),
        xaxis=dict(
            title=r"Square Feet",  # Custom x-axis title with LaTeX
            titlefont=dict(size=24, color="black"),  # Font size and color
            tickfont=dict(size=19, color="darkgray"),  # Tick label size and color
            showgrid=True,  # Show gridlines

            zeroline=False,  # Hide zero line
            showline=False,   # Show axis line
            linecolor="lightgrey",  # Axis line color
            linewidth=2       # Axis line width
        ),
        yaxis=dict(
            title=r"Rent ($)",  # Custom x-axis title with LaTeX
            titlefont=dict(size=24, color="black"),  # Font size and color
            tickfont=dict(size=19, color="darkgray"),  # Tick label size and color
            showgrid=True,  # Show gridlines
            gridcolor="lightgray",  # Gridline color
            zeroline=False,  # Hide zero line
            showline=False,   # Show axis line
            linecolor="lightgrey",  # Axis line color
            linewidth=2       # Axis line width
        ),
    )

    # Save the interactive plot as an HTML file in the static folder
    fig.write_html("static/images/nonsenseplot_interactive.html",
                   config={'displayModeBar': False})
    
    return p[0]
    
    
def plot_histograms(df):

    # Ensure the images directory exists
    os.makedirs("static/images", exist_ok=True)
    bins = 8
    # Price histogram
    fig, ax = plt.subplots(figsize=(6,2))
    ax.hist(df["price"], bins=bins, color='skyblue', edgecolor='black')
    ax.set_title("Price ($)")
    ax.tick_params(axis='y', length=0)  # Hide y-axis tick marks, keep labels
    ax.tick_params(axis='x', length=0)

    
    
    ax.spines['right'].set_visible(False)  # Remove the right vertical line
    ax.spines['top'].set_visible(False)    # Remove the top horizontal line
    ax.spines['left'].set_color((0, 0, 0, 0.3))  # Set the left spine with 50% transparency (alpha = 0.5)
    ax.spines['bottom'].set_color((0, 0, 0, 0.3))  # Set the bottom spine with 50% transparency
    
    plt.savefig("static/images/price_histogram.png")
    plt.close()

    # Area histogram
    fig, ax = plt.subplots(figsize=(6,2))
    ax.hist(df["area"], bins=bins, color='skyblue', edgecolor='black')
    ax.set_title("Square Footage")
    
    ax.tick_params(axis='y', length=0)  # Hide y-axis tick marks, keep labels
    ax.tick_params(axis='x', length=0)
    
    ax.spines['right'].set_visible(False)  
    ax.spines['top'].set_visible(False)    
    ax.spines['left'].set_color((0, 0, 0, 0.3))  
    ax.spines['bottom'].set_color((0, 0, 0, 0.3))  
    
    plt.savefig("static/images/sqft_histogram.png")
    plt.close()


