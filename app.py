import sys
import os
import streamlit as st
import requests
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import tempfile
import numpy as np
import streamlit as st


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import json

from budget_functions import *

# # Was hoping to put the site online...
# script_directory = os.path.dirname(os.path.abspath(__file__))
# # Add the project root directory to sys.path
# project_root_directory = os.path.join(script_directory, '..')
# sys.path.append(project_root_directory)


@st.cache_data
def get_latest_clevmoney_file(app='local'):
    folder_name = 'ClevMoney'
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if app == 'local':
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "secrets/creds_v2.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
    else:
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                gcp_installed_secrets = st.secrets['gcp_installed']

                # Convert the secrets to the JSON structure expected by InstalledAppFlow
                credentials_info = {
                    "installed": {
                        "client_id": gcp_installed_secrets['client_id'],
                        "project_id": gcp_installed_secrets['project_id'],
                        "auth_uri": gcp_installed_secrets['auth_uri'],
                        "token_uri": gcp_installed_secrets['token_uri'],
                        "auth_provider_x509_cert_url": gcp_installed_secrets['auth_provider_x509_cert_url'],
                        "client_secret": gcp_installed_secrets['client_secret'],
                        "redirect_uris": gcp_installed_secrets['redirect_uris']
                    }
                }

                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_info, SCOPES
                )
                creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

        # Search for the folder by name
    folder_query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    folder_results = service.files().list(q=folder_query, fields="files(id)").execute()
    folder_id = folder_results['files'][0]['id'] if folder_results['files'] else None

    if not folder_id:
        raise ValueError(f"Folder '{folder_name}' not found")

    # Search for the most recent file in the folder
    file_query = f"'{folder_id}' in parents and trashed=false"
    file_results = service.files().list(q=file_query, orderBy='createdTime desc', pageSize=1, fields="files(id, name)").execute()
    file_id = file_results['files'][0]['id'] if file_results['files'] else None

    if not file_id:
        raise ValueError(f"No files found in folder '{folder_name}'")

    # Retrieve the file content
    request = service.files().get_media(fileId=file_id)
    file_content = io.BytesIO()
    downloader = MediaIoBaseDownload(file_content, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    # Write the content to a local file
    with open("downloaded_file", "wb") as f:
        f.write(file_content.getvalue())

    print("File downloaded successfully.")


st.title('Budget test')

#Categories
daily = ['Groceries', 'Transportation', 'Food', 'Entertainment', 'Culture', 'Subscriptions', 'Health', 'Shopping', 'Herbals', 'Other']
notdaily = ['Holidays', 'Education', 'Rent', 'Investment', 'Donations', 'Utilities']
living = ['Groceries', 'Transportation', 'Food', 'Entertainment', 'Culture', 'Subscriptions', 'Health', 'Shopping', 'Herbals', 'Other' ,'Rent', 'Utilities']
livingholidays = ['Groceries', 'Transportation', 'Food', 'Entertainment', 'Culture', 'Subscriptions', 'Health', 'Shopping', 'Herbals', 'Other' ,'Rent', 'Holidays', 'Utilities']
no_inv_edu = ['Groceries','Food','Holidays','Transportation','Entertainment','Health','Subscriptions','Shopping','Rent','Culture','Herbals','Other','Donations','Utilities']


# file = st.text_input('Location of the data')
get_latest_clevmoney_file(app='streamlit')
file = "downloaded_file"
master = create_master(file)
selected_categories = st.multiselect(label='Select Categories',options=master['s_cate'].unique())
master['week_num'] = master['s_date'].apply(lambda x: x.isocalendar()[:2])
subcate_mask = master['s_cate'].isin(selected_categories)
temp_data = pd.DataFrame(master[subcate_mask].groupby(['week_num', 's_cate'])['s_price'].sum()).reset_index()



if st.button('Weekly spend breakdown'):
    temp_data['week_label'] = temp_data['week_num'].apply(lambda x: f"{x[0]}-{x[1]}")

    # Create a mapping for the week_num to maintain ordinality
    week_mapping = {week: i for i, week in enumerate(temp_data['week_label'].unique())}
    temp_data['week_mapped'] = temp_data['week_label'].map(week_mapping)

    # Pivot the DataFrame
    pivot_df = temp_data.pivot_table(values='s_price', index='week_mapped', columns='s_cate', aggfunc='sum', fill_value=0)

    # Initialize the bottom array
    bottom = np.zeros(len(pivot_df))

    # Plot
    fig, ax = plt.subplots(figsize=(20, 6))  # You can adjust the figure size here
    week_labels = [f'{week}' for week in sorted(week_mapping, key=week_mapping.get)]
    for cate in pivot_df.columns:
        ax.bar(pivot_df.index, pivot_df[cate], bottom=bottom, label=cate)
        bottom += pivot_df[cate].values

    # Set the x-axis labels to the sorted week numbers
    ax.set_xticks(range(len(week_labels)))
    ax.set_xticklabels(week_labels, rotation=45)  # Rotate labels for better readability

    # Labeling
    plt.xlabel('Week Number')
    plt.xticks(rotation=90)

    plt.ylabel('Price ($)')
    plt.title('Stacked Expenses by Category')
    plt.legend(title='Categories')
    plt.tight_layout()

    # Show plot
    st.pyplot(fig)



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
