# Project: Cloud_Assets, Author: Julian Baltzer, Datum: 09.09.2022
from ast import Pass
import shutil
import os
import pandas as pd
import glob
import datetime
import mysql.connector
import sys
import ntpath
import time
from sqlalchemy import create_engine
from uuid import uuid4
import random

db = mysql.connector.connect(
    host='localhost',
    database='queue',
    user='root',
    password='Gu6dQVQbMXFsPQQ7!',
    port=3306
)

def get_set_tags(tags):
    cursor.execute("Select * from tags where t_name = {}".format(tags)) 
    row = list(cursor.fetchall())
    if row == None:
        cursor.execute("Insert into tags (tag_ID,t_name) VALUES ({},{})".format(random.getrandbits(32),tags))
    cursor.execute("Select t_id from tags where t_name = {}".format(tags))
    id = list(cursor.fetchall())
    return id   

def fill_tag_to_asset(q_id, tag_id, tag_value):
    cursor.execute("Insert into tags_to_asset(tag_id,t_id,a_id,t_value) VALUES ({}, {}, {})".format(random.getrandbits(32),tag_id[0][0],q_id[0][0],tag_value))
    
    
cursor  = db.cursor()
check = 0
output_information = 0 # Auf 1 setzten, wenn keine Meldungen mehr ausgegeben werden sollen

source = "/home/opc/Project/Source/"
destination = "/home/opc/Project/arbeitsverzeichnis/"
errorverzeichnis = "/home/opc/Project/error/"
done = "/home/opc/Project/Output/"


if output_information == 0:
    print("Checkpoint 1")


if len(os.listdir('/home/opc/Project/Source') ) == 0:
    print("Keine Datei vorhanden")
    time.sleep(1)
    check = 1
else:    
    allfiles = os.listdir(source)
    check = 0
if check == 0:
    # Datein in Arbeitsverzeichnis verschieben
    for f in allfiles:
        shutil.move(source+ f, destination + f)
        
    if output_information == 0:
        print("Checkpoint 2")    
        
   
    path  = "/home/opc/Project/arbeitsverzeichnis"
    filenames  = glob.glob(path + "/*.csv.gz")
    
    if output_information == 0:
        print("Checkpoint 3")
        print(filenames)
        
    for filename in filenames:
        try:
            if output_information == 0:
                print("Checkpoint 4")
            dataframe = pd.read_csv(filename, sep=',',low_memory=False,compression='gzip')
            dataframe["q_status"] = 0
            now = datetime.datetime.now()
            dataframe["dbindate"] = now.strftime("%Y-%m-%d %H:%M:%S")
            dataframe["dbinuser"] = "jbaltzer"
            dataframe["dbupdateuser"] = "jbaltzer"
            dataframe["q_message"] = "tests"
            dataframe["dbupdate"] = now.strftime("%Y-%m-%d %H:%M:%S")
            dataframe["queue_status"] = "0"
            
            dataframe.drop(['lineItem/referenceNo','lineItem/tenantId', 'product/compartmentId', 'product/region', 'product/availabilityDomain',
                            'usage/billedQuantityOverage', 'cost/subscriptionId', 'cost/unitPriceOverage', 'cost/myCostOverage',
                            'cost/overageFlag', 'lineItem/isCorrection', 'lineItem/backreferenceNo'], axis='columns', inplace=True)
            
            tags_df = dataframe.filter(regex=r'^tag')

            print("Checkpoint 4.1")
            
            print("Checkpoint 4.2")
            if dataframe.empty:
                        print("Keine Datensätze zu verarbeiten")
                        break 
            
            dataframe = dataframe[dataframe.columns.drop(list(dataframe.filter(regex=r'^tag')))]
            dataframe = dataframe.where((pd.notnull(dataframe)), 0.0)
            rows = dataframe.values.tolist()
            if output_information == 0:
                print("Checkpoint 5")
            
            for index, rows in dataframe.iterrows():
                if output_information == 0:
                    print("Checkpoint 6")
                try: 
                    query = "INSERT IGNORE INTO queue VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
                    cursor.execute(query,(rows["q_status"],
                                        rows["dbindate"],
                                        rows["dbinuser"],
                                        rows["dbupdateuser"],
                                        rows["q_message"],
                                        rows["dbupdate"],
                                        rows["queue_status"],
                                        rows["lineItem/intervalUsageStart"],
                                        rows["lineItem/intervalUsageEnd"],
                                        rows["product/service"],
                                        rows["product/compartmentName"],
                                        rows["product/resourceId"],
                                        rows["usage/billedQuantity"],
                                        rows["cost/productSku"],
                                        rows["product/Description"],
                                        rows["cost/unitPrice"],
                                        rows["cost/myCost"],
                                        rows["cost/currencyCode"],
                                        rows["cost/billingUnitReadable"],
                                        rows["cost/skuUnitDescription"]))
                    db.commit()
                    timetest = rows["lineItem/intervalUsageStart"] 
                    query_new  = "Select q_id from queue where 'lineItem/intervalUsageStart' = %s AND 'product/resourceId' = %s;"
                    #2022-02-06 20:00:00 = 2022-02-06T20:00Z
                    print(timetest)
                    cursor.execute(query_new,(timetest,rows["product/resourceId"]))
                    q_id = list(cursor.fetchall())
                    print(timetest)
                    print(q_id)
                    counter = q_id[0][0]
                    for column in tags_df.columns:
                        id = get_set_tags(column)
                        for values in tags_df.columns:
                            fill_tag_to_asset(q_id,id,tags_df[values][counter])
                except:
                    raise

            if output_information == 0:
                print("Checkpoint 6.1")
            tests  = ntpath.basename(filename)
            if output_information == 0:
                print("Checkpoint 6.2")
            now = datetime.datetime.now()
            shutil.move(filename, done + now.strftime("%Y_%m_%d %H_%M_%S") + tests)  
            if output_information == 0:
                print("Checkpoint 7")
            db.commit()
        except Exception as e:
            print(repr(e))
            now = datetime.datetime.now()
            new_name = now.strftime("%Y_%m_%d %H_%M_%S") + " " + ntpath.basename(filename) 
            shutil.move(filename, errorverzeichnis+ new_name)
            file = open("errors.txt" ,"w")
            file.write("Error in" + filename + "\n")
            file.close()
            pass
            

