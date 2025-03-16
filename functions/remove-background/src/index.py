import io
import json
import tempfile
import os
from PIL import Image
import numpy as np
from rembg import remove

"""
  'req' variable has:
    'headers' - object with request headers
    'payload' - request body data as a string
    'variables' - object with function variables

  'res' variable has:
    'send(text, status)' - function to return text response. Status code defaults to 200
    'json(obj, status)' - function to return JSON response. Status code defaults to 200
  
  If an error is thrown, a response with code 500 will be returned.
"""

def main(req, res):
    try:
        # Create a temporary directory to work with files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Parse multipart form data
            content_type = req.headers.get("content-type", "")
            
            if not content_type.startswith("multipart/form-data"):
                return res.json({"error": "Expected multipart/form-data"}, 400)
            
            # Extract boundary
            boundary = content_type.split("boundary=")[1].strip()
            
            # Parse the multipart form data
            body = req.payload
            parts = body.split(f"--{boundary}")
            
            image_data = None
            
            # Find the image part
            for part in parts:
                if "Content-Disposition" in part and "filename" in part and ("image/jpeg" in part or "image/png" in part):
                    # Extract the binary data
                    binary_start = part.find("\r\n\r\n") + 4
                    image_data = part[binary_start:].strip().encode()
                    break
            
            if not image_data:
                return res.json({"error": "No image found in request"}, 400)
            
            # Process the image
            input_image = Image.open(io.BytesIO(image_data))
            
            # Remove background
            output_image = remove(input_image)
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            output_image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Return the processed image
            return res.send(img_byte_arr.getvalue(), 200, {
                "Content-Type": "image/png",
                "Content-Disposition": "attachment; filename=no-bg.png"
            })
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return res.json({"error": str(e)}, 500)
