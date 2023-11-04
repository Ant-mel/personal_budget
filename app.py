import sys
import os
import streamlit as st
import requests
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import tempfile
import numpy as np

from budget_functions import *

# # Was hoping to put the site online...
# script_directory = os.path.dirname(os.path.abspath(__file__))
# # Add the project root directory to sys.path
# project_root_directory = os.path.join(script_directory, '..')
# sys.path.append(project_root_directory)


st.title('Budget test')

#Categories
daily = ['Groceries', 'Transportation', 'Food', 'Entertainment', 'Culture', 'Subscriptions', 'Health', 'Shopping', 'Herbals', 'Other']
notdaily = ['Holidays', 'Education', 'Rent', 'Investment', 'Donations', 'Utilities']
living = ['Groceries', 'Transportation', 'Food', 'Entertainment', 'Culture', 'Subscriptions', 'Health', 'Shopping', 'Herbals', 'Other' ,'Rent', 'Utilities']
livingholidays = ['Groceries', 'Transportation', 'Food', 'Entertainment', 'Culture', 'Subscriptions', 'Health', 'Shopping', 'Herbals', 'Other' ,'Rent', 'Holidays', 'Utilities']
no_inv_edu = ['Groceries','Food','Holidays','Transportation','Entertainment','Health','Subscriptions','Shopping','Rent','Culture','Herbals','Other','Donations','Utilities']


# file = st.text_input('Location of the data')
file = "raw_data/clevmoney_102423_125727_auto.db"
master = create_master(file)


if st.button("Monthly categorical average"):
    raw_avg, len_of_time = mnth_avg(master)

    fig, ax = plt.subplots()
    norm = plt.Normalize(0.5, 0.75)

    x = np.arange(10)
    y = np.random.rand(10)

    cmap = plt.cm.get_cmap('rainbow')
    colours = cmap(np.linspace(0, 1, len(x)))

    ax.bar(raw_avg['s_cate'], raw_avg[0], color=colours)
    ax.grid(axis = 'y', linestyle='dashed', alpha = 0.3)
    ax.set_xlabel("Categories")
    ax.set_xticklabels(raw_avg['s_cate'], rotation=90)
    ax.set_ylabel('£ value')
    ax.set_title(f"Average monthly spend over {len_of_time} months")

    st.pyplot(fig)

if st.button('Plots by category'):
    all_cats = master.s_cate.value_counts().index.tolist()

    fig, axes = plt.subplot_mosaic([['tl','tr'],['bl', 'bl'],['bt', 'bt']], figsize=(20, 20))

    plot_spnd(subs(master, notdaily), "Not daily spend", 'r', axes['tl'])
    plot_spnd(subs(master, daily), "Daily spend", 'b', axes['tr'])
    plot_spnd(subs(master, living), "Living cost", 'g', axes['bl'])
    plot_spnd(subs(master, no_inv_edu), "No Investment and Edu", 'pink', axes['bt'])

    st.pyplot(fig)


if st.button('Unsure on categories?'):
    st.subheader('Daily')
    st.write('Groceries, Transportation, Food, Entertainment, Culture, Subscriptions, Health, Shopping, Herbals, Other')

    st.subheader('Not Daily')
    st.write('Holidays, Education, Rent, Investment, Donations, Utilities')

    st.subheader("Living")
    st.write('Groceries, Transportation, Food, Entertainment, Culture, Subscriptions, Health, Shopping, Herbals, Other, Rent, Utilities')
