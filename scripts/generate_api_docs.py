import urllib.request
import json
import os

url = "http://localhost:8000/openapi.json"
output_file = "/home/gol-d-roger/LioMonk/Projects /sara medICO/API_DOCUMENTATION.md"

try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = response.read()
        openapi = json.loads(data.decode('utf-8'))
    
    with open(output_file, "w") as f:
        f.write("# SaraMedico API Documentation\n\n")
        f.write("This document contains the expected inputs and outputs for all API endpoints in the SaraMedico Backend, compiled from the OpenAPI specification.\n\n")
        
        paths = openapi.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                f.write(f"## {method.upper()} {path}\n")
                f.write(f"**Summary**: {details.get('summary', 'No summary')}\n\n")
                
                # Parameters (Query, Path)
                parameters = details.get("parameters", [])
                if parameters:
                    f.write("### Parameters\n")
                    for param in parameters:
                        req_flag = " (Required)" if param.get('required') else ""
                        param_type = param.get("schema", {}).get("type", "string")
                        f.write(f"- `{param['name']}` ({param['in']}): {param_type}{req_flag}\n")
                    f.write("\n")
                
                # Request Body (Input)
                request_body = details.get("requestBody", {})
                if request_body:
                    f.write("### Expected Input (Request Body)\n")
                    content = request_body.get("content", {})
                    for content_type, content_details in content.items():
                        schema = content_details.get("schema", {})
                        ref = schema.get("$ref")
                        if ref:
                            model_name = ref.split("/")[-1]
                            f.write(f"- Content-Type: `{content_type}`\n- Schema: `{model_name}`\n")
                        else:
                            f.write(f"- Content-Type: `{content_type}`\n- Type: `{schema.get('type')}`\n")
                    f.write("\n")
                    
                # Responses (Output)
                responses = details.get("responses", {})
                if responses:
                    f.write("### Expected Output (Responses)\n")
                    for status_code, response_details in responses.items():
                        f.write(f"**Status {status_code}**\n")
                        content = response_details.get("content", {})
                        if content:
                            for content_type, content_details in content.items():
                                schema = content_details.get("schema", {})
                                ref = schema.get("$ref")
                                if ref:
                                    model_name = ref.split("/")[-1]
                                    f.write(f"- Content-Type: `{content_type}`\n- Schema: `{model_name}`\n")
                                else:
                                    # Fallback for inline schema types
                                    item_type = schema.get("type", "unknown")
                                    if item_type == "array" and "items" in schema and "$ref" in schema["items"]:
                                        model_name = schema["items"]["$ref"].split("/")[-1]
                                        f.write(f"- Content-Type: `{content_type}`\n- Schema: Array of `{model_name}`\n")
                                    else:
                                        f.write(f"- Content-Type: `{content_type}`\n- Type: `{item_type}`\n")
                        else:
                            f.write("- No content returned\n")
                    f.write("\n")
                
                f.write("---\n\n")
                
    print(f"✅ Generated API_DOCUMENTATION.md successfully at {output_file}!")
except Exception as e:
    print(f"❌ Error generating documentation: {e}")
