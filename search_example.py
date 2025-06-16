#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
import pickle
import numpy as np
from FAISS import load_index, search_similar_images, load_embeddings
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torch

# Load the FAISS index and data
index = load_index("image_index.faiss")
emb_tensor, image_paths = load_embeddings()

# Example: Search using an existing image as query
def search_by_image_path(query_image_path, k=5):
    """Search for similar images using an existing image as query"""
    # Load CLIP for encoding the query image
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_fast=True)
    
    # Process query image
    image = Image.open(query_image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    
    with torch.no_grad():
        query_embed = model.get_image_features(**inputs)
    query_embed = query_embed / query_embed.norm(p=2, dim=-1, keepdim=True)
    
    # Search for similar images
    results = search_similar_images(query_embed.numpy(), index, image_paths, k)
    
    print(f"\nTop {k} similar images to {query_image_path}:")
    for result in results:
        print(f"  {result['rank']}. {result['filename']} (similarity: {result['similarity']:.4f})")
    
    return results

# Example usage:
if __name__ == "__main__":
    # Use the first image as a query example
    query_path = image_paths[0]
    print(f"Using query image: {query_path}")
    search_by_image_path(query_path, k=10)

