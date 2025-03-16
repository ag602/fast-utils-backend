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

### 3. Deploy the Unified Function

```bash
cd appwrite/functions/image-processor
appwrite functions create \
  --name "FastUtils Image Processor" \
  --runtime python-3.9 \
  --entrypoint src/index.py \
  --execute
```

### 4. Deploy Function Code

```bash
appwrite functions createDeployment \
  --functionId [FUNCTION_ID] \
  --entrypoint src/index.py \
  --code .
```

Replace `[FUNCTION_ID]` with the ID of the function you created.

### 5. Update Environment Variables in UI

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

1. **Model Files**: For the upscale function, you need to upload the ESRGAN model files to the function's storage. You can do this through the Appwrite console after deploying the function.

2. **Memory Limits**: Be aware of Appwrite's memory limits for functions. Image processing can be memory-intensive, so you might need to adjust the memory allocation for your function.

3. **Execution Time**: Set appropriate execution time limits for your function, especially for the upscale operation which can take longer for larger images.

4. **CORS**: Make sure your Appwrite project has the appropriate CORS settings to allow requests from your UI domain.

## Troubleshooting

- Check function logs in the Appwrite console for any errors
- Ensure all dependencies are correctly listed in the requirements.txt file
- Verify that your function has the necessary permissions to access any external services

## Local Testing

You can test the function locally before deploying:

```bash
cd appwrite/functions/image-processor
pip install -r requirements.txt
python -c "import src.index as module; print(dir(module))"
