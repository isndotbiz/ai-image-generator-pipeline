from PIL import Image
import torch
import glob
from transformers import CLIPProcessor, CLIPModel

# 1. Load CLIP with fast processor
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")  # ViT-B/32 encoder  [oai_citation:3‡huggingface.co](https://huggingface.co/openai/clip-vit-base-patch32?utm_source=chatgpt.com)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_fast=True)

# 2. Iterate images and compute embeddings
# Get all social media images from the images directory
image_paths = (glob.glob("/Users/jonathanmallinger/Dev/images/*_tw.png") + 
               glob.glob("/Users/jonathanmallinger/Dev/images/*_tiktok.png") + 
               glob.glob("/Users/jonathanmallinger/Dev/images/*_ig.png"))
print(f"Found {len(image_paths)} images to process")
embeddings = []

for i, path in enumerate(image_paths):
    if i % 100 == 0:  # Progress update every 100 images
        print(f"Processing image {i+1}/{len(image_paths)} ({100*(i+1)/len(image_paths):.1f}%)")
    
    image = Image.open(path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        image_embed = model.get_image_features(**inputs)  # 512-d vector  [oai_citation:4‡huggingface.co](https://huggingface.co/docs/transformers/v4.29.1/model_doc/clip?utm_source=chatgpt.com)
    image_embed = image_embed / image_embed.norm(p=2, dim=-1, keepdim=True)
    embeddings.append(image_embed.cpu())

print(f"Completed processing all {len(image_paths)} images!")

# 3. Stack into tensor
emb_tensor = torch.vstack(embeddings)  # shape (1479, 512)

# 4. Save embeddings and paths for FAISS
import pickle
with open("image_embeddings.pkl", 'wb') as f:
    pickle.dump(emb_tensor, f)
with open("image_paths.pkl", 'wb') as f:
    pickle.dump(image_paths, f)

print(f"Saved embeddings tensor with shape: {emb_tensor.shape}")
print("Embeddings and image paths saved for FAISS indexing.")
