import io
import json
import tempfile
import os
from PIL import Image
import numpy as np
from cv2 import dnn_superres

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
            scale_factor = 2  # Default scale factor
            
            # Find the image part and scale factor
            for part in parts:
                if "Content-Disposition" in part and "filename" in part and ("image/jpeg" in part or "image/png" in part):
                    # Extract the binary data
                    binary_start = part.find("\r\n\r\n") + 4
                    image_data = part[binary_start:].strip().encode()
                
                if "Content-Disposition" in part and "name=\"scale\"" in part:
                    value_start = part.find("\r\n\r\n") + 4
                    scale_value = part[value_start:].strip()
                    if scale_value in ["2", "4", "8"]:
                        scale_factor = int(scale_value)
            
            if not image_data:
                return res.json({"error": "No image found in request"}, 400)
            
            # Save the input image to a temporary file
            input_path = os.path.join(temp_dir, "input.png")
            with open(input_path, "wb") as f:
                f.write(image_data)
            
            # Initialize the super resolution model
            sr = dnn_superres.DnnSuperResImpl_create()
            
            # Path to the model - this would need to be included in the function deployment
            model_path = f"models/ESRGAN_x{scale_factor}.pb"
            
            # Check if model exists
            if not os.path.exists(model_path):
                return res.json({"error": f"Model for scale factor {scale_factor} not found"}, 500)
            
            # Read the model
            sr.readModel(model_path)
            
            # Set the model and scale
            sr.setModel("esrgan", scale_factor)
            
            # Read the input image
            img = cv2.imread(input_path)
            
            # Upscale the image
            result = sr.upsample(img)
            
            # Save the result to a temporary file
            output_path = os.path.join(temp_dir, "output.png")
            cv2.imwrite(output_path, result)
            
            # Read the output file and return it
            with open(output_path, "rb") as f:
                output_data = f.read()
            
            # Return the processed image
            return res.send(output_data, 200, {
                "Content-Type": "image/png",
                "Content-Disposition": f"attachment; filename=upscaled_x{scale_factor}.png"
            })
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return res.json({"error": str(e)}, 500)
