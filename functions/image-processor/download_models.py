import os
import sys
import shutil
import requests
from tqdm import tqdm

def download_file(url, destination):
    """
    Download a file with progress bar
    """
    if os.path.exists(destination):
        print(f"File already exists: {destination}")
        return
    
    print(f"Downloading {url} to {destination}")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    with open(destination, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=os.path.basename(destination)) as pbar:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    
    print(f"Downloaded {destination}")

def copy_file(source, destination):
    """
    Copy a file with progress bar
    """
    if os.path.exists(destination):
        print(f"File already exists: {destination}")
        return
    
    if not os.path.exists(source):
        print(f"Source file does not exist: {source}")
        return False
    
    print(f"Copying {source} to {destination}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    # Get file size for progress bar
    file_size = os.path.getsize(source)
    
    # Copy with progress bar
    with open(source, 'rb') as src, open(destination, 'wb') as dst:
        with tqdm(total=file_size, unit='B', unit_scale=True, desc=os.path.basename(destination)) as pbar:
            while True:
                chunk = src.read(1024 * 1024)  # Read 1MB at a time
                if not chunk:
                    break
                dst.write(chunk)
                pbar.update(len(chunk))
    
    print(f"Copied {destination}")
    return True

def main():
    # Create models directory
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    os.makedirs(models_dir, exist_ok=True)
    
    # Check for python_backend directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    python_backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 'python_backend')
    python_backend_model_dir = os.path.join(python_backend_dir, '@model')
    
    # Model URLs
    models = {
        "u2net.pth": "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.pth",
        "ESRGAN_x2.pb": "https://github.com/fannymonori/TF-ESRGAN/raw/master/export/ESRGAN_x2.pb",
        "ESRGAN_x4.pb": "https://github.com/fannymonori/TF-ESRGAN/raw/master/export/ESRGAN_x4.pb",
        "ESRGAN_x8.pb": "https://github.com/fannymonori/TF-ESRGAN/raw/master/export/ESRGAN_x8.pb"
    }
    
    # Process each model
    for model_name, url in models.items():
        destination = os.path.join(models_dir, model_name)
        
        # Check if model exists in python_backend/@model directory
        python_backend_model_path = os.path.join(python_backend_model_dir, model_name)
        
        if os.path.exists(python_backend_model_path):
            print(f"Found existing model in python_backend: {python_backend_model_path}")
            if copy_file(python_backend_model_path, destination):
                continue
        
        # If not found or copy failed, download
        download_file(url, destination)
    
    print("\nAll models processed successfully!")
    print(f"Models directory: {models_dir}")
    print("Files available:")
    for filename in os.listdir(models_dir):
        file_path = os.path.join(models_dir, filename)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        print(f"  - {filename} ({file_size:.2f} MB)")

if __name__ == "__main__":
    main()
