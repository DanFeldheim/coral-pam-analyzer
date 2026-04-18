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
import re
from collections import defaultdict


class Flow_Control():
    """This class makes all of the calls to other classes and methods."""
    
    def __init__(self):
        
        # self.search_columns_A = [
        #                         'Y(II)1', 'Y(II)2', 'Y(II)3', 'Y(II)4', 'Y(II)5',
        #                         'ETR1', 'ETR2', 'ETR3', 'ETR4', 'ETR5',
        #                         ]
        
        # self.search_columns_B = ['Y(NPQ)1', 'Y(NPQ)2', 'Y(NPQ)3', 'Y(NPQ)4', 'Y(NPQ)5']
        
        self.search_columns_A = ['Y(II)', 'ETR']
        
        self.search_columns_B = ['Y(NPQ)']
       
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
        
        tab1, tab2 = setup.tabs()
        
        with tab1:
        
            # Upload data
            uploader = Load_Data()
            data_files, output_file = uploader.upload()
            
            # Import data into dataframe. Calls function that caches the data
            data_df = uploader.import_data(data_files)
            
            # Import target output file into dataframe
            output_df = uploader.upload_output(output_file)
            
            if data_df and output_file:
                
                # Drop rows with all columns empty
                output_df = output_df.dropna(how='all')
                
                # Find the max 
                max_finder = Find_Max()
                max_dict = max_finder.get_max_par_values(data_df, self.search_columns_A, self.search_columns_B)
                
                # Test for all max values in same row for Y(II) and Y(NPQ)
                # max_test = max_finder.max_check(data_df, max_dict)
                
                # Call download class
                exporter = Export()
                final_results_dict = exporter.arrange_by_genotype(output_df, max_dict)
                final_results_df = exporter.add_to_output(final_results_dict, output_df)
                # st.write(final_results_df)
                
                exporter.download_data(final_results_df)
                
        with tab2: 
            
            About().about_tab()
                
        
        
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
            st.write('')
            
            st.markdown(f"<p style='color: Blue; \
                          font-size: 32px; \
                          margin: 0;'>Coral Health and Disease PAM Data Organizer</p>",
                          unsafe_allow_html=True
                        )
        st.divider()
        
    def tabs(self):
        """Styles and creates the tab bar."""
        
        # Style the tabs
        st.markdown("""
                    <style>
                    /* target the tab-list inside the Streamlit tab wrapper */
                    .stTabs [data-baseweb="tab-list"] button[role="tab"][aria-selected="true"]{
                        font-weight: 700 !important;
                        color: #1E90FF !important;
                        border-bottom: 3px solid #1E90FF !important;
                        background-color: #f0f2f6 !important;
                        border-radius: 8px 8px 0 0 !important;
                    }
                
                    .stTabs [data-baseweb="tab-list"] button[role="tab"][aria-selected="false"]{
                        color: gray !important;
                        background: transparent !important;
                    }
                
                    .stTabs [data-baseweb="tab-list"] button[role="tab"]{
                        padding: 8px 14px !important;
                        transition: transform .12s ease, color .12s ease !important;
                    }
                    .stTabs [data-baseweb="tab-list"] button[role="tab"]:hover{
                        transform: scale(1.03) !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
        st.markdown("""
                    <style>
                    /* Tab text (normal and active) */
                    .stTabs [data-baseweb="tab-list"] button[role="tab"] > div {
                        font-size: 18px !important;  /* increase font size */
                        font-weight: 600 !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
    
        # Tabs
        tab1, tab2= st.tabs(["PAM", "How To"])
        
        return tab1, tab2


class Load_Data():
    """Creates a file uploader and imports data as dataframe."""
    
    def __init__(self):
        
        pass
    
    def upload(self):
        
        col1, col2, dummy = st.columns([1,1, 1])
        st.write('')
        st.write('')
        
        with col1:
            
            # File uploader 
            data_file = st.file_uploader(
                                         "Choose PAM Data Files", 
                                         type=["csv"],  
                                         accept_multiple_files=True, 
                                        )
            
        with col2:
            
            # Upload the output where all resuls will end up
            output_file = st.file_uploader(
                                           "Choose Output File", 
                                            type=["csv"],  
                                            accept_multiple_files=False, 
                                          )
            
        return data_file, output_file
            
    @staticmethod    
    @st.cache_data
    def import_data(data_files):
        
        """
        Import a .csv file into a pandas DataFrame.
        - CSV: tries multiple common encodings.
        Returns DataFrame on success, None on failure.
        """
        
        uploaded_data_dict = {}
        
        if not data_files:
            return None
        
        for file in data_files:
       
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
    
    @staticmethod    
    @st.cache_data
    def upload_output(output_file):
        
        if not output_file:
            return None
       
        # Handle all types of CSV files
        if output_file.name.endswith(".csv"):
            encodings_to_try = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
            for enc in encodings_to_try:
                try:
                    df = pd.read_csv(output_file, encoding=enc)
                    # uploaded_output_dict[output_file.name] = df
                    success = True
                    break  

                except UnicodeDecodeError:
                    continue

                except Exception as e:
                    st.error(f"❌ Error reading CSV file {output_file.name}: {e}")
                    break  

            if not success:
                st.error(f"❌ Unable to read CSV file {output_file.name}. Please save as UTF-8 CSV.")

        else:
            st.error(f"❌ Unsupported file type: {output_file.name}")
              

        return df   
    
   
            
class Find_Max():
    
    def __init__(self):
        
        pass
    
    def get_max_par_values(self, data_dict, search_columns_A, search_columns_B):
    
        """Find the max value in the columns Y(II), Y(NPQ), and ETR."""
        
        max_results_dict = {}
        
        if data_dict:
            
            for filename, df in data_dict.items():
                
                max_results_dict[filename] = {}
                
                for target in search_columns_A:
                    
                    A_matching_cols = [c for c in df.columns if c.startswith(target)]
    
                    if A_matching_cols:
                        
                        for col in A_matching_cols:
                            max_results_dict[filename][col] = df[col].max()
                    
                    else:
                        max_results_dict[filename][target] = None
                        
                for target in search_columns_B:
                    
                    B_matching_cols = [c for c in df.columns if c.startswith(target)]
                    
                    if B_matching_cols:
                        
                        for col in B_matching_cols:
                            
                            matches = df.loc[df["PAR"] == 1076, col]
    
                            if not matches.empty:
                                max_results_dict[filename][col] = matches.iloc[0]
                            else:
                                max_results_dict[filename][col] = None
                    
                    else:
                        
                        max_results_dict[filename][target] = None
        
        return max_results_dict
    
    def max_check(self, data_dict, max_results_dict):
        
        check_list = ["Y(II)", "Y(NPQ)"]
        
        for check in check_list:
        
            for filename, df in data_dict.items():
                
                max_calculated = []
                max_row = []
                
                # Subset the raw data df by check_list column header
                subset_df = df.loc[:, df.columns.str.contains(check, regex = False)]
                # st.write("subset_df: ", subset_df)
    
                # Get row based on the first calculated Ymax value
                # Get the first max value from the max_results_dict
                target_value = next((v for k, v in max_results_dict[filename].items() if check in k), None)
                # st.write("target_value: ", target_value)
                
                # Get the first column of subset_df (returns a series)
                first_col = subset_df.iloc[:, 0]
                
                # Create a boolean mask to check in the next line (returns true/false for every row index)
                row_mask = np.isclose(first_col, target_value)
                
                # A match is where the mask is true (returns the entire row of subset_df)
                matches = subset_df.loc[row_mask]
                # st.write(matches)
                
                # Send to list
                raw_row_values = matches.iloc[0].tolist()
                # st.write("Raw values: ", raw_row_values)
         
                calc_max_vals = [value for key, value in max_results_dict[filename].items() if check in key]
                # st.write("calc vals: ", calc_max_vals)
                
                match = np.allclose(raw_row_values, calc_max_vals)
                
                if not match:
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        st.warning(f"Warning! The {check} max values were not located in the same row for {filename}.")
                
            
class Export():
    
    def __init__(self):
        
        pass
    
    def arrange_by_genotype(self, output_file, max_dict):
        
        col1, col2 = st.columns([1,2])
        
        # Check output file dataframe
        if output_file is None or output_file.empty:
            
            with col1:
                st.error('Target output file is missing or empty.')
                
            return None
        
        # Check dictionary itself
        if not max_dict:
            
            with col1:
                st.error("PAM data dictionary is empty or missing.")
            return None
                
        final_results_dict = defaultdict(dict)
        search_substrings = ["Y(II)", "Y(NPQ)", "ETR"]
        
        for filename, results_dict in max_dict.items():
            
            if not results_dict:
                
                with col1:
                    st.error(f"PAM data are missing or empty for file {filename}")
                continue
               
            for colname, val in results_dict.items():
                
                for substring in search_substrings:
                    
                    if substring in colname:
                        
                        genotype = re.split(r"[-_]", colname)[-1]
                        
                        if substring in final_results_dict[genotype]:
                            
                            prev_file = final_results_dict[genotype].get("source", "unknown")
            
                            with col1:
                                st.warning(
                                            f"Duplicate entry detected for genotype '{genotype}' "
                                            f"and metric '{substring}'. First seen in '{prev_file}', "
                                            f"encountered again in '{filename}'. Overwriting previous value."
                                          )
                        
                        final_results_dict[genotype][substring] = val
                        final_results_dict[genotype]["source"] = filename
                            
            return final_results_dict            
                            
    def add_to_output(self, final_results_dict, output_df):  

        col1, col2 = st.columns([1, 2])
    
        # Check dataframe
        if output_df is None or output_df.empty:
            with col1:
                st.error("Output dataframe is missing or empty.")
            return None
        
        # Check dictionary
        if not final_results_dict:
            with col1:
                st.error("Final results dictionary is missing or empty.")
            return None
        
        # Required output columns
        required_columns = [
                            "Genotype",
                            "Y(II) max initial",
                            "Y(NPQ) max initial",
                            "ETR max initial"
                           ]
        
        missing_columns = [col for col in required_columns if col not in output_df.columns]
        
        if missing_columns:
            with col1:
                st.error(
                         "Output dataframe is missing required columns: "
                         + ", ".join(missing_columns)
                        )
            return None
        
        # Work on a copy
        output_df = output_df.copy()
        
        # Optional cleanup in case Genotype values have spaces
        output_df["Genotype"] = output_df["Genotype"].astype(str).str.strip()
        
        # Fill columns from final_results_dict
        output_df["Y(II) max initial"] = output_df["Genotype"].map(
                                                                    lambda g: final_results_dict.get(g, {}).get("Y(II)")
                                                                  )
        
        output_df["Y(NPQ) max initial"] = output_df["Genotype"].map(
                                                                    lambda g: final_results_dict.get(g, {}).get("Y(NPQ)")
                                                                   )
        
        output_df["ETR max initial"] = output_df["Genotype"].map(
                                                                 lambda g: final_results_dict.get(g, {}).get("ETR")
                                                                )
        
    
        return output_df         
                        
    def download_data(self, final_results_df):
        
        st.divider()
        
        # Write a header
        st.markdown(f"<p style='color: hotpink; \
              font-size: 24px; \
              margin: 0;'>Max Values</p>",
              unsafe_allow_html=True)
            
        st.dataframe(final_results_df, hide_index=True, use_container_width=True, width=750)
        
        # Convert to CSV
        csv = final_results_df.to_csv(index=False)
        
        # Download button
        st.download_button(
                            label="Download Max Values",
                            data=csv,
                            file_name="max_values.csv",
                            mime="text/csv"
                          )
        st.divider()
        
class About():

    def __init__(self):
        
        pass
    
    def about_tab(self):
        
        st.write('')
     
        st.markdown(f"<p style='color: blue; \
                      font-size: 24px; \
                      margin: 0;'>Users Guide</p>",
                      unsafe_allow_html=True)
        
        st.write('')
        
        col1, col2 = st.columns([1,1])
        
        with col1:
        
            with st.expander('🪸 File Formatting'):
                
                st.markdown("""
                            ### File Conventions
                            - **Files** → Data and target output files must be `.csv`format. 
                            - **Data Files** → Must have at least the following columns.
                              - Genotype
                              - Columns with Y(II), Y(NPQ), and ETR followed by-Genotype. (e.g., Y(II)-C44).
                            - **Output Files** → Must have at least the following columns.
                              - Genotype
                              - Columns with Y(II) initial max, Y(NPQ) initial max, and ETR inital max).
                              - Spaces and case matter! 
                            """
                ,
                unsafe_allow_html=True
                )
                  
                st.write('')
                
                # Create a downloadable template
                template_df = pd.DataFrame([{
                                            "GenotypeID",
                                            "Cohort",	
                                            "Tank",	
                                            "Y(II) max initial",
                                            "Y(NPQ) max initial",
                                             "ETR max initial"
                                           }])
                
                st.download_button(
                                    label="📥 Download PAM Output File Template",
                                    data=template_df.to_csv(index=False),
                                    file_name="pam_template.csv",
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

        
