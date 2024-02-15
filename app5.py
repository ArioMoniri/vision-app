import streamlit as st
import google.cloud
import requests
import io

import firebase_admin
from firebase_admin import credentials, firestore


# Check if the Firebase app has already been initialized
if not firebase_admin._apps:
    # Initialize Firebase Admin SDK
    cred = credentials.Certificate('D:/Chrome Downloads/vision-app-414411-firebase-adminsdk-7uiv4-1f79ffa362.json')
    firebase_admin.initialize_app(cred)

# Get a Firestore client
db = firestore.client()

def add_classification_to_firestore(category, confidence):
    doc_ref = db.collection('recyclingClassifications').document()
    doc_ref.set({
        'category': category,
        'confidence': confidence,
        'timestamp': firestore.SERVER_TIMESTAMP
    })

# Set your Unsplash Access Key
UNSPLASH_ACCESS_KEY = 'u-scjqP5ILn0N_XsAs6CZhduPip7Ci9WWsOoQkHI3mw'

def fetch_image_url(category):
    enhanced_query = f"{category} recycle trash"
    url = f"https://api.unsplash.com/search/photos?query={enhanced_query}&client_id={UNSPLASH_ACCESS_KEY}&orientation=landscape&content_filter=high"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json()['results']
            if results:
                # Example: Select the most liked image
                selected_image = max(results, key=lambda x: x['likes'])
                return selected_image['urls']['regular']
    except Exception as e:
        st.error(f"Error fetching image: {e}")
    return None
# Function to add classification result to Firestore
def add_classification_to_firestore(category, confidence):
    doc_ref = db.collection('recyclingClassifications').document()
    doc_ref.set({
        'category': category,
        'confidence': confidence,
        'timestamp': firestore.SERVER_TIMESTAMP
    })

def set_page_bg_color(hex_color):
    """Sets the background color of the Streamlit app."""
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
client = vision.ImageAnnotatorClient()

# Initialize session state for uploaded_file if it doesn't already exist
if 'uploaded_file' not in st.session_state:
    st.session_state['uploaded_file'] = None

# UI modifications for conditional display
st.title('Recyclable Material Classifier with Google Vision API')

# Only show the uploader if no file has been uploaded yet
if st.session_state['uploaded_file'] is None:
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png"])
    if uploaded_file is not None:
        st.session_state['uploaded_file'] = uploaded_file
else:
    # If a file has been uploaded, process and display the results
    uploaded_file = st.session_state['uploaded_file']
    image_bytes = uploaded_file.getvalue()

    # Call the Vision API for label detection
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

    # After detecting the recyclable category and fetching the image URL
    if found_category:
        category_details = recycling_categories[found_category]
        image_url = fetch_image_url(category_details["query"])
        set_page_bg_color(category_details["color"])
        # Using custom HTML to make the font larger
        st.markdown(
            f"<h2 style='font-size: 24px;'>{found_category.capitalize()} should be recycled in the corresponding bin.</h2>",
            unsafe_allow_html=True)
        if image_url:
            st.image(image_url, caption=f"{found_category.capitalize()} Recycling trash can ", use_column_width=True)
        confidence = 0.9
        add_classification_to_firestore(found_category, confidence)
    else:
        st.write("The recyclable category of this item could not be determined or is not present.")

    # Optionally, add a button to allow the user to classify a new image
    if st.button("Classify another image"):
        st.session_state['uploaded_file'] = None
