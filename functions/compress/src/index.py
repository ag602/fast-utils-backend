import io
import json
import tempfile
import os
from PIL import Image

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
            quality = 85  # Default quality
            estimate = False
            
            # Find the image part and parameters
            for part in parts:
                if "Content-Disposition" in part and "filename" in part and ("image/jpeg" in part or "image/png" in part):
                    # Extract the binary data
                    binary_start = part.find("\r\n\r\n") + 4
                    image_data = part[binary_start:].strip().encode()
                
                if "Content-Disposition" in part and "name=\"quality\"" in part:
                    value_start = part.find("\r\n\r\n") + 4
                    quality_value = part[value_start:].strip()
                    try:
                        quality = int(quality_value)
                        quality = max(1, min(100, quality))  # Ensure quality is between 1 and 100
                    except ValueError:
                        pass
                
                if "Content-Disposition" in part and "name=\"estimate\"" in part:
                    estimate = True
            
            if not image_data:
                return res.json({"error": "No image found in request"}, 400)
            
            # Open the image
            input_image = Image.open(io.BytesIO(image_data))
            input_size = len(image_data)
            
            # If just estimating, return the original and compressed sizes
            if estimate:
                # Create a temporary buffer for the compressed image
                temp_buffer = io.BytesIO()
                
                # Save with the specified quality
                input_image.save(temp_buffer, format='JPEG', quality=quality, optimize=True)
                compressed_size = len(temp_buffer.getvalue())
                
                # Return the size information
                return res.json({
                    "originalSize": input_size,
                    "compressedSize": compressed_size,
                    "compressionRatio": round(input_size / compressed_size, 2) if compressed_size > 0 else 0,
                    "savings": round((input_size - compressed_size) / input_size * 100, 2)
                })
            
            # Compress the image
            output_buffer = io.BytesIO()
            input_image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            output_buffer.seek(0)
            
            # Return the compressed image
            return res.send(output_buffer.getvalue(), 200, {
                "Content-Type": "image/jpeg",
                "Content-Disposition": "attachment; filename=compressed.jpg"
            })
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return res.json({"error": str(e)}, 500)
