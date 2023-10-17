import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from urllib.parse import urlparse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

base_url = "https://www.oc.gov.ma/fr"

data_dict = {}
response = requests.get(base_url)

# Extract the base URL
parsed_base_url = urlparse(base_url).netloc

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content of the base page with a specified encoding
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding=response.encoding)

    # Find all the HTML elements with an 'href' attribute
    for link in soup.find_all(href=True):
        path = link['href']

        # Create an absolute URL by joining the base URL and the relative path
        absolute_url = urljoin(base_url, path)

        # Extract the netloc (domain) of the absolute URL
        parsed_url = urlparse(absolute_url)
        absolute_netloc = parsed_url.netloc

        # Check if the URL has the same base URL
        if absolute_netloc == parsed_base_url:
            # Send an HTTP GET request to the absolute URL
            page_response = requests.get(absolute_url)

            # Check if the request to the relative page was successful
            if page_response.status_code == 200:
                # Parse the HTML content of the relative page with a specified encoding
                page_soup = BeautifulSoup(page_response.content, 'html.parser', from_encoding=page_response.encoding)

                # Extract and store the content of the relative page, preserving accents and removing '\n'
                page_content = ' '.join(line.strip() for line in page_soup.stripped_strings)

                # Avoid including specific file extensions (e.g., .png, .jpg, .css, .js, .json)
                if not absolute_url.endswith((".png", ".jpg", ".css", ".js", ".json")):
                    data_dict[absolute_url] = page_content

            else:
                print(f"Failed to retrieve the relative page. Status code: {page_response.status_code}")

# Write the data to a JSON file
with open('./data/scraped_data.json', 'w', encoding='utf-8') as json_file:
    json.dump(data_dict, json_file, ensure_ascii=False, indent=4)
print("Data has been saved to scraped_data.json")
# Open the file for writing and save the string
file_path = "./data/scraped_data2.txt"
with open(file_path, "w", encoding="utf-8") as text_file:
    text_file.write(str(data_dict))


def create_pdf(pdf_directory, pdf_name, pdf_content):
    pdf_path = os.path.join(pdf_directory, pdf_name)
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    c.drawString(100, height - 100, pdf_content)
    c.save()
# Choose the directory where the PDFs will be saved
output_directory = "./data/"
# Create PDFs from the dictionary
for pdf_name, pdf_content in data_dict.items():
    pdf_name = pdf_name.split('://')[1].replace('/','-')+'.pdf'
    create_pdf(output_directory, pdf_name, pdf_content)
print("PDFs created successfully in the specified directory.")