# -*- coding: utf-8 -*-
"""app.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1UkcIO5NUPwdr8I02_AL_5XCvPx33B4cZ
"""
import streamlit as st
import requests
from bs4 import BeautifulSoup
import gzip
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# Define the header and body of text
header = "4xx Redirects V2 (BigC-URL path)"
body = """
This script is designed to automate the process of suggesting redirects by matching old URLs (resulting in 4xx errors) with live URLs from an XML sitemap crawl based on the similarity of the URL paths and H1 tags.

Files Used:

- Old.xlsx: This Excel file represents the list of old URLs that result in 4xx errors. It contains one column: URL.
- New.xlsx: This Excel file represents the live URLs crawled from the XML sitemap, including the H1 tags for each URL. It contains two columns: URL and H1.

Purpose:
The script compares the URL paths from Old.xlsx with the paths from New.xlsx, and takes into account the similarity between the old path and the H1 tag from New.xlsx. It suggests the best matching live URL with a similarity score.

Steps:

1. Loading the Data (Old.xlsx, New.xlsx)
2. Extracting URL paths
3. Similarity Matching (Paths and H1)
4. Generating Redirect Suggestions
5. Exporting Results to Excel (matched_urls.xlsx)
"""

# Add custom CSS to style the entire sidebar
st.markdown(  
        """
     <style>
    /* Style for the entire sidebar */
    [data-testid="stSidebar"] > div:first-child {
        background-color: blue;
        color: white;
    }
    /* Optional: Adjust text styles */
    [data-testid="stSidebar"] p {
        font-size: 14px;
        line-height: 1.5;
    }
    /* Header styles */
    .sidebar-header {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Place content inside the styled sidebar
with st.sidebar:
    st.markdown(f'<div class="sidebar-header">{header}</div>', unsafe_allow_html=True)
    st.markdown(f'<p>{body.replace("\n", "<br>")}</p>', unsafe_allow_html=True)

# Main page content
st.write("")

# Function to fetch and parse a webpage
def fetch_and_parse(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove unnecessary tags
        for tag in soup(['head', 'header', 'footer', 'script', 'style', 'meta']):
            tag.decompose()
        return soup
    except requests.RequestException as e:
        st.error(f"Error fetching URL {url}: {e}")
        return None

# Function to extract and combine text from the page
def extract_text_selectively(soup):
    if not soup:
        return ""
    individual_tags = {'p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'tr'}
    container_tags = {'div', 'section', 'article', 'main'}
    excluded_tags = {'style', 'script', 'meta', 'body', 'html', '[document]', 'button'}
    
    text_lines = []
    for element in soup.find_all(True, recursive=True):
        if element.name in excluded_tags:
            continue
        if element.name == 'tr':
            row_text = [cell.get_text(separator=' ', strip=True) for cell in element.find_all(['th', 'td']) if cell.get_text(strip=True)]
            if row_text:
                text_lines.append(', '.join(row_text))
        elif element.name in individual_tags:
            inline_text = ' '.join(element.stripped_strings)
            if inline_text:
                text_lines.append(inline_text)
        elif element.name in container_tags:
            direct_text = ' '.join([t.strip() for t in element.find_all(text=True, recursive=False) if t.strip()])
            if direct_text:
                text_lines.append(direct_text)
    
    combined_text = ' '.join(text_lines)
    return combined_text

# Function to calculate compression ratio
def calculate_compression_ratio(text):
    if not text:
        return 0
    original_size = len(text.encode('utf-8'))
    compressed_size = len(gzip.compress(text.encode('utf-8')))
    return original_size / compressed_size

# Streamlit app
st.title("URL Compression Ratio Calculator")

uploaded_file = st.file_uploader("Upload an Excel file with a column named 'URL'", type=['xlsx'])

if uploaded_file:
    # Read the uploaded Excel file
    try:
        df = pd.read_excel(uploaded_file)
        if 'URL' not in df.columns:
            st.error("The uploaded file must contain a column named 'URL'.")
        else:
            compression_ratios = []
            with st.spinner("Processing URLs..."):
                for index, row in df.iterrows():
                    url = row['URL']
                    st.write(f"Processing: {url}")
                    soup = fetch_and_parse(url)
                    combined_text = extract_text_selectively(soup)
                    compression_ratio = calculate_compression_ratio(combined_text)
                    compression_ratios.append(compression_ratio)
            
            # Add compression ratios to DataFrame
            df['Compression Ratio'] = compression_ratios
            
            st.success("Processing completed!")
            st.write("Here are the results:")
            st.dataframe(df)
            
            # Allow download of results
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            st.download_button(
                label="Download Results as Excel",
                data=output,
                file_name="compression_ratios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Visualize compression ratios
            st.subheader("Compression Ratios Visualization")
            plt.figure(figsize=(12, 8))
            bars = plt.bar(df['URL'], df['Compression Ratio'], color='blue', alpha=0.7, label='Compression Ratio')
            for i, bar in enumerate(bars):
                if df['Compression Ratio'][i] > 4.0:
                    bar.set_color('red')
            plt.axhline(y=4.0, color='orange', linestyle='--', linewidth=2, label='Spam Threshold (4.0)')
            plt.xticks(rotation=90, fontsize=8)
            plt.title("Compression Ratios of URLs", fontsize=16)
            plt.xlabel("URLs", fontsize=12)
            plt.ylabel("Compression Ratio", fontsize=12)
            plt.legend()
            plt.tight_layout()
            st.pyplot(plt)
    except Exception as e:
        st.error(f"Error processing the file: {e}")


