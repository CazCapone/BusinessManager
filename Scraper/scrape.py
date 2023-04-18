from bs4 import BeautifulSoup
import requests
import csv
import pandas as pd
import os
import glob
import re
import logging

# These will be input fields
PALLET_COST = 75
MARGIN = 35
ESTIMATED_SHIPPING_COST = 8
FINAL_FEES = 0.1325

# Const
BASE_URL = "https://www.ebay.com/sch/i.html?"
# Change this path to a static to be uploaded
M_PATH = "./manifests/"

logging.basicConfig(filename='scraper.log', level=logging.DEBUG)

""" MIN/AVE/MAX SALES WILL BE EBAY SALES RESULTS; TOTAL MIN/AVE/MAX * QTY WILL BE EBAY SALES RESULTS MINUS EBAY+SHIPPING FEES TIMES QTY; 
    MIN/AVE/MAX PROFITS WILL BE THE TOTAL OF ALL MIN/AVE/MAX SALES MINUS FEES TIMES QUANTITY MINUS PALLET COST """
temp_data = {
        'QTY': [], 'UPC': [], 'DESCRIPTION': [], 'RETAIL PRICE': [], 'TOTAL RETAIL PRICE': [], 'MIN PALLET COST': [], 'AVE PALLET COST': [], 
        'MIN SALE': [], 'MIN % OF RETAIL': [], 'AVE SALE': [], 'AVE % OF RETAIL': [], 'MAX SALE': [], 'MAX % OF RETAIL': [], 
        'TOTAL MIN * QTY': [], 'TOTAL AVE * QTY': [], 'TOTAL MAX * QTY': [], 'TOTAL MIN': [], 'TOTAL AVE': [], 'TOTAL MAX': [],
        'MIN PROFITS': [], 'MIN P % OF RETAIL': [], 'AVE PROFITS': [], 'AVE P % OF RETAIL': [], 'MAX PROFITS': [], 'MAX P % OF RETAIL': [],  
        'HOW MANY SALES': [], 'LAST SALE DATE': [], 'UPC MIN SALE': [], 'UPC MIN % OF RETAIL': [], 'UPC AVE SALE': [], 'UPC AVE % OF RETAIL': [], 
        'UPC MAX SALE': [], 'UPC MAX % OF RETAIL': [], 'UPC TOTAL MIN * QTY': [], 'UPC TOTAL AVE * QTY': [], 'UPC TOTAL MAX * QTY': [], 
        'UPC MIN PALLET COST': [], 'UPC AVE PALLET COST': [], 'UPC TOTAL MIN': [], 'UPC TOTAL AVE': [], 'UPC TOTAL MAX': [],
        'UPC MIN PROFITS': [], 'UPC MIN P % OF RETAIL': [], 'UPC AVE PROFITS': [], 'UPC AVE P % OF RETAIL': [], 'UPC MAX PROFITS': [], 
        'UPC MAX P % OF RETAIL': [], 'UPC HOW MANY SALES': [], 'UPC LAST SALE DATE': []
        }

searchList = []
upcSearchList = []


def deleteFile():
    """ Step 2: Delete uploaded manifest """

    for folder, subfolders, files in os.walk(M_PATH):   
        for file in files: 
            if file.endswith('.csv'): 
                path = os.path.join(folder, file) 
                logging.info(f'Deleted: {file}')
                os.remove(path)


def cleanManifest():
    """ Step 1: Clean up data in the uploaded manifest; normalize all data column names; copy column data to new data frame """

    manifest_data = pd.concat([pd.read_csv(f) for f in glob.glob(M_PATH+'*.csv')])
    df = pd.DataFrame(manifest_data)

    """ Normalize all possible manifest headings """
    df = df.rename(columns=lambda c: "QTY" if "Qty" in c else c)
    df = df.rename(columns=lambda c: "QTY" if "QTY" in c else c)
    df = df.rename(columns=lambda c: "QTY" if "qty" in c else c)
    df = df.rename(columns=lambda c: "QTY" if "quantity" in c else c)
    df = df.rename(columns=lambda c: "QTY" if "Quantity" in c else c)
    df = df.rename(columns=lambda c: "QTY" if "QUANTITY" in c else c)
    df = df.rename(columns=lambda c: "UPC" if "upc" in c else c)
    df = df.rename(columns=lambda c: "UPC" if "Upc" in c else c)
    df = df.rename(columns=lambda c: "UPC" if "UPC" in c else c)
    df = df.rename(columns=lambda c: "DESCRIPTION" if "DESCRIPTION" in c else c)
    df = df.rename(columns=lambda c: "DESCRIPTION" if "Description" in c else c)
    df = df.rename(columns=lambda c: "DESCRIPTION" if "description" in c else c)

    """ May need to add more Retail Options For now instruct to remove Total columns from manifest """
    df = df.rename(columns=lambda c: "RETAIL PRICE" if "Retail Price" in c else c)
    df = df.rename(columns=lambda c: "RETAIL PRICE" if "Unit Retail" in c else c)
    
    df = df[df.DESCRIPTION != " "]
    df = df[df.UPC != " "]
    df = df[df.QTY != " "]

    columns = list(df.columns.values)

    if "QTY" in columns:
        for i in df["QTY"]:
            temp_data["QTY"].append(i)
    if "UPC" in columns:
        for i in df["UPC"]:
            temp_data["UPC"].append(i)
    if "DESCRIPTION" in columns:
        for i in df["DESCRIPTION"]:
            temp_data["DESCRIPTION"].append(i)
    if "RETAIL PRICE" in columns:
        for i in df["RETAIL PRICE"]:
            temp_data["RETAIL PRICE"].append(i)

    deleteFile()
    return temp_data, df


def displayDataFrame(df):
        """ Displays DataFrame """
        print("*********DataFrame**********")
        print(df)
        print("*********DataFrame**********")


def calculateSales(max_count, sales, i):
    """ This function calculates sales data including average, low, and high sales prices """

    count = 0
    subtotal = 0
    sales_list = []

    for sale in sales[1:max_count]:
        logging.debug(f'Calculated Sale: {sale}')
        try:
            this_sale = float(re.sub('[^0-9.]','', (sale.getText()[1:])))
            sales_list.append(this_sale)
            subtotal += this_sale
            count += 1
        except:
            logging.error(f'Error Calculating sale: {sale}')

    logging.debug(f'Count: {count} Subtotal: {subtotal} Sales: {sales_list}')
    
    if count > 0:
        try:
            ave_sales = subtotal/count
            sales_high = max(sales_list)
            sales_low = min(sales_list)
            
            total_min_sale = sales_low - (((sales_low * FINAL_FEES) + .30) + ESTIMATED_SHIPPING_COST)
            total_ave_sale = ave_sales - (((ave_sales * FINAL_FEES) + .30) + ESTIMATED_SHIPPING_COST)
            total_max_sale = sales_high - (((sales_high * FINAL_FEES) + .30) + ESTIMATED_SHIPPING_COST)
            logging.debug(f'Total Sales Min-Ave-Max: {total_min_sale} {total_ave_sale} {total_max_sale}')

            """ Calculate the ave sales minus fees and shipping times qty """
            qty = cleaned_dict["QTY"]
            retail = cleaned_dict["RETAIL PRICE"]
            logging.debug(f'Qty: {qty} | Retail Price: {retail}')

            min_perc = sales_low / retail[i]
            max_perc = sales_high / retail[i]
            ave_perc = ave_sales / retail[i]
            t_min_sale = qty[i] * round(total_min_sale, 2)
            t_ave_sale = qty[i] * round(total_ave_sale, 2)
            t_max_sale = qty[i] * round(total_max_sale, 2)
        
            return ave_sales, sales_low, sales_high, min_perc, ave_perc, max_perc, t_min_sale, t_ave_sale, t_max_sale
        except:
            logging.error(f'Error calculating sales high, low, average.')


def scrapePrices(searchList):
    """ This scrapes ebay sales prices using the urls in the searchList """

    for url in searchList:
        """ Scrapes and stores (sales var) ebay listings for Sold items; Counts total sales"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            sales = soup.find_all(name="span", class_="s-item__price")
            logging.debug(f'Desc Sales Prices: {sales}')
            max_count = (len(sales))
            logging.debug(f'Desc Max Sales Count: {max_count}')
            dates = soup.find(name="span", class_="POSITIVE")
            date = dates.getText()
            logging.debug(f'Desc Last Sale Date: {date}')
            i = searchList.index(url)
        except:
            logging.error(f'Error scraping ebay data.')

        """ eBay adds one $20.00 sale in the site so all max counts must be counted with -1 """ 
        try:
            cleaned_dict["HOW MANY SALES"].append(max_count - 1)
            cleaned_dict['LAST SALE DATE'].append(date)
        except:
            logging.error(f'Error adding sales count to dict.')

        if max_count > 1:
            i = searchList.index(url)
            if max_count < 6:
                ave_sales, sales_low, sales_high, min_perc, ave_perc, max_perc, t_min_sale, t_ave_sale, t_max_sale = calculateSales(max_count, sales, i)
            elif max_count >= 6:
                ave_sales, sales_low, sales_high, min_perc, ave_perc, max_perc, t_min_sale, t_ave_sale, t_max_sale = calculateSales(6, sales, i)
            logging.debug(f'Ave Sales: {ave_sales} | Low Sales: {sales_low} | High Sales: {sales_high}')
        else:
            ave_sales, sales_low, sales_high = 0, 0, 0
            logging.debug(f'No Sales: Ave Sales: {ave_sales} | Low Sales: {sales_low} | High Sales: {sales_high}')
        
        if ave_sales > 0:
            try: 
                """ Min, Ave, Max sales and %s """
                cleaned_dict["MIN SALE"].append(round(sales_low, 2))
                cleaned_dict["MIN % OF RETAIL"].append(round(min_perc, 2))
                cleaned_dict["MAX SALE"].append(round(sales_high, 2))
                cleaned_dict["MAX % OF RETAIL"].append(round(max_perc, 2))
                cleaned_dict["AVE SALE"].append(round(ave_sales, 2))
                cleaned_dict["AVE % OF RETAIL"].append(round(ave_perc, 2))
                """ Min, Ave, Max sales minus fees, multiplied by qty """
                cleaned_dict["TOTAL MIN * QTY"].append(round(t_min_sale, 2))
                cleaned_dict["TOTAL AVE * QTY"].append(round(t_ave_sale, 2))
                cleaned_dict["TOTAL MAX * QTY"].append(round(t_max_sale, 2))                    
                logging.debug(f'Min %: {min_perc} | Max %: {max_perc} | Ave %: {ave_perc} | Total Sale Min-Ave-Max: {t_min_sale}-{t_ave_sale}-{t_max_sale}')
            except:
                logging.error(f'Error updating sales data.')
        else:
            try:
                cleaned_dict["MIN SALE"].append(0)
                cleaned_dict["MAX SALE"].append(0)
                cleaned_dict["AVE SALE"].append(0)
                cleaned_dict["MIN % OF RETAIL"].append(0)
                cleaned_dict["MAX % OF RETAIL"].append(0)
                cleaned_dict["AVE % OF RETAIL"].append(0)
                cleaned_dict["TOTAL MIN * QTY"].append(0)
                cleaned_dict["TOTAL AVE * QTY"].append(0)
                cleaned_dict["TOTAL MAX * QTY"].append(0) 
            except:
                logging.error(f'Error updating zero sales data.')


def scrapeUPCPrices(upcSearchList):
    """ This scrapes ebay sales prices using the urls in the upcSearchList """

    for url in upcSearchList:
        """ Scrapes and stores (sales var) ebay listings for Sold items; Counts total sales"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            sales = soup.find_all(name="span", class_="s-item__price")
            logging.debug(f'UPC Sales Prices: {sales}')
            max_count = (len(sales))
            logging.debug(f'UPC Max Sales Count: {max_count}')
            dates = soup.find(name="span", class_="POSITIVE")
            date = dates.getText()
            logging.debug(f'UPC Last Sale Date: {date}')
            i = upcSearchList.index(url)
        except:
            logging.error(f'Error scraping ebay data.')

        """ #eBay adds one $20.00 sale in the site so all max counts must be counted with -1 """ 
        try:
            cleaned_dict["UPC HOW MANY SALES"].append(max_count - 1)
            cleaned_dict['UPC LAST SALE DATE'].append(date)
        except:
            logging.error(f'Error adding sales count to dict.')

        if max_count > 1:
            if max_count < 6:
                ave_sales, sales_low, sales_high, min_perc, ave_perc, max_perc, t_min_sale, t_ave_sale, t_max_sale = calculateSales(max_count, sales, i)
            elif max_count >= 6:
                ave_sales, sales_low, sales_high, min_perc, ave_perc, max_perc, t_min_sale, t_ave_sale, t_max_sale = calculateSales(6, sales, i)
            logging.debug(f'Ave Sales: {ave_sales} | Low Sales: {sales_low} | High Sales: {sales_high}')
        else:
            ave_sales, sales_low, sales_high = 0, 0, 0
            logging.debug(f'No Sales: Ave Sales: {ave_sales} | Low Sales: {sales_low} | High Sales: {sales_high}')

        if ave_sales > 0:
            try:
                cleaned_dict["UPC MIN SALE"].append(round(sales_low, 2))
                cleaned_dict["UPC MIN % OF RETAIL"].append(round(min_perc, 2))
                cleaned_dict["UPC MAX SALE"].append(round(sales_high, 2))
                cleaned_dict["UPC MAX % OF RETAIL"].append(round(max_perc, 2))
                cleaned_dict["UPC AVE SALE"].append(round(ave_sales, 2))
                cleaned_dict["UPC AVE % OF RETAIL"].append(round(ave_perc, 2))
                """ Min, Ave, Max sales minus fees, multiplied by qty """
                cleaned_dict["UPC TOTAL MIN * QTY"].append(round(t_min_sale, 2))
                cleaned_dict["UPC TOTAL AVE * QTY"].append(round(t_ave_sale, 2))
                cleaned_dict["UPC TOTAL MAX * QTY"].append(round(t_max_sale, 2))                    
                logging.debug(f'Min %: {min_perc} | Max %: {max_perc} | Ave %: {ave_perc} | Total Sale Min-Ave-Max: {t_min_sale}-{t_ave_sale}-{t_max_sale}')
            except:
                logging.error(f'Error updating sales data.')
        else:
            try:
                cleaned_dict["UPC MIN SALE"].append(0)
                cleaned_dict["UPC MAX SALE"].append(0)
                cleaned_dict["UPC AVE SALE"].append(0)
                cleaned_dict["UPC TOTAL AVE SALE"].append(0)
                cleaned_dict["UPC MIN % OF RETAIL"].append(0)
                cleaned_dict["UPC MAX % OF RETAIL"].append(0)
                cleaned_dict["UPC AVE % OF RETAIL"].append(0)
                cleaned_dict["UPC TOTAL AVE % OF RETAIL"].append(0)
                cleaned_dict["UPC TOTAL * QTY"].append(0) 
            except:
                logging.error(f'Error updating zero sales data.') 


def createUPCSearchList(upc):
    """ Takes a UPC from the cleaned_dict and creates a product string url; places the url into a list; then calls the scrapePrices method """

    try:
        logging.info(f"{BASE_URL}_nkw={upc}&_sacat=0&LH_Sold=1")
        upcSearchList.append(f"{BASE_URL}_nkw={upc}&_sacat=0&LH_Sold=1")
    except:
        logging.error(f'Error creating UPC search with {upc}')


def createSearchList(description):
    """ Takes a description name from the cleaned_dict and creates a product string url; places the url into a list; then calls the scrapePrices method """

    if " " in description and len(description) > 1:
        try:
            f_description = re.sub('[^0-9a-zA-Z. "]','', description)
            product = f_description[0:65]
            product_string = product.replace(" ", "+")
            logging.info(f"{product}: {BASE_URL}_nkw={product_string}&_sacat=0&LH_Sold=1")
            searchList.append(f"{BASE_URL}_nkw={product_string}&_sacat=0&LH_Sold=1")
        except:
            logging.error(f'Error creating description search with {description}')


def startSearches(cleaned_dict):
    """ Used to start the search process """

    if "UPC" in cleaned_dict:
        logging.debug("UPC Search Started")
    for i in cleaned_dict['UPC']:
        if isinstance(i, int):
            logging.debug(f'UPC: {i}')
            createUPCSearchList(i)
        else:
            logging.debug(f'No UPC Found')
    if len(upcSearchList) > 0:     
        scrapeUPCPrices(upcSearchList)
        logging.debug(f'UPC Search List: {upcSearchList}')
    else:
        logging.debug('UPC Search List is empty!')

    if "DESCRIPTION" in cleaned_dict:
        for i in cleaned_dict['DESCRIPTION']:
            logging.debug("Description Search Started")
            createSearchList(i)
        if len(searchList) > 0:     
            scrapePrices(searchList)
            logging.debug(f'Search List: {searchList}')
        else:
            logging.debug('Search List is empty!')

    logging.debug("All Searches Have Completed")


def calculateProfits(data):
    """ Finishes final calculations; Profits """

    low, ave, high, retail = 0, 0, 0, 0
    min_prof, ave_prof, max_prof = 0, 0, 0
    ulow, uave, uhigh, uretail = 0, 0, 0, 0
    umin_prof, uave_prof, umax_prof = 0, 0, 0

    for d in data['TOTAL MIN * QTY']:
        low += d
    min_prof = low - PALLET_COST
    min_pallet = low - (low * (MARGIN/100))

    data['TOTAL MIN'].append(round(low, 2))
    data['MIN PALLET COST'].append(round(min_pallet, 2))
    data['MIN PROFITS'].append(round(min_prof, 2))

    for d in data['TOTAL AVE * QTY']:
        ave += d
    ave_prof = ave - PALLET_COST
    ave_pallet = ave - (ave * (MARGIN/100))
    
    data['TOTAL AVE'].append(round(ave, 2))
    data['AVE PALLET COST'].append(round(ave_pallet, 2))
    data['AVE PROFITS'].append(round(ave_prof, 2))

    for d in data['TOTAL MAX * QTY']:
        high += d
    max_prof = high - PALLET_COST
    
    data['TOTAL MAX'].append(round(high, 2))
    data['MAX PROFITS'].append(round(max_prof, 2))

    for d in data['RETAIL PRICE']:
        retail += d
    data['TOTAL RETAIL PRICE'].append(round(retail, 2))

    lpor = int(round((low / retail), 2) * 100)
    apor = int(round((ave / retail), 2) * 100)
    hpor = int(round((high / retail), 2) * 100)

    data['MIN P % OF RETAIL'].append(f'{lpor}%')
    data['AVE P % OF RETAIL'].append(f'{apor}%')
    data['MAX P % OF RETAIL'].append(f'{hpor}%')

    for d in data['UPC TOTAL MIN * QTY']:
        ulow += d
    umin_prof = ulow - PALLET_COST
    umin_pallet = ulow - (ulow * (MARGIN/100))
    
    data['UPC TOTAL MIN'].append(round(ulow, 2))
    data['UPC MIN PALLET COST'].append(round(umin_pallet, 2))
    data['UPC MIN PROFITS'].append(round(umin_prof, 2))

    for d in data['UPC TOTAL AVE * QTY']:
        uave += d
    uave_prof = uave - PALLET_COST
    uave_pallet = uave - (uave * (MARGIN/100))

    data['UPC TOTAL AVE'].append(round(uave, 2))
    data['UPC AVE PALLET COST'].append(round(uave_pallet, 2))
    data['UPC AVE PROFITS'].append(round(uave_prof, 2))

    for d in data['UPC TOTAL MAX * QTY']:
        uhigh += d
    umax_prof = uhigh - PALLET_COST
    
    data['UPC TOTAL MAX'].append(round(uhigh, 2))
    data['UPC MAX PROFITS'].append(round(umax_prof, 2))

    ulpor = int(round((ulow / retail), 2) * 100)
    uapor = int(round((uave / retail), 2) * 100)
    uhpor = int(round((uhigh / retail), 2) * 100)

    data['UPC MIN P % OF RETAIL'].append(f'{ulpor}%')
    data['UPC AVE P % OF RETAIL'].append(f'{uapor}%')
    data['UPC MAX P % OF RETAIL'].append(f'{uhpor}%')


##################################################
# Called after file upload returns a dictionary
# First Clean manifest file
cleaned_dict, df = cleanManifest()
#print("Step 1: Clean data: ", cleaned_dict)
displayDataFrame(df)
startSearches(cleaned_dict)
calculateProfits(cleaned_dict)

print(cleaned_dict)