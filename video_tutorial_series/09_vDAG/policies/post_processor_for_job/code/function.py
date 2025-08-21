import subprocess
import logging, json
import requests
import os,sys
import re
from typing import Dict
import shutil
import zipfile
import time
from markdown_it import MarkdownIt

class AIOSv1PolicyRule:
    def __init__(self, rule_id, settings, parameters):
        """
        settings = {
            
        }
        parameters = {
            
        }
        """
        self.settings = settings
        self.parameters = parameters
        self.rule_id = rule_id
        self.policy_db_url = os.getenv("POLICY_DB_URL", "http://MANAGEMENTMASTER:30102")
        if not self.policy_db_url:
            logging.error("POLICY_DB_URL environment variable is not set.")
            raise ValueError("POLICY_DB_URL environment variable is required.")

        self.job_policy_name = self.settings.get("job_policy_name", "alerter:1.0.0-stable")
        self.classification_patterns = self.settings.get("classification_patterns",[
            "(?:\\*\\*)?Classification:(?:\\*\\*)?\\s*Alertable",
            "(?:\\*\\*)?Classification:(?:\\*\\*)?\\s*Alert",
            "(?:\\*\\*)?Classification:(?:\\*\\*)?\\s*`Alertable",
            "(?:\\*\\*)?Classification:(?:\\*\\*)?\\s*`Alert"
        ])

        self.zip_store_url = self.settings.get("zip_store_url", "http://MANAGEMENTMASTER:32555")
        self.base_uri = self.settings.get("BASE_URI", "http://10.138.0.5:5000/receive")
        self.pusher_url = self.settings.get("pusher_url", "http://POLICYSTORESERVER:30186/upload")
        self.policy_registration_url = self.settings.get("policy_registration_url", "http://MANAGEMENTMASTER:30102/policy")
        self.job_deployment_url = self.settings.get("job_deployment_url", "http://MANAGEMENTMASTER:30102/jobs/submit/executor-001")

        if not self.job_policy_name or not self.zip_store_url or not self.base_uri or not self.pusher_url or not self.policy_registration_url or not self.job_deployment_url:
            logging.error("One or more required settings are not set.")
            raise ValueError("All required settings must be provided.")


    def _process_reply(self, reply):
        # Initialize variables
        classification_line = None
        summary_text = None
        python_code = None

        # 1. Extract the full Classification line (MODIFIED PART)
        # This pattern matches the literal string including the bold markdown asterisks.
        # Note: Asterisks are special characters in regex, so they are "escaped" with a backslash (\).
        llm_response = reply  # Assuming 'reply' is the LLM response string
        logging.info("llm_response: %s", llm_response)
        logging.info("classification_patterns: %s", self.classification_patterns)
        classification = False
        for pattern in self.classification_patterns:
            logging.info("Checking pattern: %s", pattern)
            if re.search(pattern, llm_response):
                classification = True
                break

        # 2. Extract the Summary text (no change)
        summary_pattern = r"Summary:\s*(.*?)(?=\n\n###|$)"
        summary_match = re.search(summary_pattern, llm_response, re.DOTALL)
        if summary_match:
            summary_text = summary_match.group(1).strip()

        # 3. Extract the Python code (no change)
        code_pattern = r"```python\n(.*)```"
        code_match = re.search(code_pattern, llm_response, re.DOTALL)
        if code_match:
            python_code = code_match.group(1).strip()

        return classification, summary_text, python_code

    def _parse_llm_response(self, markdown_text: str) -> tuple[Dict[str, str], bool, str]:
        """
        Parses an LLM response to extract named code blocks.

        This function finds sections formatted with a markdown heading like
        '### **filename.ext**' followed by a fenced code block and extracts
        the filename and the code content.

        Args:
            response_text: The string containing the LLM response.

        Returns:
            A tuple containing:
                - A dictionary where keys are the filenames and values are the corresponding code content,
                - A boolean indicating classification,
                - A summary string.
        """
        try:
            
            #markdown_text = response_text  # Assuming 'reply' is the LLM response string
            #print("llm_response:", markdown_text)
            logging.info("classification_patterns: %s", self.classification_patterns)
            classification = False
            for pattern in self.classification_patterns:
                logging.info("Checking pattern: %s", pattern)
                if re.search(pattern, markdown_text, re.IGNORECASE):
                    classification = True
                    break

            # 2. Extract the Summary text with multiple patterns
            summary_patterns = [
                r"\*\*Summary:\*\*\s*(.*?)(?=\n\n|---|\n###|$)",  # Matches **Summary:** format, stops at \n\n, ---, \n###, or end
                r"Summary:\s*(.*?)(?=\n\n|---|\n###|$)"           # Matches Summary: format, stops at \n\n, ---, \n###, or end
            ]
            
            summary_text = ""
            for pattern in summary_patterns:
                summary_match = re.search(pattern, markdown_text, re.DOTALL)
                if summary_match:
                    summary_text = summary_match.group(1).strip()
                    # Clean the summary text - remove trailing --- and extra whitespace
                    summary_text = re.sub(r'\s*---\s*$', '', summary_text).strip()
                    # Remove any trailing newlines and whitespace
                    summary_text = summary_text.rstrip('\n\r\t ')
                    break  # Use the first match found
            
            # This regex looks for a word with a specific file extension.
            # It will find 'file.py' inside '(**file.py**)' or '(A. `script.py`)'
            filename_pattern = re.compile(
                # Capture Group 1: The full filename
                r"([\w-]+\.(?:py|json|sh|js|cpp|txt|bash)\b)"
            )
            
            md = MarkdownIt()
            tokens = md.parse(markdown_text)

            headers: List[Tuple[int, str]] = []
            code_blocks: List[Tuple[int, str]] = []

            # Step 1: Reliably find all headers and code blocks using the library
            for i, token in enumerate(tokens):
                if token.type == 'heading_open':
                    line_num = token.map[0] if token.map else -1
                    heading_text = tokens[i + 1].content
                    headers.append((line_num, heading_text))
                elif token.type == 'fence':
                    line_num = token.map[0] if token.map else -1
                    code_content = token.content
                    code_blocks.append((line_num, code_content))

            # Step 2: Associate each code block with its closest preceding header
            extracted_files = {}
            for code_line, code_content in code_blocks:
                closest_header_line = -1
                associated_header_text = ""
                for header_line, header_text in headers:
                    if header_line < code_line and header_line > closest_header_line:
                        closest_header_line = header_line
                        associated_header_text = header_text

                # Step 3: Use the new, smarter regex to find the filename
                if associated_header_text:
                    match = filename_pattern.search(associated_header_text)
                    if match:
                        # The filename is the first (and only) captured group
                        filename = match.group(1)
                        extracted_files[filename] = code_content.strip()

            return extracted_files, classification, summary_text
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            infoTolog = "ERROR:: code error : "+str(exc_type)+" "+ str(fname)+" "+ str(exc_tb.tb_lineno)+" "+str(e)
            logging.error(infoTolog)
            return {}, False, ""

    def _do_function_call(self, reply):
        """
        Calls the function with the given reply.
        """
        url = f"{self.policy_db_url}/function/call_function/{self.function_name}"
        headers = {"Content-Type": "application/json"}
        try:
            classification, summary_text, python_code = self._process_reply(reply)
            if not classification:
                logging.error("Classification not found in the reply.")
                return {"result": [], "reason": "Classification not found in the reply."}
            
            data = json.dumps({"string_for_eval": python_code, "summary": summary_text})
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            output = response.json()
            if "success" in output and output["success"]:
                data = output.get("data", {})
                if not data:
                    logging.error("Expected 'data' to be a non-empty dictionary.")
                    return {"error": "Invalid response format"}
                if "reason" in data and data["reason"] == "Success":
                    result = data.get("result", {})
                    if result["reason"] != "Success":
                        logging.error(f"Function Eval failed: {result.get('reason', 'Unknown error')}")
                        return {"error": result.get("reason", "Unknown error")}
                    return {"result": result, "reason": "Success"}
                else:
                    logging.error(f"Function call failed: {data.get('reason', 'Unknown error')}")
                    return {"error": data.get("reason", "Unknown error")}
            else:
                logging.error(f"Function call failed: {output}")
                return {"error": output} 
        except requests.RequestException as e:
            logging.error(f"Error calling function: {e}")
            return {"error": str(e)}
    def _do_clean_up(self, policy_name_registered):
        """
        Cleans up the job by deleting the job and unregistering the policy.
        """
        #return {"status": "success", "message": "Cleanup completed successfully"}
        cleanup_errors = []
        try:
            # 2. Unregister the policy
            if policy_name_registered:
                unregister_url = f"{self.policy_registration_url}/{policy_name_registered}"
                response = requests.delete(unregister_url)
                if response.status_code == 200:
                    logging.info(f"Successfully unregistered policy: {policy_name_registered}")
                else:
                    error_msg = f"Failed to unregister policy: {policy_name_registered}. Status code: {response.status_code}, Response: {response.text}"
                    logging.warning(error_msg)
                    cleanup_errors.append(error_msg)
            else:
                logging.warning("No policy name provided for cleanup")
                
        except requests.RequestException as e:
            error_msg = f"Error unregistering policy {policy_name_registerd}: {e}"
            logging.error(error_msg)
            cleanup_errors.append(error_msg)
        
        # 3. Clean up local files

        try:
            files_to_clean = ["registration.json","alerter.zip", "pusher.sh", "register.sh", "deploy_job.sh"]
            for filename in files_to_clean:
                file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logging.info(f"Deleted local file: {filename}")
            
            # Remove the code directory
            code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "code")
            if os.path.exists(code_dir):
                shutil.rmtree(code_dir)
                logging.info("Deleted code directory")
                
        except Exception as e:
            error_msg = f"Error cleaning up local files: {e}"
            logging.error(error_msg)
            cleanup_errors.append(error_msg)
        
        if cleanup_errors:
            return {"status": "partial_cleanup", "errors": cleanup_errors}
        else:
            return {"status": "success", "message": "Cleanup completed successfully"}

    def _process_reply(self, llm_response):
        """
        Processes the LLM response to extract classification, summary, and code.
        """
        policy_name_registered = ""
        try:
            # Initialize variables
            classification = None
            summary_text = None
            python_code = None

            # 1. Extract the full Classification line (MODIFIED PART)
            # This pattern matches the literal string including the bold markdown asterisks.
            # Note: Asterisks are special characters in regex, so they are "escaped" with a backslash (\).

            parsed_files, classification, summary_text = self._parse_llm_response(llm_response)

            logging.info(classification)
            logging.info(summary_text)
            logging.info(parsed_files)

            if not classification:
                logging.error("Classification not found in the reply.")
                return {"result": [], "reason": "Classification pattern not found in the reply."}
            # Print the extracted content for verification
            json_file_path = ""
            pusher_script_path = ""
            register_script_path = ""
            deploy_job_script_path = ""
            python_file_path = ""

            job_id = ""

            for filename, content in parsed_files.items():
                logging.info(f"--- Content of {filename} ---")
                logging.info(content)
                logging.info("-" * (len(filename) + 16))
                if filename.endswith(".py"):
                    python_code = content.strip()
                    if not python_code:
                        logging.error(f"Python code in {filename} is empty.")
                        self._do_clean_up(policy_name_registered)
                        return {"result": [], "reason": f"Python code in {filename} is empty."}
                    mkdir_path = os.path.dirname(os.path.abspath(__file__))+ "/code"
                    if not os.path.exists(mkdir_path):
                        os.makedirs(mkdir_path)
                    else:
                        shutil.rmtree(mkdir_path)
                        os.makedirs(mkdir_path)
                    # Replace destination_url assignment in python_code
                    python_code = re.sub(
                        r'destination_url\s*=\s*self\.settings\.BASE_URI',
                        f'destination_url = self.settings.get("BASE_URI", "{self.base_uri}")',
                        python_code
                    )

                    python_file_path = os.path.join(mkdir_path, "function.py")
                    with open(python_file_path, "w") as f:
                        f.write(python_code)

                    # Zip the contents of mkdir_path into alerter.zip
                    zip_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alerter.zip")
                    parent_dir = os.path.dirname(mkdir_path)  # Get parent of code directory
                    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
                        for root, dirs, files in os.walk(mkdir_path):
                            for file in files:
                                if file != "alerter.zip":  # Avoid zipping the zip itself
                                    file_path = os.path.join(root, file)
                                    # Use relative path from parent directory to preserve 'code' folder name
                                    arcname = os.path.relpath(file_path, parent_dir)
                                    zipf.write(file_path, arcname)

                elif filename.endswith(".json"):
                    json_content = content.strip()
                    if not json_content:
                        logging.error(f"JSON content in {filename} is empty.")
                        self._do_clean_up(policy_name_registered)
                        return {"result": [], "reason": f"JSON content in {filename} is empty."}
                    try:
                        json_data = json.loads(json_content)
                        json_data["code"] =  self.zip_store_url+"/"+"alerter.zip"
                        json_data["policy_settings"]["BASE_URI"] =  self.base_uri
                        policy_name_registered = json_data["name"]+":"+json_data["version"]+'-'+ json_data["release_tag"]
                        # Write the JSON content to a file with the extracted filename
                        json_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
                        with open(json_file_path, "w") as f:
                            f.write(json.dumps(json_data))
                    except json.JSONDecodeError as e:
                        logging.error(f"Invalid JSON in {filename}: {e}")
                        self._do_clean_up(policy_name_registered)
                        return {"result": [], "reason": f"Invalid JSON in {filename}: {e}"}

                elif "pusher.sh" in filename or "pusher" in filename:
                    pusher_script = content.strip()
                    if not pusher_script:
                        logging.error(f"Pusher script in {filename} is empty.")
                        self._do_clean_up(policy_name_registered)
                        return {"result": [], "reason": f"Pusher script in {filename} is empty."}
                    # Replace ENDPOINT in the pusher script with the actual pusher_url
                    pusher_script = re.sub(
                        r'ENDPOINT="http://YOUR_CONTENT_STORE_IP:PORT/upload"',
                        f'ENDPOINT="{self.pusher_url}"',
                        pusher_script
                    )
                    # Replace FILE_PATH="alerter.zip" with FILE_PATH="./alerter.zip"
                    zip_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alerter.zip")
                    pusher_script = re.sub(
                        r'FILE_PATH="alerter\.zip"',
                        f'FILE_PATH="{zip_file_path}"',
                        pusher_script
                    )
                    # Replace $ENDPOINT only in the curl command line
                    pusher_lines = pusher_script.splitlines()
                    for i, line in enumerate(pusher_lines):
                        if "curl" in line and "$ENDPOINT" in line:
                            # Replace $ENDPOINT with '-F "path=." $ENDPOINT' only in the curl command line
                            pusher_lines[i] = line.replace('$ENDPOINT', '-F "path=." $ENDPOINT')
                    pusher_script = "\n".join(pusher_lines)
                    pusher_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pusher.sh")
                    logging.info(f"Writing pusher script to {pusher_script_path}")
                    logging.info(f"Pusher script content: {pusher_script}")
                    with open(pusher_script_path, "w") as f:
                        f.write(pusher_script)
                    os.chmod(pusher_script_path, 0o755)
                elif "register.sh" in filename or "register" in filename:
                    register_script = content.strip()
                    if not register_script:
                        logging.error(f"Register script in {filename} is empty.")
                        self._do_clean_up(policy_name_registered)
                        return {"result": [], "reason": f"Register script in {filename} is empty."}
                    # Replace ENDPOINT in the register script with the actual policy_registration_url
                    register_script = re.sub(
                        r'ENDPOINT="http://YOUR_REGISTRY_IP:PORT/policy"',
                        f'ENDPOINT="{self.policy_registration_url}"',
                        register_script
                    )
                    json_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registration.json")
                    # Replace the curl line to use the correct json_file_path
                    register_script = re.sub(
                        r'curl\s+-X\s+POST\s+-H\s+"Content-Type:\s*application/json"\s+--data\s+@\.\/registration\.json\s+\$ENDPOINT',
                        f'curl -X POST -H "Content-Type: application/json" --data @{json_file_path} $ENDPOINT',
                        register_script
                    )
                    register_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "register.sh")
                    logging.info(f"Writing register script to {register_script_path}")
                    logging.info(f"Register script content: {register_script}")
                    with open(register_script_path, "w") as f:
                        f.write(register_script)
                    os.chmod(register_script_path, 0o755)
                elif "deploy_job.sh" in filename or "deploy" in filename:
                    deploy_job_script = content.strip()
                    if not deploy_job_script:
                        logging.error(f"Deploy job script in {filename} is empty.")
                        self._do_clean_up(policy_name_registered)
                        return {"result": [], "reason": f"Deploy job script in {filename} is empty."}
                    # Replace ENDPOINT in the deploy job script with the actual job_deployment_url
                    deploy_job_script = re.sub(
                        r'ENDPOINT="http://YOUR_JOB_API_IP:PORT/jobs/submit/executor-001"',
                        f'ENDPOINT="{self.job_deployment_url}"',
                        deploy_job_script
                    )
                    # Replace the summary value in the deploy job script with the extracted summary_text
                    # Replace the summary value in the deploy job script with the extracted summary_text
                    # Remove all double quotes and single quotes from summary_text before substitution
                    clean_summary = summary_text.replace('"', '').replace("'", "")
                    deploy_job_script = re.sub(
                        r'("summary":\s*")[^"]*(")',
                        r'\1' + clean_summary + r'\2',
                        deploy_job_script
                    )

                    #print("1111deploy_job_script:", deploy_job_script)

                    # Fix: Handle JSON escaping properly in curl command
                    def fix_curl_json(script_content):
                        lines = script_content.split('\n')
                        fixed_lines = []
                        in_json_block = False
                        
                        for line in lines:
                            if '-d "{' in line or "-d '{" in line:
                                # Start of JSON block - convert to single quotes wrapper
                                line = re.sub(r'-d\s*"', "-d '", line)
                                in_json_block = True
                            elif in_json_block and (line.strip().endswith("}'") or line.strip().endswith('}"')):
                                # End of JSON block - ensure it ends with single quote
                                if line.strip().endswith("}'"):
                                    line = line.strip()
                                else:
                                    line = line.rstrip('}"') + "}'"
                                in_json_block = False
                            
                            # Inside JSON block, keep valid JSON syntax (double quotes for properties)
                            if in_json_block:
                                # Handle summary line specially (escape single quotes in content)
                                if '"summary":' in line:
                                    # Extract the summary value and escape single quotes
                                    match = re.search(r'"summary":\s*"([^"]*)"', line)
                                    if match:
                                        summary_content = match.group(1)
                                        # Escape single quotes in summary content for shell
                                        escaped_content = summary_content.replace("'", "\\'")
                                        line = f'      "summary": "{escaped_content}"'
                                # Keep all other JSON properties unchanged (valid JSON with double quotes)
        
                            fixed_lines.append(line)
                        
                        return '\n'.join(fixed_lines)

                    # Apply the fix
                    deploy_job_script = fix_curl_json(deploy_job_script)
                    deploy_job_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deploy_job.sh")
                    logging.info(f"Writing deploy job script to {deploy_job_script_path}")
                    logging.info(f"Deploy job script content: {deploy_job_script}")
                    with open(deploy_job_script_path, "w") as f:
                        f.write(deploy_job_script)
                    os.chmod(deploy_job_script_path, 0o755)

                

            # Print the contents of all generated files if their paths are set
            for file_path in [python_file_path, json_file_path, pusher_script_path, register_script_path, deploy_job_script_path]:
                if file_path and os.path.exists(file_path):
                    logging.info(f"\n--- Content of {os.path.basename(file_path)} ---")
                    with open(file_path, "r") as f:
                        logging.info(f.read())
                    logging.info("-" * (len(os.path.basename(file_path)) + 16))

            #let us run the pusher script to upload the zip file
            try:
                if pusher_script_path:
                    logging.info(f"Running pusher script: {pusher_script_path}")
                    subprocess.run([pusher_script_path], check=True)
                else:
                    logging.error("Pusher script path is not set.")
                    self._do_clean_up(policy_name_registered)
                    return {"result": [], "reason": "Pusher script path is not set."}
            except subprocess.CalledProcessError as e:
                logging.error(f"Error running pusher script: {e}")
                self._do_clean_up(policy_name_registered)
                return {"result": [], "reason": f"Error running pusher script: {str(e)}"}

            #let us run the register script to register the policy
            try:
                if register_script_path:
                    logging.info(f"Running register script: {register_script_path}")
                    subprocess.run([register_script_path], check=True)
                else:
                    logging.error("Register script path is not set.")
                    self._do_clean_up(policy_name_registered)
                    return {"result": [], "reason": "Register script path is not set."}
            except subprocess.CalledProcessError as e:
                logging.error(f"Error running register script: {e}")
                self._do_clean_up(policy_name_registered)
                return {"result": [], "reason": f"Error running register script: {str(e)}"}

            #let us run the deploy job script to deploy the job
            try:
                if deploy_job_script_path:
                    logging.info(f"Running deploy job script: {deploy_job_script_path}")
                    # Run the deploy job script and capture its output
                    result = subprocess.run([deploy_job_script_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    output = result.stdout.strip()
                    logging.info(f"Deploy job script output: {output}")

                    # Try to find a JSON object in the output
                    try:
                        # Find the first JSON object in the output
                        match = re.search(r'(\{.*"success"\s*:\s*true.*\})', output)
                        if match:
                            job_info = json.loads(match.group(1))
                            job_id = job_info.get("job_id")
                            logging.info(f"Job deployed successfully. job_id: {job_id}")
                        else:
                            logging.warning("No successful job deployment JSON found in output.")
                    except Exception as e:
                        logging.error(f"Error parsing deploy job script output: {e}")
                else:
                    logging.error("Deploy job script path is not set.")
                    self._do_clean_up(policy_name_registered)
                    return {"result": [], "reason": "Deploy job script path is not set."}
            except subprocess.CalledProcessError as e:
                logging.error(f"Error running deploy job script: {e}")
                self._do_clean_up(policy_name_registered)
                return {"result": [], "reason": f"Error running deploy job script: {str(e)}"}

            if not job_id:
                logging.error("Job ID could not be received for deployed job.")
                self._do_clean_up(policy_name_registered)
                return {"result": [], "reason": "Job ID could not be received for deployed job."}

            # Poll the job status endpoint until a successful response is received
            job_done = False
            job_status_url = self.job_deployment_url.split('/jobs/')[0] + f"/jobs/{job_id}"
            while True:
                try:
                    response = requests.get(job_status_url)
                    if response.status_code == 200:
                        resp_json = response.json()
                        if resp_json.get("success"):
                            logging.info(f"Job completed successfully: {resp_json}")
                            job_done = True
                            break
                    time.sleep(2)  # Wait before polling again
                            
                    # If not successful, wait and poll again
                except Exception as e:
                    logging.warning(f"Error polling job status: {e}")
                    time.sleep(2)
            self._do_clean_up(policy_name_registered)
            if job_done:
                return {"result": response, "reason": "Success"}
            else:
                logging.error("Job did not complete successfully.")
                return {"result": [], "reason": "Job did not complete successfully."}

        except Exception as e:
            logging.error(f"Error in job deployment: {e}")
            if policy_name_registered:
                self._do_clean_up(policy_name_registered)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            infoTolog = "ERROR:: code error : "+str(exc_type)+" "+ str(fname)+" "+ str(exc_tb.tb_lineno)+" "+str(e)
            logging.error(infoTolog)
            return {"result": [], "reason": "Error in job deployment."}

    def eval(self, parameters, input_data, context):
        try:
            logging.info(f"[policy-settings] {self.settings}")
            logging.info(f"[input-data] {input_data}")
            packet = input_data.get("packet", {})
            data = json.loads(packet.data)
            if not data:
                #return {"result": [], "reason": "input_data is empty", "input_data": input_data}
                return input_data
            if "reply" not in data:
                #return {"result": [], "reason": "reply missing in input_data", "input_data": input_data}
                return input_data
            reply = data["reply"]
            if not reply:
                #return {"result": [], "reason": "reply is empty in input_data", "input_data": input_data}
                return input_data
            logging.info(f"[reply] {reply}")
            response = self._process_reply(reply)
            if "reason" in response and response["reason"] != "Success":
                logging.error(f"Error in _process_reply: {response['reason']}")
                #return {"result": [], "reason": response["reason"], "input_data": input_data}
                return input_data
            logging.info(f"Success Processing [response] {response}")
            #return {"result": response.get("result", []), "reason": "success", "input_data": input_data}
            return input_data
        except Exception as e:
            logging.error(f"Error in eval: {e}")
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            infoTolog = "ERROR:: code error : "+str(exc_type)+" "+ str(fname)+" "+ str(exc_tb.tb_lineno)+" "+str(e)
            logging.error(infoTolog)
            #return {"result": [], "reason": "Error in eval", "input_data": input_data}
            return input_data
    def management(self, action: str, data: dict) -> dict:
        try:
            if action == "update":
                self.policy_db_url = data.get("POLICY_DB_URL", self.policy_db_url)
                self.function_name = data.get("function_name", self.function_name)
                
                return {"status": "success", "message": "Policy rule updated successfully"}

            else:
                return {"status": "error", "message": f"Unknown action '{action}'"}
        except Exception as e:
            logging.error(f"Error in management action '{action}': {e}")
            return {"status": "error", "message": f"Error occurred"}