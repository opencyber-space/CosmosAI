# AIOS & AI Blueprints

This repository contains tutorials to get started on the following:
1. https://github.com/OpenCyberspace/OpenOS.AI-Documentation
2. https://github.com/opencyber-space/AIGr.id/tree/main

# AIOS AI Blueprints: Video Tutorial Series Index & Progress

Welcome to the **AIOS AI Blueprints Video Tutorial Series**!  
This guide is an index and progress tracker for the video tutorial series and accompanying Jupyter notebooks. It provides an overview of each part, its current status (as of September 5, 2025), and guidance on navigating the materials.

---

## 📚 Series Overview & Progress

| Part | Tutorial | Description | Status (as of 2025-09-5) | Video Link |
|------|----------------|-------------|---------------------------|:----------:|
| 1 | [prerequisites_setup](./video_tutorial_series/01_prerequisites_setup/) | Initial setup and prerequisites for the AIOS platform and working with LLMs. | <br>🟢 Jupyter notebook  |   -   |
| 2.a | [Part-1: onboard_gemma3<br>_llama_cpp](./video_tutorial_series/02_Part1_onboard_gemma3_llama_cpp/) | Onboarding Gemma-3 to AIOS ecosystem. | <br>✅ Video  <br>🟢 Jupyter notebook  | [AIOS Tutorial: Onboard Any GGUF Model in AIOS Ecosystem with LlamacppPython in Minutes](https://youtu.be/G_yKqIbBP5Q) |
| 2.b | [Part-2: onboard_<br>custom_llama_cpp](./video_tutorial_series/02_Part2_onboard_custom_llama_cpp/) | Onboarding custom LLM models with llama_cpp_python on AIOS. | <br>🟢 Jupyter notebook  |   -   |
| 2.c | [Part-3: More Models llama cpp](./video_tutorial_series/02_more_models_llama_cpp/) | Onboarding more models (Qwen & Magistral notebooks under AIOS onboarding in progress) using llama_cpp_python. | <br>🟢 Jupyter notebook |   -   |
| 3 | [autoscaler](./video_tutorial_series/03_autoscaler/) | Autoscaling on AIOS to support varying workloads as V1 Policy. | <br>✅ Video  <br>🟢 Jupyter notebook  | [Never Overprovision Again: Intelligent LLM Autoscaling with AIOS](https://youtu.be/SZPScDgwhqA) |
| 4 | [loadbalancer](./video_tutorial_series/04_loadbalancer/) | Load balancing strategies (V1 Policy) in AIOS for efficient inference. | <br>✅ Video  <br>🟢 Jupyter notebook  | [AIOS Smart Routing: Building a Token-Aware Load Balancer](https://youtu.be/HyC1jV-fzuE) |
| 5 | [router](./video_tutorial_series/05_router/) | Dynamic routing of requests to LLM models/endpoints in AIOS. | <br>✅ Video  <br>🟢 Jupyter notebook  | [The Ultimate AI Router: Dynamic Model Selection with AIOS](https://youtu.be/uW-qEsVKZAE) |
| 6 | [adhoc_inference](./video_tutorial_series/06_adhoc_inference/) | Ad-hoc/on-demand inference serving using AIOS. | <br>✅ Video  <br>🟢 Jupyter notebook  | [Mastering Ad-hoc Inference for Dynamic Model Execution](https://youtu.be/lEqe0iIUQy8) |
| 7 | [pre and post processing,<br> metrics,streaming,health](./video_tutorial_series/07_pre_and_post_processing_metrics_streaming_health/) | Pre/post-processing policies, metrics and streaming, health monitoring in AIOS. | <br>🟢 Jupyter notebook |   -   |
| 8 | [AutoAIExpert_RAG_Based](./video_tutorial_series/08_AutoAIExpert_RAG_Based/) | RAG based AppLayout and ScaleLayout generation | <br>✅ Video <br>🟢 Jupyter notebook | [Automate AI Design & Scaling with AutoAI Expert System for AIOS v1](https://youtu.be/RX7UYUQ1kKY) |
| 9.a | [Part-1: vDAG](./video_tutorial_series/09_vDAG/) |  vDAGs, Blocks, PostProcessing Policies, vDAG Controller | <br>✅ Video  <br>🟢 Jupyter notebook| [Break Down Complex AI Models with AIOS v1's vDAG \| A Deep Dive](https://youtu.be/VROxR2e5RNE) |
| 9.b | [Part-2: vDAG Policies](./video_tutorial_series/09_vDAG/) |  Policies(Quota Check, Quality Store) | <br>✅ Video <br>🟢 Jupyter notebook | [vDAG Controller Policy Demonstration: Quota and Quality store policy](https://youtu.be/OdBeVDoMhzE) |
| 9.c | [Part-3: vDAG Policies & Metrics](./video_tutorial_series/09_vDAG/) | Health Check and vDAGs Metrics | <br>✅ Video <br>🟢 Jupyter notebook | [Health Check policies and Metrics of vDAG Controller](https://youtu.be/XRc32ywSzX8) |
| 10.a | [Part-1: Cluster Node Block in AIOS](./video_tutorial_series/10_cluster_node_block/) | Cluster Controller gateway APIs, Cluster Controller, Node, Block | <br>✅ Video  <br>🟢 Jupyter notebook |   <br> [Cluster Controller gateway APIs, Cluster Controller](https://youtu.be/DktryLA-gaY) |
| 10.b | [Part-2: Policies of Control](./video_tutorial_series/10_cluster_node_block/) | Policies of Control for Gateway, Cluster Controller, Block | <br>✅ Video  <br>🟢 Jupyter notebook |  [Policies of Control for Gateway, Cluster Controller, Block](https://youtu.be/XlJufXZzYno) |
| 11 | [Cyclic Graph](./video_tutorial_series/11_circular_vdag/) | Using AIOSV1 policies to create a Debate System between LLMs | <br>✅ Video  <br>🟢 Jupyter notebook  |   -   |
| 12.a | [Part1: Model Splitting](./video_tutorial_series/12_model_splitting/) | Model Splitting within and across Nodes in AIOSV1 using Native Library Pytorch and Transformer(without Optimizations) | 🟢 Jupyter notebook  |   -   |
| 12.b | [Part2: Model Splitting](./video_tutorial_series/12_model_splitting/) | Model Splitting  within and across Nodes in AIOS using 3rd party softwares like vLLM(with Ray) in a Grid | 🟢 Jupyter notebook  |   -   |
| 13 | [Automate vision model selection MCP & ROR](./video_tutorial_series/12_model_splitting/) | Selecting Vision Models Dynamically from Registry of Registries Via MCP and LLM | 🟢 Jupyter notebook  |   -   |
---

### Legend

- ✅ Video Available
- 🟢 Jupyter notebook Available
- 🟡 Jupyter notebook partially created

---

## 🗂️ How to Use This Series

- Start with **01_prerequisites_setup** to ensure your environment is ready for the AIOS platform.
- Follow the sequence for a comprehensive journey through onboarding, scaling, and managing LLMs with AIOS.
- For each folder, refer to its notebook for detailed instructions, scripts, and (where available) video links.
- New video recordings and content will be added as they become available—check back for updates!

---

## 🚧 Coming Soon

- Many more tutorials on AGI Ecosystem

---

Happy Learning!  
For questions or contributions, open an issue or discussion in the repository.
