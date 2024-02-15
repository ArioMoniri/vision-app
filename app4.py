import streamlit as st
from google.cloud import vision
import requests
import io

# Set your Unsplash Access Key and Google Cloud credentials
UNSPLASH_ACCESS_KEY = 'u-scjqP5ILn0N_XsAs6CZhduPip7Ci9WWsOoQkHI3mw'
GOOGLE_CLOUD_CREDENTIALS = {
    # Your Google Cloud credentials here
}

def fetch_image_url(query):
    url = f"https://api.unsplash.com/search/photos?query={query} recycling bin&client_id={UNSPLASH_ACCESS_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json()['results']
        if results:
            return results[0]['urls']['regular']
    return None

def set_page_bg_color(hex_color):
    st.markdown(
        f"""<style>.stApp {{ background-color: {hex_color}; }}</style>""",
        unsafe_allow_html=True
    )

# Relevant categories and their corresponding bin colors and search queries
recycling_categories = {
    "plastic": {"color": "#FFFF00", "query": "plastic recycling bin"},
    "paper": {"color": "#0000FF", "query": "paper recycling bin"},
    "glass": {"color": "#008000", "query": "glass recycling bin"},
    "metal": {"color": "#FF0000", "query": "metal recycling bin"}
}

# Ignore list for non-recyclable items detection
ignore_list = ['hand', 'person', 'animal']

# Authenticate to the Vision API
client = vision.ImageAnnotatorClient(credentials=GOOGLE_CLOUD_CREDENTIALS)

# UI
st.title('Recyclable Material Classifier with Google Vision API')

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png"])
if uploaded_file is not None:
    image_bytes = uploaded_file.getvalue()
    st.image(image_bytes, caption='Uploaded Image', use_column_width=True)

    image = vision.Image(content=image_bytes)
    response = client.label_detection(image=image)
    labels = response.label_annotations

    found_category = None
    for label in labels:
        label_desc = label.description.lower()
        if label_desc in ignore_list:
            continue
        for category, details in recycling_categories.items():
            if category in label_desc:
                found_category = category
                break
        if found_category:
            break

    if found_category:
        category_details = recycling_categories[found_category]
        image_url = fetch_image_url(category_details["query"])
        set_page_bg_color(category_details["color"])
        st.markdown(f"**{found_category.capitalize()}** should be recycled in the corresponding bin.")
        if image_url:
            st.image(image_url, caption=f"{found_category.capitalize()} Recycling Bin", use_column_width=True)
    else:
        st.write("The recyclable category of this item could not be determined or is not present.")
