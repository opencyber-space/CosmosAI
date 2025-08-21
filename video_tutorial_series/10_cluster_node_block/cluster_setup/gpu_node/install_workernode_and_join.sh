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


if [ -z "$1" ]; then
  echo "❌ Error: Please provide the full 'kubeadm join' command as an argument."
  echo "Usage: sudo ./install_k8s_worker.sh \"kubeadm join <MASTER_IP>:<PORT> ...\""
  exit 1
fi

JOIN_COMMAND="$1"

echo "[1/7] Installing containerd..."
apt-get update
apt-get install -y containerd

echo "[2/7] Configuring containerd..."
mkdir -p /etc/containerd
containerd config default | tee /etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

systemctl restart containerd
systemctl enable containerd

echo "[3/7] Loading kernel modules and sysctl settings..."
modprobe overlay
modprobe br_netfilter

cat <<EOF | tee /etc/sysctl.d/kubernetes.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sysctl --system

echo "[4/7] Disabling swap..."
swapoff -a
sed -i '/ swap / s/^/#/' /etc/fstab

echo "[5/7] Installing Kubernetes components..."
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | gpg --dearmor -o /etc/apt/trusted.gpg.d/kubernetes.gpg
echo "deb https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /" > /etc/apt/sources.list.d/kubernetes.list

apt-get update
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl

echo "[6/7] Joining the Kubernetes cluster..."
$JOIN_COMMAND --cri-socket=unix:///var/run/containerd/containerd.sock

echo "[7/7] Worker node joined successfully!"
