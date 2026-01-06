"""
OpenAPI Spec Cleaner and Splitter

This tool reads milky.openapi.json and:
1. Cleans unnecessary metadata (keeps only essential fields for SDK generation)
2. Splits API endpoints into separate files under openapi_split/paths/
3. Splits schemas into separate files under openapi_split/schemas/
"""

import json
from pathlib import Path


def clean_schema(schema: dict) -> dict:
    """Remove unnecessary fields from a schema definition."""
    # Fields to remove (not needed for SDK generation)
    remove_fields = ["$id", "id", "scalarType"]
    
    if isinstance(schema, dict):
        cleaned = {}
        for key, value in schema.items():
            if key in remove_fields:
                continue
            cleaned[key] = clean_schema(value)
        return cleaned
    elif isinstance(schema, list):
        return [clean_schema(item) for item in schema]
    else:
        return schema


def main():
    input_file = Path(__file__).parent / "milky.openapi.json"
    output_dir = Path(__file__).parent / "openapi_split"
    
    # Create output directories
    schemas_dir = output_dir / "schemas"
    paths_dir = output_dir / "paths"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    paths_dir.mkdir(parents=True, exist_ok=True)
    
    # Load the OpenAPI spec
    with open(input_file, "r", encoding="utf-8") as f:
        spec = json.load(f)
    
    # Extract and save schemas
    schemas = spec.get("components", {}).get("schemas", {})
    print(f"Found {len(schemas)} schemas")
    
    for schema_name, schema_def in schemas.items():
        cleaned = clean_schema(schema_def)
        schema_file = schemas_dir / f"{schema_name}.json"
        with open(schema_file, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)
        print(f"  -> {schema_file.name}")
    
    # Extract and save paths (API endpoints)
    paths = spec.get("paths", {})
    print(f"\nFound {len(paths)} API endpoints")
    
    for path, path_def in paths.items():
        # Create a clean filename from the path
        # e.g., /api/get_login_info -> get_login_info.json
        filename = path.replace("/api/", "").replace("/", "_") + ".json"
        if filename.startswith("_"):
            filename = filename[1:]
        
        # Extract operation info and clean it
        cleaned_path = {}
        for method, operation in path_def.items():
            cleaned_op = {
                "summary": operation.get("summary", ""),
                "operationId": operation.get("operationId", ""),
                "tags": operation.get("tags", []),
            }
            
            # Extract request body schema reference
            request_body = operation.get("requestBody", {})
            if request_body:
                content = request_body.get("content", {}).get("application/json", {})
                schema_ref = content.get("schema", {}).get("$ref", "")
                if schema_ref:
                    cleaned_op["requestSchema"] = schema_ref.split("/")[-1]
            
            # Extract response schema reference
            responses = operation.get("responses", {}).get("200", {})
            if responses:
                content = responses.get("content", {}).get("application/json", {})
                schema = content.get("schema", {})
                # Handle allOf with ApiResponse + data
                if "allOf" in schema:
                    for item in schema["allOf"]:
                        if "properties" in item:
                            data_ref = item["properties"].get("data", {}).get("$ref", "")
                            if data_ref:
                                cleaned_op["responseSchema"] = data_ref.split("/")[-1]
            
            cleaned_path[method] = cleaned_op
        
        path_file = paths_dir / filename
        with open(path_file, "w", encoding="utf-8") as f:
            json.dump({"path": path, **cleaned_path}, f, ensure_ascii=False, indent=2)
        print(f"  -> {path_file.name}")
    
    # Create a summary index file
    index = {
        "info": {
            "title": spec.get("info", {}).get("title", ""),
            "version": spec.get("info", {}).get("version", ""),
            "description": spec.get("info", {}).get("description", ""),
        },
        "schemas": list(schemas.keys()),
        "endpoints": [
            {
                "path": path,
                "operationId": list(ops.values())[0].get("operationId", "") if ops else "",
                "summary": list(ops.values())[0].get("summary", "") if ops else "",
            }
            for path, ops in paths.items()
        ],
    }
    
    index_file = output_dir / "index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"\n-> Created index: {index_file}")
    
    print(f"\nDone! Output directory: {output_dir}")


if __name__ == "__main__":
    main()
