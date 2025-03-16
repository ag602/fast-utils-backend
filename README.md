# FastUtils - Appwrite Serverless Function Deployment Guide

This guide explains how to deploy the FastUtils backend to Appwrite's serverless functions.

## Prerequisites

1. [Appwrite Account](https://appwrite.io/)
2. [Appwrite CLI](https://appwrite.io/docs/command-line) installed
3. Python 3.9+ (for local testing)

## Function Structure

The FastUtils backend uses a single unified function for all image processing operations:
- `image-processor` - Handles all image operations (background removal, upscaling, compression, and editing)

The function includes:
- `src/index.py` - The main function code that handles all operations
- `requirements.txt` - Python dependencies
- `models/` - Directory for model files

## Required Model Files

You need to download and include the following model files in your deployment:

1. **For Background Removal**:
   - Download the U2Net model file (`u2net.pth`) from [here](https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.pth)
   - Place it in the `models` directory

2. **For Image Upscaling**:
   - Download ESRGAN model files:
     - [ESRGAN_x2.pb](https://github.com/fannymonori/TF-ESRGAN/raw/master/export/ESRGAN_x2.pb)
     - [ESRGAN_x4.pb](https://github.com/fannymonori/TF-ESRGAN/raw/master/export/ESRGAN_x4.pb)
     - [ESRGAN_x8.pb](https://github.com/fannymonori/TF-ESRGAN/raw/master/export/ESRGAN_x8.pb)
   - Place them in the `models` directory

## Deployment Steps

### 1. Login to Appwrite CLI

```bash
appwrite login
```

### 2. Initialize Appwrite Project (if not already done)

```bash
appwrite init project
```

Follow the prompts to select your project.

### 3. Prepare Model Files

Download the required model files and place them in the `models` directory:

```bash
cd appwrite/functions/image-processor
mkdir -p models
# Download models (you can use curl, wget, or manually download)
# For background removal:
curl -L https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.pth -o models/u2net.pth
# For upscaling:
curl -L https://github.com/fannymonori/TF-ESRGAN/raw/master/export/ESRGAN_x2.pb -o models/ESRGAN_x2.pb
curl -L https://github.com/fannymonori/TF-ESRGAN/raw/master/export/ESRGAN_x4.pb -o models/ESRGAN_x4.pb
curl -L https://github.com/fannymonori/TF-ESRGAN/raw/master/export/ESRGAN_x8.pb -o models/ESRGAN_x8.pb
```

### 4. Deploy the Unified Function

```bash
cd appwrite/functions/image-processor
appwrite functions create \
  --name "FastUtils Image Processor" \
  --runtime python-3.9 \
  --entrypoint src/index.py \
  --execute
```

### 5. Deploy Function Code with Models

```bash
appwrite functions createDeployment \
  --functionId [FUNCTION_ID] \
  --entrypoint src/index.py \
  --code .
```

Replace `[FUNCTION_ID]` with the ID of the function you created.

### 6. Update Environment Variables in UI

After deploying the function, update the `.env.local` file in your Next.js UI project:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:5000
NEXT_PUBLIC_APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
NEXT_PUBLIC_APPWRITE_PROJECT_ID=your-project-id
NEXT_PUBLIC_APPWRITE_FUNCTION_ID=your-function-id
```

## How It Works

The unified function uses a path parameter to determine which operation to perform:

1. **Background Removal**: `operation=remove-background`
2. **Image Upscaling**: `operation=upscale`
3. **Image Compression**: `operation=compress`
4. **Image Editing**: `operation=edit`

The UI automatically routes requests to the appropriate operation based on the endpoint.

## Important Notes

1. **Model Files**: The model files are quite large (especially u2net.pth which is around 170MB). Make sure your Appwrite function has enough storage allocated for these files.

2. **Memory Limits**: Be aware of Appwrite's memory limits for functions. Image processing can be memory-intensive, so you might need to adjust the memory allocation for your function.

3. **Execution Time**: Set appropriate execution time limits for your function, especially for the upscale operation which can take longer for larger images.

4. **CORS**: Make sure your Appwrite project has the appropriate CORS settings to allow requests from your UI domain.

## Troubleshooting

- Check function logs in the Appwrite console for any errors
- Ensure all dependencies are correctly listed in the requirements.txt file
- Verify that your function has the necessary permissions to access any external services
- If you encounter model loading issues, check that the model files are correctly placed in the models directory

## Local Testing

You can test the function locally before deploying:

```bash
cd appwrite/functions/image-processor
pip install -r requirements.txt
# Download model files as described above
python -c "import src.index as module; print(dir(module))"
