import argparse
import base64
import requests
import os
import json
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def load_prompt(prompt_file):
    with open(prompt_file, 'r', encoding='utf-8') as file:
        return file.read()

def load_api_keys(api_keys_file):
    with open(api_keys_file, 'r') as file:
        return [line.strip() for line in file]

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_image(api_key, base64_image, prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    for attempt in range(1, 6):  # Retry up to 5 times
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            if 'choices' in response_data and response_data['choices']:
                content = response_data['choices'][0]['message']['content']
                return content
            else:
                raise ValueError("Response does not contain 'choices'")
        except requests.exceptions.RequestException as e:
            if response.status_code == 429:
                print(f"Rate limit exceeded, retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)
            else:
                print(f"Error processing image: {e}")
                break
        except (ValueError, KeyError) as e:
            print(f"Error processing image: {e}")
            break
    return None

def process_single_image(image_path, api_keys, request_counters, prompt):
    base64_image = encode_image(image_path)

    # Find the API key with the least requests or next in round-robin fashion
    key_index = min(request_counters, key=request_counters.get)
    api_key = api_keys[key_index]

    # Process the image
    result = process_image(api_key, base64_image, prompt)

    # Increment the request counter
    request_counters[key_index] += 1

    # If an API key reaches 30 requests, pause and reset its counter
    if request_counters[key_index] >= 30:
        print(f"Pausing for API key {key_index} after 30 requests...")
        time.sleep(2)  # Adjust the sleep time as needed
        request_counters[key_index] = 0  # Reset the counter

    return result, key_index

def normalize_id(id_value):
    return str(id_value).strip('"')

def process_directory(directory_path, prompt_file, api_keys_file, failed_log_file):
    # Load prompt and API keys
    prompt = load_prompt(prompt_file)
    api_keys = load_api_keys(api_keys_file)

    # Initialize request counters for each API key
    request_counters = {i: 0 for i in range(len(api_keys))}

    # File to log failed images
    output_file = os.path.join("Data", f"{os.path.basename(directory_path)}_label.jsonl")

    # Read already processed image IDs
    processed_images = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as file:
            for line in file:
                record = json.loads(line)
                processed_images.add(normalize_id(record['id']))

    # Read failed images
    failed_images = set()
    if os.path.exists(failed_log_file):
        with open(failed_log_file, 'r') as file:
            for line in file:
                failed_images.add(line.strip())

    # Collect all image paths
    all_images = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.endswith('.jpg')]

    # Filter images to be processed
    images_to_process = [img for img in all_images if os.path.basename(img).split('.jpg')[0] not in processed_images]

    if not images_to_process:
        print(f"No images to process in directory: {directory_path}")
        return

    with open(output_file, 'a') as file, open(failed_log_file, 'w') as failed_file, ThreadPoolExecutor(
            max_workers=3) as executor:  # Adjust max_workers as needed
        futures = {executor.submit(process_single_image, image_path, api_keys, request_counters, prompt): image_path for
                   image_path in images_to_process}

        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Images"):
            image_path = futures[future]
            image_id = normalize_id(os.path.basename(image_path).split('.jpg')[0])
            try:
                result, key_index = future.result()
                if result:
                    json_record = json.dumps({"id": image_id, "content": result})
                    file.write(json_record + "\n")
                else:
                    print(f"Failed to process image {image_id} with API key {key_index}")
                    failed_file.write(image_path + "\n")
            except Exception as e:
                print(f"Error processing image {image_id}: {e}")
                failed_file.write(image_path + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process images using OpenAI API.')
    parser.add_argument('--directory', type=str, required=True, help='Directory containing images to process.')
    parser.add_argument('--prompt_file', type=str, required=True, help='File containing the prompt.')
    parser.add_argument('--api_keys_file', type=str, required=True, help='File containing the OpenAI API keys.')
    parser.add_argument('--failed_log_file', type=str, required=True, help='File to log failed images.')

    args = parser.parse_args()
    process_directory(args.directory, args.prompt_file, args.api_keys_file, args.failed_log_file)
