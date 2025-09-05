import json

def parse_and_display_json_log(file_path):
    """
    Parses a JSON log file to extract and display the sequence of tool calls
    and assistant responses in a readable format.

    Args:
        file_path (str): The path to the input JSON log file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' is not a valid JSON file.")
        return

    # The sequence of events is in the 'output' list
    execution_flow = data.get('response', {}).get('output', [])
    
    if not execution_flow:
        print("Could not find a valid execution flow in the file.")
        return

    # --- Display the parsed sequence ---
    print("=" * 80)
    print("                🤖 AI Assistant Execution Flow 🤖")
    print("=" * 80)
    
    call_counter = 0
    final_output = ""

    for event in execution_flow:
        event_type = event.get('type')

        # Process tool calls
        if event_type == 'mcp_call':
            call_counter += 1
            name = event.get('name', 'N/A')
            server = event.get('server_label', 'N/A')
            
            # Arguments and output are stored as JSON strings, so we parse them
            try:
                args = json.loads(event.get('arguments', '{}'))
            except (json.JSONDecodeError, TypeError):
                args = event.get('arguments', '{}') # Fallback to raw string

            try:
                output = json.loads(event.get('output', '""'))
            except (json.JSONDecodeError, TypeError):
                output = event.get('output', '""') # Fallback to raw string


            print(f"\n--- 📞 Call #{call_counter}: {name} on server '{server}' ---")
            print(f"  ▶️  Arguments: {args}")
            print(f"  ◀️  Output: {output}")
            print("-" * 60)
        
        # Process assistant messages
        elif event_type == 'message':
            # The text content is nested within the 'content' list
            content_list = event.get('content', [])
            if content_list and 'text' in content_list[0]:
                message_text = content_list[0]['text']
                print("\n--- 💬 Assistant Thought & Summary ---")
                print(message_text)
                final_output = message_text # Capture the last message as the final one

    # --- Display the final output separately ---
    if final_output:
        print("\n\n" + "=" * 80)
        print("                          ✅ FINAL OUTPUT ✅")
        print("=" * 80)
        print(final_output)

# --- Main execution ---
# Ensure the file 'final_response.txt' is in the same directory as the script
file_to_parse = 'final_response.txt'
parse_and_display_json_log(file_to_parse)