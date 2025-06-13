import replicate
import requests
import sys

model = "black-forest-labs/flux-1.1-pro"
prompt = f"""Photo mode: sleek Miami Edgewater sky-suite, Cartier Love ring foreground, \
Canon EOS R5 35 mm f/1.8 ISO 200, soft window light, \
overlay "Spoil to Stay Close", 4:5, style: RealistVision"""

print(f"Using prompt: {prompt}")
print(f"Making request to {model}...")

try:
    url = replicate.run(model, input={
        "prompt": prompt,
        "aspect_ratio": "4:5",
        "output_format": "png",
        "negative_prompt": ("lowres, jpeg artifacts, plastic, text, watermark, "
                            "logo, duplicate, deformed, bad anatomy")
    })
    print(f"Got result: {type(url)} - {url}")
    
    if hasattr(url, 'url'):
        actual_url = url.url
    else:
        actual_url = str(url)
    
    print(f"Downloading from: {actual_url}")
    response = requests.get(actual_url)
    print(f"Response status: {response.status_code}")
    
    outfile = "test_output.png"
    with open(outfile, "wb") as f:
        f.write(response.content)
    print(f"Saved {outfile}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

