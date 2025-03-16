import io
import json
import tempfile
import os
from PIL import Image
import numpy as np

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

# Get the base directory of the function
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Path to models directory
MODELS_DIR = os.path.join(BASE_DIR, 'models')

# Check for existing models in python_backend
PYTHON_BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR)))), 'python_backend')
PYTHON_BACKEND_MODEL_DIR = os.path.join(PYTHON_BACKEND_DIR, '@model')

def find_model_file(filename):
    """Find a model file in various possible locations"""
    # Check in the models directory first
    model_path = os.path.join(MODELS_DIR, filename)
    if os.path.exists(model_path):
        return model_path
    
    # Check in python_backend/@model directory
    model_path = os.path.join(PYTHON_BACKEND_MODEL_DIR, filename)
    if os.path.exists(model_path):
        return model_path
    
    # Check in parent directories
    parent_dir = os.path.dirname(BASE_DIR)
    for _ in range(3):  # Check up to 3 levels up
        model_path = os.path.join(parent_dir, 'models', filename)
        if os.path.exists(model_path):
            return model_path
        parent_dir = os.path.dirname(parent_dir)
    
    return None

def parse_multipart(content_type, body):
    """Parse multipart form data to extract file and fields"""
    if not content_type.startswith("multipart/form-data"):
        return None, {}
    
    boundary = content_type.split("boundary=")[1].strip()
    parts = body.split(f"--{boundary}")
    
    image_data = None
    fields = {}
    
    for part in parts:
        if "Content-Disposition" not in part:
            continue
        
        # Check if this part contains a file
        if "filename" in part and ("image/jpeg" in part or "image/png" in part):
            binary_start = part.find("\r\n\r\n") + 4
            image_data = part[binary_start:].strip().encode()
        
        # Extract form fields
        elif "name=" in part:
            name_start = part.find('name="') + 6
            name_end = part.find('"', name_start)
            field_name = part[name_start:name_end]
            
            value_start = part.find("\r\n\r\n") + 4
            field_value = part[value_start:].strip()
            
            fields[field_name] = field_value
    
    return image_data, fields

def remove_background(image):
    """Remove background from image"""
    try:
        from rembg import remove
        
        # Try to find u2net.pth model file
        u2net_path = find_model_file('u2net.pth')
        if u2net_path:
            # Set the U2NET model path environment variable
            model_dir = os.path.dirname(u2net_path)
            print(f"Setting U2NET_HOME to {model_dir}")
            os.environ['U2NET_HOME'] = model_dir
        else:
            print("Warning: u2net.pth model file not found")
        
        return remove(image)
    except Exception as e:
        print(f"Error removing background: {str(e)}")
        raise e

def upscale_image(image, scale_factor):
    """Upscale image using ESRGAN"""
    try:
        import cv2
        from cv2 import dnn_superres
        
        # Convert PIL Image to OpenCV format
        img_array = np.array(image)
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Initialize super resolution model
        sr = dnn_superres.DnnSuperResImpl_create()
        
        # Try to find the model file
        model_filename = f"ESRGAN_x{scale_factor}.pb"
        model_path = find_model_file(model_filename)
        
        if not model_path:
            raise Exception(f"Model file {model_filename} not found")
        
        print(f"Using model file: {model_path}")
        
        # Read the model
        sr.readModel(model_path)
        sr.setModel("esrgan", scale_factor)
        
        # Upscale the image
        result = sr.upsample(img_cv)
        
        # Convert back to PIL Image
        result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        return Image.fromarray(result_rgb)
    except Exception as e:
        print(f"Error upscaling image: {str(e)}")
        raise e

def compress_image(image, quality, estimate=False):
    """Compress image with specified quality"""
    try:
        # Create a buffer for the original image
        original_buffer = io.BytesIO()
        image.save(original_buffer, format='PNG')
        original_size = len(original_buffer.getvalue())
        
        # Create a buffer for the compressed image
        compressed_buffer = io.BytesIO()
        image.save(compressed_buffer, format='JPEG', quality=quality, optimize=True)
        compressed_size = len(compressed_buffer.getvalue())
        
        if estimate:
            return {
                "originalSize": original_size,
                "compressedSize": compressed_size,
                "compressionRatio": round(original_size / compressed_size, 2) if compressed_size > 0 else 0,
                "savings": round((original_size - compressed_size) / original_size * 100, 2)
            }
        else:
            compressed_buffer.seek(0)
            return Image.open(compressed_buffer)
    except Exception as e:
        print(f"Error compressing image: {str(e)}")
        raise e

def edit_image(image, settings):
    """Apply edits to image based on settings"""
    try:
        from PIL import ImageEnhance, ImageFilter
        
        # Apply brightness
        if 'brightness' in settings:
            factor = float(settings['brightness']) / 100
            image = ImageEnhance.Brightness(image).enhance(factor)
        
        # Apply contrast
        if 'contrast' in settings:
            factor = float(settings['contrast']) / 100
            image = ImageEnhance.Contrast(image).enhance(factor)
        
        # Apply saturation
        if 'saturation' in settings:
            factor = float(settings['saturation']) / 100
            image = ImageEnhance.Color(image).enhance(factor)
        
        # Apply blur
        if 'blur' in settings:
            radius = float(settings['blur'])
            if radius > 0:
                image = image.filter(ImageFilter.GaussianBlur(radius=radius))
        
        # Apply rotation
        if 'rotation' in settings:
            angle = float(settings['rotation'])
            if angle != 0:
                image = image.rotate(angle, expand=True)
        
        # Apply sepia
        if 'sepia' in settings and float(settings['sepia']) > 0:
            sepia_intensity = float(settings['sepia']) / 100
            if sepia_intensity > 0:
                sepia_filter = [
                    (0.393 + 0.607 * (1 - sepia_intensity), 0.769 * (1 - sepia_intensity), 0.189 * (1 - sepia_intensity)),
                    (0.349 * (1 - sepia_intensity), 0.686 + 0.314 * (1 - sepia_intensity), 0.168 * (1 - sepia_intensity)),
                    (0.272 * (1 - sepia_intensity), 0.534 * (1 - sepia_intensity), 0.131 + 0.869 * (1 - sepia_intensity))
                ]
                image = image.convert('RGB', sepia_filter)
        
        return image
    except Exception as e:
        print(f"Error editing image: {str(e)}")
        raise e

def main(req, res):
    try:
        # Print environment variables and directories for debugging
        print(f"BASE_DIR: {BASE_DIR}")
        print(f"MODELS_DIR: {MODELS_DIR}")
        print(f"PYTHON_BACKEND_MODEL_DIR: {PYTHON_BACKEND_MODEL_DIR}")
        
        # List directories to help with debugging
        print(f"Directory contents of BASE_DIR: {os.listdir(BASE_DIR) if os.path.exists(BASE_DIR) else 'Not found'}")
        if os.path.exists(MODELS_DIR):
            print(f"Models directory contents: {os.listdir(MODELS_DIR)}")
        if os.path.exists(PYTHON_BACKEND_MODEL_DIR):
            print(f"Python backend model directory contents: {os.listdir(PYTHON_BACKEND_MODEL_DIR)}")
        
        # Get the operation type from the URL path or query parameters
        path = req.variables.get('APPWRITE_FUNCTION_PATH', '')
        query = req.variables.get('APPWRITE_FUNCTION_QUERY', '')
        operation = None
        
        # Try to get operation from query parameters
        if query:
            query_params = {}
            for param in query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[key] = value
            
            operation = query_params.get('operation')
        
        # Try to get operation from path if not found in query
        if not operation and path:
            parts = path.split('/')
            if parts and parts[-1] in ['remove-background', 'upscale', 'compress', 'edit']:
                operation = parts[-1]
        
        # Default to edit if no operation specified
        if not operation:
            operation = 'edit'
        
        print(f"Operation: {operation}")
        
        # Parse multipart form data
        content_type = req.headers.get("content-type", "")
        image_data, fields = parse_multipart(content_type, req.payload)
        
        if not image_data:
            return res.json({"error": "No image found in request"}, 400)
        
        # Open the image
        input_image = Image.open(io.BytesIO(image_data))
        
        # Process based on operation
        if operation == 'remove-background':
            output_image = remove_background(input_image)
            content_type = "image/png"
            filename = "no-bg.png"
            img_format = 'PNG'
        
        elif operation == 'upscale':
            scale_factor = int(fields.get('scale', '2'))
            if scale_factor not in [2, 4, 8]:
                scale_factor = 2
            output_image = upscale_image(input_image, scale_factor)
            content_type = "image/png"
            filename = f"upscaled_x{scale_factor}.png"
            img_format = 'PNG'
        
        elif operation == 'compress':
            quality = int(fields.get('quality', '85'))
            quality = max(1, min(100, quality))
            
            if 'estimate' in fields:
                # Return compression estimation as JSON
                result = compress_image(input_image, quality, estimate=True)
                return res.json(result)
            else:
                output_image = compress_image(input_image, quality)
                content_type = "image/jpeg"
                filename = "compressed.jpg"
                img_format = 'JPEG'
        
        elif operation == 'edit':
            # Parse edit settings
            settings = {}
            for key in ['brightness', 'contrast', 'saturation', 'blur', 'rotation', 'sepia']:
                if key in fields:
                    settings[key] = fields[key]
            
            output_image = edit_image(input_image, settings)
            content_type = "image/png"
            filename = "edited.png"
            img_format = 'PNG'
        
        else:
            return res.json({"error": f"Unknown operation: {operation}"}, 400)
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format=img_format)
        img_byte_arr.seek(0)
        
        # Return the processed image
        return res.send(img_byte_arr.getvalue(), 200, {
            "Content-Type": content_type,
            "Content-Disposition": f"attachment; filename={filename}"
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return res.json({"error": str(e)}, 500)
