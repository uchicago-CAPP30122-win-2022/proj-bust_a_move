'''
Functions to clean all of the raw datasets and save clean versions of these
'''
from unicodedata import numeric
import requests
import io
import pandas as pd
import numpy as np

#------------MEDIAN INCOME AND POVERTY DATA FROM CENSUS API-----------------------#

def clean_med_pov():
    '''
    Function to call census API and clean census median income and poverty data

    Inputs :
    file (str) : File path median income and poverty data

    Returns : median income and poverty data pandas dataframe
    '''

    call = '''https://api.census.gov/data/timeseries/poverty/saipe?get=SAEMHI_PT,SAEPOVRTALL_PT,NAME&for=county:*&in=state:*&time=2020&key=2a3bf1bd5b110158358335717d5d067b0e377810'''
    
    print("Requesting poverty and income data from API...")

    response = requests.get(call)

    rawData = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
    rawData = rawData.rename(columns= {'[["SAEMHI_PT"':"med_inc","SAEPOVRTALL_PT" : "pov_rate",\
        "NAME":"county","county]":"fips_county"})
    med_inc = rawData.copy()

    cols_to_fix = ["med_inc", "fips_county"]

    for col in cols_to_fix:
        med_inc[col] = med_inc[col].str.replace("[","")
        med_inc[col] = med_inc[col].str.replace("]","")
        med_inc[col] = med_inc[col].str.replace('"',"")

    med_inc = med_inc.replace('null', np.nan)
    med_inc = med_inc.astype({"state": str, "fips_county": str, "med_inc": float}) 

    med_inc["state"] = med_inc['state'].str.zfill(2)
    med_inc['County Code'] = med_inc["state"] + med_inc["fips_county"]

    print("Income and poverty data retrieved!")

    return med_inc

#--------    MOBILITY   ---------------#


# Mobility
def clean_mobility_data(file): 
    """
    Function to clean mobility data

    Inputs :
    file (str) : File path to mobility data

    Returns : mobility data pandas dataframe
    """

    print("Cleaning Google mobility data....")

    mobi = pd.read_csv(file, dtype= {"countyfips": str})
    mobi = mobi.replace(["."], [None])
    mobi[["gps_retail_and_recreation", "gps_grocery_and_pharmacy", "gps_parks"]] = \
                mobi[["gps_retail_and_recreation", "gps_grocery_and_pharmacy", "gps_parks"]].apply(pd.to_numeric)

    cols_to_check = ["date","countyfips","gps_retail_and_recreation", \
        "gps_grocery_and_pharmacy","gps_parks"]
    mobi["countyfips"]= mobi["countyfips"].str.zfill(5)
    mobi["date"] = pd.to_datetime(mobi[["year", "month", "day"]])
    mobi = mobi[cols_to_check]

    print("Google mobility data saving.. in clean folder!")

    return mobi

#+++++++++++++++++++++ RACE/ETHNICITY ++++++++++++++++++++++++++

def clean_race_data(file):
    '''
    Function to clean race data

    Inputs :
    file (str) : File path to race data

    Returns : race data pandas dataframe
    '''

    cols = {'NAME':	'County',
            'B02001_001E': 'total',
            'B02001_001M':	'moe_total',
            'B02001_002E':  'white',
            'B02001_002M':	'moe_white',
            'B02001_003E':	'blk_af_am',
            'B02001_003M':	'moe_blk_af_am',
            'B02001_004E':	"am_indian_alas_nat",
            'B02001_004M':	"moe_am_indian_alas_nat",
            'B02001_005E':	"asian",
            'B02001_005M':	"moe_asian",
            'B02001_006E':	"nat_haw_pac_island",
            'B02001_006M':	"moe_nat_haw_pac_island",
            'B02001_007E':	"other",
            'B02001_007M':	"moe_other",
            'B02001_008E':	"two_or_more",
            'B02001_008M':	"moe_two_or_more",
            'B02001_009E':	"two_more_inc_other",
            'B02001_009M':	"moe_two_more_inc_other",
            'B02001_010E':	"two_more_excl_other_three",
            'B02001_010M':	"moe_two_more_excl_other_three"}

    
    print("Cleaning race distribution data...")

    race = pd.read_csv(file)
    race = race.rename(columns = cols)
    race = race.iloc[1:]
 
    cols_to_check = race.columns[:-3]
    race['is_na'] = race[cols_to_check].isnull().apply(lambda x: all(x), axis=1) 
    race = race[race['is_na']==False]
    race = race.loc[:, ~race.columns.str.startswith('moe')]
    race = race.iloc[:,:-1]

    race.fillna(0)
    race = race.drop('two_more_inc_other',1)
    race = race.drop('two_more_excl_other_three', 1)

    cols_to_numeric = ['total', 'white', 'blk_af_am', 'am_indian_alas_nat', 'asian',
       'nat_haw_pac_island', 'other', 'two_or_more']
    for col in cols_to_numeric:
        race[col] = pd.to_numeric(race[col])

    percs = ['white', 'blk_af_am', 'am_indian_alas_nat', 'asian',
       'nat_haw_pac_island', 'other', 'two_or_more']

    for p in percs:
        race[f'perc_{p}'] = race[p] / race['total']
        race['fips'] = race['GEO_ID'].str[-5:]

    df_unpivoted = race.melt(id_vars=['GEO_ID', 'County','fips'], var_name='race', value_name='perc_total')
    df_unpivoted.head()
    df_race = df_unpivoted[df_unpivoted['race']!= 'total']
    df_race = df_race[df_race['race'].str.contains("perc")]

    print("Race data saved in clean folder!")
    
    return df_race


#++++++++   POPULATION   ++++++++++++++++++++

def clean_pop_data(file):
    '''
    Function to clean census population data

    Inputs :
    file (str) : File path to population data

    Returns : population data pandas dataframe
    '''

    print("Cleaning population data....")

    population = pd.read_csv(file, encoding = "ISO-8859-1", dtype={"STATE" : object, "COUNTY" : object})
    population["STATE"] = population["STATE"].str.zfill(2)
    population["COUNTY"] = population["COUNTY"].str.zfill(3)
    population["COUNTY_FIPS"] = population["STATE"] + population["COUNTY"]

    print("Population data cleaned!")

    return population


#++++++++++ ZILLOW HOUSING +++++++++++++++++++

def housing_pop_inc_pov(zillow, crosswalk, population):
    '''
    Function for merging all of the datasets together into a 
    dataset for the chloropleth map that contains -
    1. county wise housing prices, 2. county wise median income and poverty rates
    3. county wise population. 

    Inputs-

    zillow: (str) path of zillow housing prices -county wise
    crosswalk: (str) path to crosswalk to merge zillow region IDs with county FIPS codes
    population: (str) path to population data

    Returns -
    County level pandas dataframe with housing prices, median income, poverty rate and
    population
    '''

    print("Loading and cleaning all of the required data....")

    zhvi = pd.read_csv(zillow, index_col="RegionID")
    crosswalk = pd.read_csv(crosswalk, encoding = "ISO-8859-1", \
        index_col="CountyRegionID_Zillow", dtype={"FIPS" : object})
    population = clean_pop_data(population)
    med_inc = clean_med_pov()


    years = zhvi.loc[:, "2019-01-31":"2021-12-31":1]

    regions = zhvi.loc[:, "SizeRank":"MunicipalCodeFIPS":1]

    zhvi2 = regions.join(years)

    zhvi2["2019_average"] = zhvi2.loc[:, "2019-01-31":"2019-12-31": 1].mean(axis=1)
    zhvi2["2020_average"] = zhvi2.loc[:, "2020-01-31":"2020-12-31": 1].mean(axis=1)
    zhvi2["2021_average"] = zhvi2.loc[:, "2021-01-31":"2021-12-31": 1].mean(axis=1)
    zhvi2["2020_increase"] = ((zhvi2["2020_average"] - zhvi2["2019_average"])/zhvi2["2019_average"])*100
    zhvi2["2021_increase"] = ((zhvi2["2021_average"] - zhvi2["2020_average"])/zhvi2["2020_average"])*100
    zhvi2["2021_2yr_increase"] = ((zhvi2["2021_average"] - zhvi2["2019_average"])/zhvi2["2019_average"])*100

    zhvi2["text_20"] = " "
    zhvi2["text_21"] = " "
    zhvi2["text_2yrs"] = " "

    zhvi2.dropna()

    # MERGES
    print("Merging housing, income, poverty and population data...")

    zhvi_county = pd.merge(zhvi2, crosswalk, left_index=True, right_index=True)
    zhvi_county["FIPS"] = zhvi_county["FIPS"].str.zfill(5)
    zhvi_county_inc = pd.merge(zhvi_county, med_inc, left_on="FIPS", right_on="County Code")
    zhvi_county_inc_pop = pd.merge(zhvi_county_inc, population, left_on="FIPS", right_on="COUNTY_FIPS")

    # Format text for hovering
    for idx, row in zhvi_county_inc_pop.iterrows():
        zhvi_county_inc_pop.at[idx, 'text_20'] = 'County: ' + row["RegionName"] + \
            '<br>' + 'State: ' + row["State"] + \
            '<br>' + '2019-20 increase: ' + str(round(row["2020_increase"], 3)) + '%' + '<br>' + \
            'Med_Inc: ' + '$' + str(row["med_inc"]) + \
            '<br>' + 'Pop_2019:' + str(row["POPESTIMATE2019"])
    
        zhvi_county_inc_pop.at[idx, 'text_21'] = 'County: ' + row["RegionName"] + \
            '<br>' + 'State: ' + row["State"] + \
            '<br>' + '2020-21 increase: ' + str(round(row["2021_increase"], 3)) + '%' + '<br>' + \
            'Med_Inc: ' +  '$' + str(row["med_inc"]) + \
            '<br>' + 'Pop_2020: ' + str(row["POPESTIMATE2020"])
    
        zhvi_county_inc_pop.at[idx, 'text_2yrs'] = 'County: ' + row["RegionName"] + \
            '<br>' + 'State: ' + row["State"] + \
            '<br>' + '2019-21 increase: ' + str(round(row["2021_2yr_increase"], 3)) + '%' + '<br>' + \
            'Med_Inc: ' + '$' +  str(row["med_inc"]) + \
            '<br>' + 'Pop_2020: ' + str(row["POPESTIMATE2020"])

    median_pov = zhvi_county_inc_pop['pov_rate'].median()
    median_inc = zhvi_county_inc_pop['med_inc'].median()

    zhvi_county_inc_pop['house_pov_ind'] = zhvi_county_inc_pop['2021_2yr_increase'] >= 30 & \
        ((zhvi_county_inc_pop.pov_rate >= median_pov) | (zhvi_county_inc_pop.med_inc <= median_inc))
    
    zhvi_county_inc_pop['opacity'] = zhvi_county_inc_pop['house_pov_ind'].apply(lambda x: 1 if x==True else 0.2)

    cols_to_keep = ['RegionName','State', 'Metro','FIPS',"2021_average","2020_average","2019_average",\
        "2020_increase","2021_increase",'2021_2yr_increase','text_2yrs','text_20',\
            'text_21','med_inc', 'pov_rate','POPESTIMATE2020','opacity']

    zhvi_county_inc_pop = zhvi_county_inc_pop[cols_to_keep]

    zhvi_county_inc_pop['FIPS'] = zhvi_county_inc_pop['FIPS'].apply(str)
    zhvi_county_inc_pop['FIPS'] = zhvi_county_inc_pop["FIPS"].str.zfill(5)

    med_pov = zhvi_county_inc_pop['pov_rate'].median()
    med_inc = zhvi_county_inc_pop['med_inc'].median()   

    zhvi_county_inc_pop['house_pov_ind'] = ((zhvi_county_inc_pop['pov_rate']>= med_pov) \
                                         | (zhvi_county_inc_pop['med_inc']<= med_inc)) \
                                         & (zhvi_county_inc_pop['2021_2yr_increase'] >= 25)
    
    zhvi_county_inc_pop['opacity'] = zhvi_county_inc_pop['house_pov_ind'].apply(lambda x: 1 if x==True else 0.2)

    print("Housing, income and poverty data saved in clean folder!")

    return zhvi_county_inc_pop


#--------------------SAVING CLEAN DATASETS FOR THE APP----------------------#

zillow = "raw/zillow_home_value_index_county.csv"
crosswalk = "raw/CountyCrossWalk_Zillow.csv"
population = "raw/county_population.csv"

housing_inc_pov_data = housing_pop_inc_pov(zillow, crosswalk, population)
housing_inc_pov_data.to_csv("clean/zhvi_county_inc_pop_clean.csv")

race_data = clean_race_data("raw/race_by_county.csv")
race_data.to_csv("clean/race_data_clean.csv")

mobility = clean_mobility_data("raw/google_mobility_county.csv")
mobility.to_csv("clean/google_mobility_county_clean.csv")






