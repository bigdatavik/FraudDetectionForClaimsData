#!/usr/bin/env python3
"""
Quick setup script - runs all notebooks on interactive cluster
"""
import subprocess
import time
import json

PROFILE = "DEFAULT_azure"
CLUSTER_ID = "0304-162117-qgsi1x04"  # Field Eng Shared UC LTS Cluster
WORKSPACE_PATH = "/Workspace/Users/vik.malhotra@databricks.com/fraud_detection_setup"

notebooks = [
    "01_create_catalog_schema.py",
    "02_generate_sample_data.py",
    "03_uc_fraud_classify.py",
    "04_uc_fraud_extract.py",
    "05_uc_fraud_explain.py",
    "06_create_knowledge_base.py",
    "07_create_vector_index.py",
    "08_create_genie_space.py",
]

print("🚀 Running setup notebooks on cluster:", CLUSTER_ID)
print("=" * 60)

for i, notebook in enumerate(notebooks, 1):
    print(f"\n[{i}/{len(notebooks)}] Running: {notebook}")
    
    # Submit notebook run
    cmd = [
        "databricks", "jobs", "submit",
        "--profile", PROFILE,
        "--json", json.dumps({
            "run_name": f"fraud_setup_{notebook}",
            "existing_cluster_id": CLUSTER_ID,
            "notebook_task": {
                "notebook_path": f"{WORKSPACE_PATH}/{notebook}",
                "base_parameters": {}
            }
        })
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to submit: {result.stderr}")
        continue
    
    response = json.loads(result.stdout)
    run_id = response["run_id"]
    print(f"   Run ID: {run_id}")
    
    # Wait for completion
    while True:
        status_cmd = ["databricks", "jobs", "get-run", str(run_id), "--profile", PROFILE, "-o", "json"]
        status_result = subprocess.run(status_cmd, capture_output=True, text=True)
        
        if status_result.returncode == 0:
            run_info = json.loads(status_result.stdout)
            state = run_info["state"]["life_cycle_state"]
            
            if state in ["TERMINATED", "SKIPPED"]:
                result_state = run_info["state"].get("result_state", "UNKNOWN")
                if result_state == "SUCCESS":
                    print(f"   ✅ {notebook} completed successfully")
                    break
                else:
                    print(f"   ❌ {notebook} failed: {result_state}")
                    # Get error
                    output_cmd = ["databricks", "jobs", "get-run-output", str(run_id), "--profile", PROFILE]
                    output_result = subprocess.run(output_cmd, capture_output=True, text=True)
                    if output_result.returncode == 0:
                        print(f"   Error: {output_result.stdout[:500]}")
                    break
            elif state == "INTERNAL_ERROR":
                print(f"   ❌ Internal error running {notebook}")
                break
            
            print("   ⏳ Running...", end="\r")
            time.sleep(5)
        else:
            print(f"   ⚠️  Could not check status")
            break

print("\n" + "=" * 60)
print("✅ Setup complete!")


