#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 16:21:35 2026

A streamlit app to find the max values of data output
from coral PAM experiments performed at Mote Marine Laboratory

The data are uploaded as a csv file.
The output may be downloaded as a csv file. 

@author: danfeldheim
"""

# Imports
import pandas as pd
import numpy as np
import streamlit as st
from styles import CSS
import os
from PIL import Image


class Flow_Control():
    """This class makes all of the calls to other classes and methods."""
    
    def __init__(self):
        
        pass
       
    def all_calls(self):
        """This is the main logic workflow. All calls to other functions are here."""
        
        # Show loading message for first-time initialization
        st.write('')
        st.write('')
        st.write('')
     
        # Set up the header, login form, and check user credentials
        # Create Setup instance
        setup = Setup()
        
        # Render the header
        header = setup.header()
        
        # Upload data
        uploader = Load_Data()
        files = uploader.upload()
        
        # Import into dataframe. Calls function that caches the data
        import_data = uploader.import_df(files)
        
        # Find the max 
        max_finder = Find_Max()
        max_dict = max_finder.max(import_data)
        
        # Call download class
        exporter = Export()
        exporter.download_max_values(max_dict)
        
        
class Setup():
    """Class that lays out the app header and sidebar."""
    
    def __init__(self):
        
        pass
    
    def header(self):
        
        # Inject custom CSS from styles.py file
        st.markdown(CSS, unsafe_allow_html=True)
        
        # Draw line across the page
        st.divider()
        
        # Add a logo and title
        col1, col2 = st.columns([1,6])
        
        with col1:
        
            st.image(st.session_state['logo'])
            
        with col2:

            st.write('')
            st.write('')
            st.write('')
            # st.write('')
            
            st.markdown(f"<p style='color: Blue; \
                          font-size: 32px; \
                          margin: 0;'>Coral Health and Disease PAM Data Analyzer</p>",
                          unsafe_allow_html=True
                        )
        st.divider()


class Load_Data():
    """Creates a file uploader and imports data as dataframe."""
    
    def __init__(self):
        
        pass
    
    def upload(self):
        
        col1, col2 = st.columns([1,1])
        
        with col1:
        
            # File uploader that allows multiple files
            uploaded_files = st.file_uploader(
                                              "Choose PAM Data Files", 
                                              type=["csv"],  
                                              accept_multiple_files=True, 
                                              )
            
        return uploaded_files
            
    @staticmethod    
    @st.cache_data
    def import_df(files):
        
        """
        Import a .csv file into a pandas DataFrame.
        - CSV: tries multiple common encodings.
        Returns DataFrame on success, None on failure.
        """
        
        uploaded_data_dict = {}
    
        for file in files:
            
            # Handle all types of CSV files
            if file.name.endswith(".csv"):
                encodings_to_try = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
                for enc in encodings_to_try:
                    try:
                        df = pd.read_csv(file, encoding=enc)
                        uploaded_data_dict[file.name] = df
                        success = True
                        break  
    
                    except UnicodeDecodeError:
                        continue
    
                    except Exception as e:
                        st.error(f"❌ Error reading CSV file {file.name}: {e}")
                        break  
    
                if not success:
                    st.error(f"❌ Unable to read CSV file {file.name}. Please save as UTF-8 CSV.")
    
            else:
                st.error(f"❌ Unsupported file type: {file.name}")
                continue  
    
        return uploaded_data_dict
            
class Find_Max():
    
    def __init__(self):
        
        pass
    
    def max(self, data_dict):
    
        """Find the max value in the columns Y(II)2, Y(NPQ)1, and ETR1."""
        
        search_columns = ['Y(II)2', 'Y(NPQ)1', 'ETR1']
        max_results_dict = {}
        
        if data_dict:
            for filename, df in data_dict.items():
                
                max_results_dict[filename] = {} 
                
                for col in search_columns:
                    maxVal = df[col].max()
                    max_results_dict[filename][col] = maxVal 
                    
        return max_results_dict
    
    
    
class Export():
    
    def __init__(self):
        
        pass
    
    
   
    def download_max_values(self, results_dict):
    
        # Convert nested dict → DataFrame
        df = pd.DataFrame.from_dict(results_dict, orient="index")
        
        # Move filename from index to column
        df.index.name = "filename"
        df.reset_index(inplace=True)
        
        # Rename columns 
        df.rename(columns={
                          "Y(II)2": "Y(II)_max_initial",
                          "Y(NPQ)1": "Y(NPQ)_max_initial",
                          "ETR1": "ETR_max_initial"
                          }, inplace=True)
        
        # Optional: enforce column order
        df = df[[
                "filename",
                "Y(II)_max_initial",
                "Y(NPQ)_max_initial",
                "ETR_max_initial"
               ]]
        
        st.write('')
        st.write('')
        # Write the filename
        st.markdown(f"<p style='color: hotpink; \
              font-size: 24px; \
              margin: 0;'>Max Values</p>",
              unsafe_allow_html=True)
            
        # st.dataframe(
        #             df,
        #             hide_index=True,
        #             use_container_width=False,
        #             column_config={
        #                 "filename": st.column_config.TextColumn(width="large"),
        #                 "Y(II)_max_initial": st.column_config.NumberColumn(width="medium"),
        #                 "Y(NPQ)_max_initial": st.column_config.NumberColumn(width="medium"),
        #                 "ETR_max_initial": st.column_config.NumberColumn(width="medium"),
        #             }
        #         )
        
        st.dataframe(df, hide_index=True, use_container_width=False, width=750)
        
        # Convert to CSV
        csv = df.to_csv(index=False)
        
        # Download button
        st.download_button(
            label="Download max values CSV",
            data=csv,
            file_name="max_values.csv",
            mime="text/csv"
        )
        
                
       
        
        
# Run 
if __name__ == '__main__':
    
    # Get the path relative to the current file (inside Docker container)
    BASE_DIR = os.path.dirname(__file__)
        
    # Use this for cloud
    st.session_state['logo'] = 'mote_logo.png'
    
    # Load image for favicon
    logo_img = Image.open(st.session_state['logo'])
    
    # Use this for local machine
    # if 'logo' not in st.session_state:
    #     st.session_state['logo'] = BASE_DIR + '/mote_logo.png'
        
    # logo_img = BASE_DIR + '/mote_logo.png'
        
    # Page config
    st.set_page_config(layout = "wide", 
                       page_title = 'Mote', 
                       page_icon = logo_img,
                       initial_sidebar_state="auto", 
                       menu_items = None)
    
    
    # Call Flow_Control class that makes all calls to other classes and methods
    obj1 = Flow_Control()
    all_calls = obj1.all_calls()

        