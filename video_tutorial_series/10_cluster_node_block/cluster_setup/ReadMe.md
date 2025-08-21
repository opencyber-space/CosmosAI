## To Setup New Cluster
### Step.1: Install Script on Master Node
- Run the following script on master node
- If Needed you can change CIDR of POD in the script
```bash
sudo bash master_node/install_masternode.sh
```
- Collect the join command from the output of the script.
- The join command will look like this:
```bash
kubeadm join <master-ip>:<port> --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```
- Once Master node is ready:
```bash
  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config
```
- Then create neworking layer with weavenet
```bash
kubectl apply -f https://reweave.azurewebsites.net/k8s/v1.29/net.yaml
```

### Step.2: Install and Join Script on Worker Node
- First install the Nvidia Driver by downloading latest driver from Nvidia website
- Run the following script on worker node
```bash
sudo bash gpu_node/install_workernode_and_join.sh `join_command_from_master`
```
- Copy the config file from master and put it in worker node for kubectl access
```bash
mkdir -p $HOME/.kube
# scp the $HOME/.kube/config from master node to worker node
# and then run the following command on worker node
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```
- Then install the Nvidia Contiainer Toolkit by running the following this
    - `https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html`

### Step.3: Add Tag to Worker Node (for GPU Node only)
- Add the tag to the worker node by running the following command
```bash
bash gpu_node/annotation_gpunode.sh
```
### Step.4: Replace Toml File in Master node
- Replace the toml file in master node with the one provided in `master_node/config_master.toml` to `/etc/containerd/config.toml`
```bash
sudo cp master_node/config_master.toml /etc/containerd/config.toml
```
- Restart the containerd service
```bash
sudo systemctl restart containerd   
```

### Step.5: Replace Toml File in Worker node
- Replace the toml file in worker node with the one provided in `worker_node/config_gpu.toml` to `/etc/containerd/config.toml`
```bash
sudo cp worker_node/config_gpu.toml /etc/containerd/config.toml
```
- Restart the containerd service
```bash
sudo systemctl restart containerd   
```