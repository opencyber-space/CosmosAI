# Example RAG Queries for scalelayout.md

## Hardware & Decoding
- What is the maximum number of Full HD H265 streams a Tesla A10 GPU can decode at 30FPS?
- How many 4K H264 streams can a Tesla T4 GPU decode simultaneously?
- How do I estimate the number of GPUs needed for decoding streams at different FPS?

## CPU & RAM Requirements
- How many vCPUs are required to decode 2000 H264 FullHD camera streams?
- What is the estimated CPU RAM usage for 13 video streams in Kubernetes?
- How can I calculate vCPU and RAM requirements for a given number of camera sources?

## GPU RAM Planning
- How much GPU RAM does a single H265 FullHD stream at 15FPS use on a Tesla T4?
- What is the GPU RAM per GPU for Tesla A10 and Tesla A100?
- How do I estimate the number of GPUs needed based on total GPU RAM required?

## AppLayout & ScaleLayout Concepts
- What is the difference between AppLayout and ScaleLayout in AIOS?
- How does ScaleLayout help in optimizing hardware requirements?
- How are GStreamer pipelines used in ScaleLayout?

## Model Deployment & Planning
- What parameters affect model throughput and GPU utilization?
- How should batch size and decoder type be chosen for model deployment?
- How do I use pod_metrics.xlsx and pod_gpumemory_and_gpuutility.csv for planning?

## Practical Node & Set Planning
- What is the recommended node configuration for 5 GPUs per node?
- How do I create sets for deployment planning in ScaleLayout?
- What are the rules for grouping usecases in a set?

## Camera & Usecase Matrix
- How do I map cameras to usecases for deployment?
- What is the typical FPS requirement for Parking Violation usecase?
- How do I plan the number of usecases per camera for 605 cameras and 1700 licenses?

## General Optimization & Best Practices
- How can I maximize model utilization across multiple cameras?
- What are the best practices for assigning sets to nodes and GPUs?
- How do I balance GPU and CPU usage across nodes for fault tolerance?

---

**Tip:**
For best results, phrase your queries as naturally as possible, using the terminology and structure found in your markdown. This will help the retriever surface the most relevant and context-rich chunks.
