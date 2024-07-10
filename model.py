import clip
import torch
import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
import requests
from io import BytesIO
from transformers import pipeline

class CLIPModel:
    def __init__(self, model_name='ViT-B/32'):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load(model_name, self.device)
        self.context_length = 77  # Maximum context length for CLIP
        self.sentiment_analyzer = pipeline("sentiment-analysis", model="blanchefort/rubert-base-cased-sentiment")

    def extract_features(self, image):
        image = self.preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            image_features = self.model.encode_image(image)
        return image_features.cpu().numpy()

    def recommend(self, favorite_images, new_image_paths, about_text):
        def load_image(img_path):
            if img_path.startswith('http://') or img_path.startswith('https://'):
                response = requests.get(img_path)
                image = Image.open(BytesIO(response.content))
            else:
                image = Image.open(img_path)
            return self.preprocess(image).unsqueeze(0).to(self.device)

        # Truncate about_text to fit within the context length
        truncated_text = about_text[:self.context_length]

        # Preprocess and encode favorite images
        favorite_image_features = []
        for img in favorite_images:
            image = load_image(img)
            with torch.no_grad():
                image_features = self.model.encode_image(image)
            favorite_image_features.append(image_features.cpu().numpy())

        # Preprocess and encode new images if they are paths
        new_image_features = []
        for img in new_image_paths:
            if isinstance(img, str):  # Check if img is a path
                image = load_image(img)
                with torch.no_grad():
                    image_features = self.model.encode_image(image)
                new_image_features.append(image_features.cpu().numpy())
            else:
                new_image_features.append(img)  # Assume img is already a feature

        # Encode about text
        text = clip.tokenize([truncated_text]).to(self.device)
        with torch.no_grad():
            text_features = self.model.encode_text(text).cpu().numpy()

        # Calculate similarity scores
        favorite_image_features = np.vstack(favorite_image_features)
        new_image_features = np.vstack(new_image_features)

        image_similarity = cosine_similarity(new_image_features, favorite_image_features)
        text_similarity = cosine_similarity(new_image_features, text_features)

        # Combine image and text similarity scores
        combined_similarity = image_similarity.mean(axis=1) + text_similarity.flatten()

        # Analyze sentiment of about_text
        sentiment = self.sentiment_analyzer(about_text)[0]
        sentiment_score = 1 if sentiment['label'] == 'POSITIVE' else -1

        # Adjust combined similarity based on sentiment
        combined_similarity += sentiment_score

        # Return all recommended images with their scores
        recommended_images = [(new_image_paths[i], combined_similarity[i]) for i in range(len(new_image_paths))]
        recommended_images = sorted(recommended_images, key=lambda x: x[1], reverse=True)

        return recommended_images
