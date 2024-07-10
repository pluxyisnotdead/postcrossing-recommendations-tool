import gradio as gr
import requests
from PIL import Image
from io import BytesIO
import logging
import json
import os
import numpy as np
from parser import PostcrossingParser
from model import CLIPModel

logging.basicConfig(level=logging.INFO)

def parse_user_interface(username, password, target_name):
    parser = PostcrossingParser(username, password)
    result = parser.parse_user(target_name)
    logging.info(f"Result from parser: {result}")
    return result

def display_results(result, target_name):
    if result is None:
        logging.error("Result is None")
        return None, "No data found"

    if 'favorites' not in result and 'about_text' not in result:
        logging.error("Result does not contain expected keys")
        return None, "Invalid data format"

    # Load images from URLs
    images = []
    if 'favorites' in result:
        for url in result['favorites']:
            try:
                response = requests.get(url)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                images.append(img)
            except requests.exceptions.RequestException as e:
                logging.error(f"Error loading image from {url}: {e}")
                continue

    if not images and 'favorites' in result:
        logging.error("No images were loaded successfully")
        return None, f"No images found, about text: \n{result.get('about_text', '')}"

    return images, result.get('about_text', '')

def load_existing_json(json_file):
    try:
        with open(json_file, 'r') as f:
            result = json.load(f)
        return result
    except Exception as e:
        logging.error(f"Error loading existing JSON: {e}")
        return None

def parse_or_load_json(username, password, target_name, use_existing):
    json_file = f'users/{target_name}.json'
    if use_existing and os.path.exists(json_file):
        result = load_existing_json(json_file)
    else:
        result = parse_user_interface(username, password, target_name)
        if result:
            with open(json_file, 'w') as f:
                json.dump(result, f, indent=4)
    return display_results(result, target_name)

def get_existing_json_files():
    users_folder = 'users'
    return [os.path.join(users_folder, f) for f in os.listdir(users_folder) if f.endswith('.json')]

def recommend_images(model, user_data, images):
    if 'favorites' not in user_data and 'about_text' not in user_data:
        logging.error("User JSON does not contain 'favorites' or 'about_text'")
        return None, "Invalid user JSON format"

    favorites = user_data.get('favorites', [])
    about_text = user_data.get('about_text', '')

    if not favorites and not about_text:
        logging.error("No favorites or about_text provided")
        return None, "No favorites or about_text provided"

    logging.info(f"Favorites: {favorites}")
    logging.info(f"About Text: {about_text}")

    # Extract features from favorite images
    favorite_image_features = []
    for url in favorites:
        try:
            response = requests.get(url)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            feature = model.extract_features(img)
            favorite_image_features.append(feature)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error loading image from {url}: {e}")
            continue
        except Exception as e:
            logging.error(f"Error extracting features from image: {e}")
            continue

    if not favorite_image_features:
        logging.error("No features extracted from favorite images")
        return None, "No features extracted from favorite images"

    logging.info(f"Favorite Image Features: {favorite_image_features}")

    # Recommend images based on features and about text
    recommended_images = model.recommend(favorite_image_features, images, about_text)

    if not recommended_images:
        logging.error("No recommendations found")
        return None, "No recommendations found"

    return recommended_images

def recommend_images_with_titles(model, user_json, images):
    try:
        with open(user_json, 'r') as f:
            user_data = json.load(f)
    except Exception as e:
        logging.error(f"Error loading user JSON: {e}")
        return None, "Invalid user JSON"

    recommended_images = recommend_images(model, user_data, images)
    if recommended_images is None:
        return None, "No recommendations found"

    # Create a list of tuples (image, title)
    images_with_titles = [(img, f"Score: {score:.2f}") for img, score in recommended_images]

    favorites_images = []
    if 'favorites' in user_data:
        for url in user_data['favorites']:
            try:
                response = requests.get(url)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                favorites_images.append(img)
            except requests.exceptions.RequestException as e:
                logging.error(f"Error loading image from {url}: {e}")
                continue

    about_text = user_data.get('about_text', '')

    return images_with_titles, favorites_images, about_text


# Define the Gradio interface
iface = gr.Interface(
    fn=lambda username, password, target_name, use_existing: parse_or_load_json(username, password, target_name, use_existing),
    inputs=[
        gr.Textbox(label="Username"),
        gr.Textbox(label="Password", type="password"),
        gr.Textbox(label="Target Username"),
        gr.Checkbox(label="Use existing JSON if available", value=True)
    ],
    outputs=[
        gr.Gallery(label="Favorites"),  # Use Gallery for interactive image viewing
        gr.Textbox(label="About Text")
    ],
    title="Postcrossing Parser",
    description="Enter your Postcrossing credentials and the target username to parse their data or use existing JSON if available."
)

# Define the second tab for recommendations
recommendation_iface = gr.Interface(
    fn=lambda user_json, images: recommend_images_with_titles(model, user_json, images),
    inputs=[
        gr.Dropdown(label="User JSON", choices=get_existing_json_files(), type="value"),
        gr.File(label="Images", file_count="multiple", type="filepath")
    ],
    outputs=[
        gr.Gallery(label="Favorites"),
        gr.Textbox(label="About Text"),
        gr.Gallery(label="Recommended Images with Scores"),
    ],
    title="Recommendations",
    description="Select a user JSON and upload images to get recommendations."
)

# Combine both interfaces into tabs
tabbed_interface = gr.TabbedInterface(
    [iface, recommendation_iface],
    ["Parser", "Recommendations"]
)

if __name__ == "__main__":
    model = CLIPModel()  # Ensure the model is initialized
    tabbed_interface.launch()
