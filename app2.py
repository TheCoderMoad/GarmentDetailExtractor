import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io
import re
#
# Configure the API key
GOOGLE_API_KEY = 'Your api key'
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('models/gemini-1.5-flash')

# Function to process images and extract details
def process_images(image_files):
    details = {
        'Image': [],
        'Text': [],
        'Garment Type': [],
        'Brand': [],
        'Size': [],
        'Color': [],
        'Fabric': [],
        'Additional Characteristics': []
    }
    for image_file in image_files:
        image = Image.open(image_file)
        text = get_text_from_image(image)
        details['Image'].append(image_file.name)
        details['Text'].append(text)

        garment_type, brand, size, color, fabric, additional_characteristics = extract_garment_details(text)
        details['Garment Type'].append(garment_type)
        details['Brand'].append(brand)
        details['Size'].append(size)
        details['Color'].append(color)
        details['Fabric'].append(fabric)
        details['Additional Characteristics'].append(additional_characteristics)

    return pd.DataFrame(details)

def get_text_from_image(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    image_data = img_byte_arr.getvalue()
    
    # Convert the image data to the appropriate format for the API
    image_part = {
        "inline_data": {
            "data": image_data,
            "mime_type": "image/jpeg"
        }
    }
    
    # Generate content from the image using the Gemini API
    response = model.generate_content([
        "Describe the garment in the image and provide the following details:",
        "Garment Type:",
        "Brand:",
        "Size:",
        "Color:",
        "Fabric:",
        "Additional Characteristics:",
        image_part
    ])
    
    if response and response.candidates:
        return response.candidates[0].content.parts[0].text
    return 'Text not found'

def extract_garment_details(text):
    # Print the raw text to see the actual format
    st.write("Raw text from API:", text)
    
    # Patterns for structured responses
    structured_patterns = {
        'Garment Type': re.search(r'Garment Type:\s*(.*)', text),
        'Brand': re.search(r'Brand:\s*(.*)', text),
        'Size': re.search(r'Size:\s*(.*)', text),
        'Color': re.search(r'Color:\s*(.*)', text),
        'Fabric': re.search(r'Fabric:\s*(.*)', text),
        'Additional Characteristics': re.search(r'Additional Characteristics:\s*(.*)', text)
    }

    if all(pattern is not None for pattern in structured_patterns.values()):
        return (
            structured_patterns['Garment Type'].group(1).strip(),
            structured_patterns['Brand'].group(1).strip(),
            structured_patterns['Size'].group(1).strip(),
            structured_patterns['Color'].group(1).strip(),
            structured_patterns['Fabric'].group(1).strip(),
            structured_patterns['Additional Characteristics'].group(1).strip()
        )

    # Patterns for unstructured responses
    garment_type = re.search(r'\b(zip-up hoodie|hoodie|shirt|t-shirt|jacket|pants|shorts|sweater|dress|skirt|sweatshirt)\b', text, re.IGNORECASE)
    brand = re.search(r'brand is ([A-Za-z\s]+)', text, re.IGNORECASE) or re.search(r'\"([^\"]+)\"', text, re.IGNORECASE)
    size = re.search(r'\b(size \w+|\bL\b|\bM\b|\bS\b|\bXL\b|\bXXL\b)\b', text, re.IGNORECASE)
    color = re.search(r'\b(gray|red|blue|green|black|white|yellow|brown|purple|pink|orange|beige)\b', text, re.IGNORECASE)
    fabric = re.search(r'(\d+% \w+)', text, re.IGNORECASE)
    additional_characteristics = re.findall(r'(\bhood\b|\bstring\b|\btag\b|\bembroidered\b|\bkangaroo pocket\b|\blabel\b|\btext\b|\blining\b|\blogo\b|\bpocket\b)', text, re.IGNORECASE)

    return (
        garment_type.group(1) if garment_type else 'Not Found',
        brand.group(1) if brand else 'Not Found',
        size.group(1) if size else 'Not Found',
        color.group(1) if color else 'Not Found',
        fabric.group(1) if fabric else 'Not Found',
        ', '.join(additional_characteristics) if additional_characteristics else 'Not Found'
    )

def main():
    st.title("Garment Detail Extractor")

    uploaded_files = st.file_uploader("Upload Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        df = process_images(uploaded_files)
        st.write(df)

        output = io.BytesIO()
        df.to_excel(output, index=False, engine='xlsxwriter')
        output.seek(0)

        st.download_button(
            label="Download Excel file",
            data=output,
            file_name="garment_details.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
