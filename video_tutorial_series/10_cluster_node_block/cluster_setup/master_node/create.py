import os
import yaml
import argparse
import requests

# Constants
DEFAULT_KUBE_CONFIG_PATH = os.path.join(os.path.expanduser("~"), "configs/cluster-1.yaml")
API_URL = "http://MANAGEMENTMASTER:30600/create-cluster-infra"


def create_cluster_infra(cluster_id, kube_config_data):
  payload = {
    "cluster_id": cluster_id,
    "kube_config_data": yaml.safe_load(open(DEFAULT_KUBE_CONFIG_PATH, "r"))
  }
  response = requests.post(API_URL, json=payload)
  print(response.text, response.status_code)
  if response.status_code == 200:
    print("Cluster creation scheduled successfully:", response.json())
  else:
    print("Error creating cluster:", response.json())

def main():
  parser = argparse.ArgumentParser(description="Create Cluster Infrastructure via API")
  parser.add_argument("cluster_id", help="Cluster ID")
  parser.add_argument("--config", default=DEFAULT_KUBE_CONFIG_PATH,       help="Path to Kubernetes config file")

  args = parser.parse_args()
  create_cluster_infra(args.cluster_id, kube_config_data=None)

if __name__ == "__main__":
  main()
