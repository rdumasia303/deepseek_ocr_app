import base64
import re
import httpx
from mimetypes import guess_type

# Function to encode a local image into data URL
def local_image_to_data_url(image_path):
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'  # Default MIME type if none is found

    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')

    # Construct the data URL
    return f"data:{mime_type};base64,{base64_encoded_data}"

# Function to decode the data URL and return the image data (not saving to file)
def data_url_to_image(data_url):
    # Extract the base64 string by removing the "data:image/*;base64," part
    match = re.match(r"^data:(.*?);base64,(.*)$", data_url)
    if not match:
        raise ValueError("Invalid data URL format")

    # The second capture group is the base64 string
    base64_data = match.group(2)

    # Decode the base64 string into binary data
    image_data = base64.b64decode(base64_data)

    # Return the binary image data
    return image_data

# Function to send image data to the OCR API and print the result
async def send_image_to_ocr_api(image_binary_data):
    url = "http://localhost:3000/api/ocr"  # Replace with your FastAPI server URL
    
    # Prepare form data to send to the API
    files = {
        'image': ('image.png', image_binary_data, 'image/png'),  # Send image data as a file
    }
    
    # Correctly passing the other fields as form data (not in 'files')
    form_data = {
        'mode': 'describe',
        'base_size': 1024,
        'image_size': 640,
        'crop_mode': True,
    }
    
    timeout = httpx.Timeout(30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(url, files=files, data=form_data)
            response_data = response.json()

            if response.status_code == 200:
                print("OCR Inference Result:")
                print(f"Success: {response_data.get('success')}")
                print(f"Extracted Text: {response_data.get('text')}")
                print(f"Raw Text: {response_data.get('raw_text')}")
                print(f"Boxes: {response_data.get('boxes')}")
            else:
                print(f"Error: {response_data.get('detail')}")
        except httpx.ReadTimeout:
            print("Request timed out. The server may be taking too long to respond.")
        except Exception as e:
            print(f"An error occurred: {e}")



# Example usage
image_path = 'assets/multi-bird.png'  # Replace with your local image path
data_url = local_image_to_data_url(image_path)

# Now, decode the data URL and get the image binary data
image_binary_data = data_url_to_image(data_url)

# Call the OCR API with the image data
import asyncio
asyncio.run(send_image_to_ocr_api(image_binary_data))

# Optionally, save the binary image data to a file
output_image_path = 'restored_image.jpg'
with open(output_image_path, 'wb') as image_file:
    image_file.write(image_binary_data)

print(f"Image restored and saved at: {output_image_path}")
