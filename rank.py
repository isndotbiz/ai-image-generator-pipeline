#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
import numpy as np

cluster_centers = km.centroids  # shape (k, 512)
scores = []
for i, emb in enumerate(emb_tensor.numpy()):
    center = cluster_centers[labels[i]]
    scores.append(float(np.dot(emb, center)))  # higher = closer