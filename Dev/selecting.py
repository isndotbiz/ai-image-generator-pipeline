top_images = []
for c in range(k):
    idxs = [i for i, lab in enumerate(labels) if lab==c]
    ranked = sorted(idxs, key=lambda i: scores[i], reverse=True)
    top_images.extend(ranked[:5])  # top 5 each → 100 images