#!/bin/bash

set -e

sudo apt update && sudo apt install -y \
  build-essential \
  curl \
  wget \
  git \
  gpg \
  gnupg \
  ca-certificates \
  software-properties-common \
  unzip \
  zip \
  tar \
  pkg-config \
  lsb-release \
  apt-transport-https \
  python3 \
  python3-pip \
  python3-venv \
  nano \
  vim \
  htop \
  net-tools \
  iputils-ping


# --- Configurable variables ---
POD_CIDR="10.32.0.0/12"
K8S_VERSION="1.29.0"

echo "[1/9] Installing containerd..."
apt-get update
apt-get install -y containerd

echo "[2/9] Configuring containerd..."
mkdir -p /etc/containerd
containerd config default | tee /etc/containerd/config.toml

# Ensure SystemdCgroup is true
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

systemctl restart containerd
systemctl enable containerd

echo "[3/9] Load kernel modules and sysctl settings..."
modprobe overlay
modprobe br_netfilter

cat <<EOF | tee /etc/sysctl.d/kubernetes.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sysctl --system

#echo "[4/9] Disabling swap..."
#swapoff -a
#sed -i '/ swap / s/^/#/' /etc/fstab

echo "[5/9] Installing Kubernetes components..."
curl -fsSL https://pkgs.k8s.io/core:/stable:/v${K8S_VERSION%.*}/deb/Release.key | gpg --dearmor -o /etc/apt/trusted.gpg.d/kubernetes.gpg

echo "deb https://pkgs.k8s.io/core:/stable:/v${K8S_VERSION%.*}/deb/ /" > /etc/apt/sources.list.d/kubernetes.list

apt-get update
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl

echo "[6/9] Initialize Kubernetes master node..."
kubeadm init \
  --pod-network-cidr=$POD_CIDR \
  --kubernetes-version=v$K8S_VERSION

echo "[7/9] Configuring kubectl for current user..."
mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config

echo "[8/9] Kubernetes master initialized."
echo "[9/9] Join command for workers:"
kubeadm token create --print-join-command

echo "✅ Done. You may now install a CNI like Flannel or Calico."
