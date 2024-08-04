import subprocess
import json
import os
import sys
from tqdm import tqdm

def run_openai_script(directory, prompt_file, api_keys_file, failed_log_file):
    print("Downloading images...")
    result = subprocess.run([
        'python', 'openai.py',
        '--directory', directory,
        '--prompt_file', prompt_file,
        '--api_keys_file', api_keys_file,
        '--failed_log_file', failed_log_file
    ], capture_output=True, text=True, encoding='utf-8')
    if result.returncode == 0:
        print("Download completed.")
    else:
        print("Download failed.")
    return result.returncode == 0

def read_failed_images(failed_log_file):
    if not os.path.exists(failed_log_file):
        return []

    print("Reading list of failed images...")
    with open(failed_log_file, 'r', encoding='utf-8') as file:
        failed_images = [line.strip() for line in file]
    print(f"Found {len(failed_images)} failed images.")
    return failed_images

def merge_jsonl_files(file1, file2, output_file):
    print("Merging JSONL files...")
    data = {}
    def load_jsonl(file):
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    record_id = str(record['id']).strip('"')
                    if record_id not in data:
                        data[record_id] = record
                    else:
                        data[record_id].update(record)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from file {file}: {e}")
    load_jsonl(file1)
    load_jsonl(file2)
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in data.values():
            json.dump(record, f)
            f.write('\n')
    print(f"Successfully merged files into {output_file}")

def read_existing_data(jsonl_file):
    print("Checking existing data...")
    processed_ids = set()
    if os.path.exists(jsonl_file):
        with open(jsonl_file, 'r', encoding='utf-8') as file:
            for line in file:
                try:
                    record = json.loads(line)
                    processed_ids.add(record['id'])
                except json.JSONDecodeError:
                    continue
    print(f"Loaded {len(processed_ids)} previously processed records.")
    return processed_ids

def main(directory, prompt_file, api_keys_file):
    output_file = f'Data/{os.path.basename(directory)}_label.jsonl'
    failed_log_file = os.path.splitext(output_file)[0] + "_failed.txt"
    merged_output_file = f'result/{os.path.basename(directory)}.jsonl'

    # Ensure the result directory exists
    os.makedirs('result', exist_ok=True)

    # Read existing data to avoid reprocessing
    processed_ids = read_existing_data(output_file)

    while True:
        print("Starting image processing cycle...")
        success = run_openai_script(directory, prompt_file, api_keys_file, failed_log_file)
        if success:
            print("All images processed successfully.")
            break

        failed_images = read_failed_images(failed_log_file)
        if not failed_images:
            print("No failed images left to process.")
            break

        print(f"Retrying {len(failed_images)} failed images...")
        with open(failed_log_file, 'w', encoding='utf-8') as file:
            for image in tqdm(failed_images, desc="Retrying failed images"):
                if image not in processed_ids:
                    file.write(image + '\n')

    merge_jsonl_files(f'Data/{os.path.basename(directory)}.jsonl', output_file, merged_output_file)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python image_processing_pipeline.py <directory> <prompt_file> <api_keys_file>")
        sys.exit(1)

    directory = sys.argv[1]
    prompt_file = sys.argv[2]
    api_keys_file = sys.argv[3]

    main(directory, prompt_file, api_keys_file)
