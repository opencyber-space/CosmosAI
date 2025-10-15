
import os
import json
import requests
import random
import time
import yaml

def get_config():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    gemini_api_key = config.get('gemini_api_key')
    if "YOUR_GEMINI_API_KEY_HERE" == gemini_api_key:
        gemini_api_key = os.environ.get('GEMINI_API_KEY',"")
        if gemini_api_key == "":
            print("❌ Please set a valid Gemini API key in config.yaml or GEMINI_API_KEY env variable.")
            exit(1)
    print(f"Using Gemini API Key: {'set' if gemini_api_key else 'not set'}")
    questions_file = config.get('questions_file', 'questions.jsonl')
    reuse = config.get('reuse_questions_file', True)
    users_per_hour = config['crowd_config']['users_per_hour']
    sessions_per_block = config['user_config']['sessions_per_block']
    requests_per_hour_per_session = config['user_config']['requests_per_hour_per_session']
    duration_hours = config['test_config']['duration_hours']
    blocks = config['blocks']
    N = users_per_hour * sessions_per_block * requests_per_hour_per_session * duration_hours
    return gemini_api_key, questions_file, reuse, N, list(blocks.keys())

def fetch_gemini_questions(api_key, questions_file, count):
    topics = ["sports", "math", "science", "history", "general knowledge", "flask", "django", "python programming", "web development", "machine learning"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    written = 0
    with open(questions_file, 'a') as f:
        for cnt in range(count):
            topic = random.choice(topics)
            prompt = f"Give me a unique, non-trivial, open-ended {topic} question suitable for an LLM benchmark. Do not repeat previous questions. Keep Question within 128 tokens."
            data = {
                "contents": [
                    {"role": "user", "parts": [{"text": prompt}]}
                ],
                "generationConfig": {
                    "maxOutputTokens": 128,
                    "temperature": 0.7
                }
            }
            try:
                resp = requests.post(url, headers=headers, json=data, timeout=60)
            except Exception as e:
                print(f"[ERROR] Request failed at count {cnt}: {e}")
                continue
            if resp.status_code != 200:
                print(f"[ERROR] Gemini API returned status {resp.status_code} at count {cnt}. Response: {resp.text}")
                continue
            try:
                result = resp.json()
                if cnt < 3:
                    print(f"[DEBUG] Gemini API response at count {cnt}: {json.dumps(result)[:500]}")
                q = result["candidates"][0]["content"]["parts"][0]["text"]
                print(cnt, q)
                f.write(json.dumps({"question": q.strip(), "used_blocks": []}) + '\n')
                f.flush()
                written += 1
            except Exception as e:
                print(f"[ERROR] Failed to parse response at count {cnt}: {e}. Raw: {resp.text}")
                continue
            time.sleep(0.5)
    print(f"Total new questions written: {written}")

def main():
    api_key, questions_file, reuse, N, block_ids = get_config()
    existing = 0
    if os.path.exists(questions_file) and reuse:
        with open(questions_file, 'r') as f:
            existing = sum(1 for _ in f)
    needed = N - existing
    if needed > 0:
        print(f"Fetching {needed} new questions from Gemini...")
        fetch_gemini_questions(api_key, questions_file, needed)
    else:
        print(f"Questions file already has {existing} questions.")
    print(f"Total questions available: {max(existing, N)}")

if __name__ == '__main__':
    main()