#importing required libraries

from urllib.parse import urlparse
from flask import Flask, request, render_template
import numpy as np
import pandas as pd
from sklearn import metrics 
import warnings
import pickle
import joblib
import mysql.connector
warnings.filterwarnings('ignore')
from feature import FeatureExtraction

file = open("random_forest_model.joblib","rb")
gbc = joblib.load('random_forest_model.joblib')
file.close()




# Define your database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Xbhi",
    "database": "phishfinders"
}

app = Flask(__name__)
 

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form["url"]
        urls = url.replace("https://www.", "").replace("http://", "").replace("www.","").replace("https://","")
        print("***********************")
        print(urls)
        m = 0;

        
        try:
            # Connect to the database
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # Get the first letter of the query
            first_letter = urls[0].lower()  # Convert to lowercase
            print(".......................")
            print(first_letter)

            # Construct the column name using backticks
            column_name = f'`{first_letter}`'

            # Search the 'genuine' table for the specified column
            cursor.execute(f"SELECT * FROM genuine WHERE {column_name} = %s", (urls,))
            genuine_results = cursor.fetchall()

            # Search the 'phishing' table for the specified column
            cursor.execute(f"SELECT * FROM phishing WHERE {column_name} = %s", (urls,))
            phishing_results = cursor.fetchall()
            print("++++++++++++++++++")
            print(phishing_results)

            if genuine_results and m == 0:
                    m = 1;
                    # If found in 'genuine' table, return the results as "Genuine"
                    return render_template('index.html', xx=1,  result="Genuine")
            elif (phishing_results):
                return render_template('index.html', xx=0, result="Phishing")
            else:   
                    
                url = request.form["url"]
                obj = FeatureExtraction(url)
                x = np.array(obj.getFeaturesList()).reshape(1,30) 

                y_pred =gbc.predict(x)[0]
                #1 is safe       
                #-1 is unsafe
                y_pro_phishing = gbc.predict_proba(x)[0,0]
                y_pro_non_phishing = gbc.predict_proba(x)[0,1]
                # if(y_pred ==1 ):
                pred = "It is {0:.2f} %s safe to go ".format(y_pro_phishing*100)
                s = round(y_pro_non_phishing,2)


                if s >= 0.5:
                     cursor.execute(f"INSERT INTO genuine ({column_name}) VALUES (%s)", (urls,))
                     conn.commit()  # Commit
                elif s < 0.5:
                     cursor.execute(f"INSERT INTO phishing ({column_name}) VALUES (%s)", (urls,))
                     conn.commit()  # Commit     
                else:
                     print("DEAD WEBSITE PROBABLY");
                
                m = 0;  
                return render_template('index.html',xx =round(y_pro_non_phishing,2),url=url )
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            conn.close()

    return render_template("index.html", xx =-1)


if __name__ == "__main__":
    app.run(debug=True)