from pdb import line_prefix
from tkinter import MULTIPLE
import pandas as pd
import sqlite3

def setup(file):
    # creating file path
    sqlfile = file
    # Create a SQL connection to our SQLite database + cursor
    con = sqlite3.connect(sqlfile)
    cur = con.cursor()

    # reading all table names
    table_list = [a for a in cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    # here is your table list
#     print(table_list)

    df = pd.read_sql_query('SELECT s_date, s_time, s_where, s_cate, s_subcate, s_price FROM spendinglist', con)
    df_type = df.astype({'s_date':'datetime64[ns]', 's_time':'datetime64[ns]', 's_where':'string', 's_price':'float', 's_cate':'float', 's_subcate':'float'})
    df_type['s_time'] = df_type['s_time'].dt.strftime('%H:%M:%S')
    #Add year and month columns
    df_type['Month'] = df_type['s_date'].dt.month
    df_type['Year'] = df_type['s_date'].dt.year

    con.close()
    return df_type

def importcats(file):
    # Create a SQL connection to our SQLite database
    con = sqlite3.connect(file)
    # creating cursor
    cur = con.cursor()
    # reading all table names
    table_list = [a for a in cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    # here is your table list
#     print(table_list)

    df = pd.read_sql_query('SELECT * FROM catelist', con)
    con.close()

    dicto = df.set_index('_id')['c_name'].to_dict()
    return dicto

def merge(df, dic):
    # merges the dictionary with the dataframe
    df['s_cate'] = df['s_cate'].replace(dic, regex=True)
    df['s_subcate'] = df['s_subcate'].replace(dic, regex=True)
    df['s_cate'] = df['s_cate'].astype('string')
    return df

def plot_spnd(df, title,color=None, ax=None):
    "Creates a line graph mapping unfiltered spend"
    Mnthly = df.groupby(df['s_date'].dt.to_period('M'))["s_price"].sum()
#     print(Mnthly)

    Mnthly.plot(x='Month', y='s_price', marker='o', color=color, ax=ax)
    if ax != None:
        ax.set_title(title)
        ax.set_xlabel('Date')
        ax.set_ylabel('£ value')
    else:
        pass

def subs(df, cat, isnt=True):
    """subsets for predtermined categories
    Isnt is set to True by default"""
    df2 = df[df['s_cate'].isin(cat) == isnt]
    return df2

def mnth_avg(df):
    '''below is the average I spend on each category over the time I have been budgeting'''
    # Isolates the data we need
    sort = df.groupby(['Year', 'Month', 's_cate'])['s_price'].sum()

    # Creates a YearMonth column for us to index by
    test_df = pd.DataFrame(sort).reset_index()
    test_df['YearMonth'] = test_df['Year'].astype(str) + '-' + test_df['Month'].astype(str)
    test_df['YearMonth'] = pd.to_datetime(test_df['YearMonth'])
    test_df.set_index('YearMonth', inplace=True)

    # Creates a pivot table for accurate averaging
    pivot_table = test_df.pivot_table(index=test_df.index, columns='s_cate', values='s_price')
    pivot_table.fillna(0, inplace=True)
    avg = pd.DataFrame(pivot_table.mean().sort_values(ascending=False)).reset_index()

    len_of_time = df.groupby(['Year', 'Month'])['s_price'].sum().shape[0]
    return avg, len_of_time

def create_master(file_name):
    '''runs the required functions to setup my master budget file'''
    df1 = setup(file_name)
    dic1 = importcats(file_name)
    master = merge(df1, dic1)
    return master
