## 🧠 Introduction: vDAGs — Building Scalable, Distributed AI Workflows with Blocks

In modern AI systems, building powerful applications is no longer about deploying a single large model. Instead, it's about connecting many smaller, reusable, and scalable components — each handling a part of the task. This is where **vDAGs**, or **virtual Directed Acyclic Graphs**, step in as a game-changing abstraction for designing **distributed AI workflows**.

A **vDAG** represents a **virtual workflow composed of interconnected “blocks”**, where each block serves a specific AI or computational function. These blocks are created and deployed by developers on their own clusters using the **AIOSv1 Instance SDK**, and can scale independently based on demand.

What makes vDAGs powerful is that they allow you to build **end-to-end applications** using these distributed blocks, orchestrating them across a graph structure that can span **within or across multiple clusters**.

---

## 🔍 What Is a Block?

Before diving deeper into vDAGs, let’s clarify what a **block** is.

A **block** is the core serving component in the AIOSv1 ecosystem. It represents a self-contained unit responsible for:

* Instantiating and serving AI models or general-purpose computation
* Scaling based on load
* Being managed dynamically across a distributed cluster environment

Blocks are deployed by users on any cluster that meets the resource requirements. Once deployed, they can serve:

* As **nodes in one or more vDAGs**
* Or as **standalone inference endpoints** outside any vDAG

---

## 🔗 What Is a vDAG?

A **vDAG** (virtual Directed Acyclic Graph) is a **workflow composed of blocks**, where each node in the graph is a block (or even another vDAG). It defines how data flows through a sequence of operations — such as preprocessing, model inference, post-processing, and so on — executed across the network of blocks.

The key word here is *virtual*. vDAGs don’t physically contain the logic — they refer to existing blocks deployed on clusters. Think of a vDAG as a **blueprint or routing plan** for how a particular task should be processed by different blocks across the network.

---

## ⚙️ Key Features of vDAG

* ✅ **Modular Composition**: Each node is a block that can be reused in multiple workflows or used standalone.
* ✅ **Nested Graphs**: Nodes in a vDAG can themselves reference other vDAGs (subgraphs).
* ✅ **Cross-Cluster Execution**: Nodes can reside on different clusters depending on where blocks are deployed.
* ✅ **Assignment Policies**: During vDAG creation, a policy can select the most suitable block from a pool of candidates for a given node.
* ✅ **Custom Behavior**: Each node supports **pre-processing** and **post-processing policies**, which run before or after the core block function — allowing for transformations, validation, routing logic, etc.
* ✅ **Flexible Patterns**: Supports fan-in/fan-out logic like multiple producers → single consumer, ensembles, and branching.

### Think of It Like This…

If **blocks** are like Lego bricks that do things (classify, generate, filter, etc.), a **vDAG** is your custom-built machine. You can reuse the same bricks in multiple machines, snap them together in different ways, and control how the machine runs through policies and automation.

## 🌐 Real-World Use Case

Imagine you want to process a support ticket using AI:

1. **Pre-processing Block** parses and normalizes the text.
2. **Sentiment Analysis Block** determines the tone.
3. **Intent Detection Block** identifies the user’s goal.
4. **LLM Block** generates a response.
5. **Post-processing Block** formats the final output.

With vDAG, you simply define the graph. The system figures out which blocks to call, where they’re running, and how to route the data — possibly across clusters and providers.

---

## 🧩 Defining and Creating Your First vDAG (Minimal Setup)

Now that your controller is live and ready, the final step is to **define and deploy your vDAG** — the actual blueprint that wires your AI blocks together into a functioning pipeline.

A **vDAG** is defined as a JSON structure that specifies:

* Which **blocks** are used
* How they are **connected**
* Any optional **policies** (e.g., preprocessing, postprocessing, assignment)
* Input/output mappings for each node

In this section, we’ll walk through a **minimal working example** to help you get started quickly.

---

### ✨ Minimal Example: What This vDAG Does

This vDAG performs a three-stage AI workflow using **manual block assignments**:

1. `gemma3-27b-block` — receives and processes the input
2. `llama4-scout-17b-block` — performs intermediate inference
3. `magistral-small-2506-llama-cpp-block` — final processing, including post-processing logic

This setup uses **no assignment policies** and **no preprocessing logic**. Only the last block has a `postprocessingPolicyRule`.

> 🔹 **Note**: You can always extend this setup by adding assignment, pre/post policies, or dynamic search logic.

---

### 🧱 Sample vDAG JSON (Without Templates)

Below is a simplified version of the vDAG spec file (saved as `llm-vdag.json`):

```json
{
  "parser_version": "Parser/V1",
  "body": {
    "spec": {
      "values": {
        "vdagName": "llm-analyzer",
        "vdagVersion": {
          "version": "0.0.6",
          "release-tag": "stable"
        },
        "discoveryTags": ["objedet", "narasimha", "prasanna"],
        "controller": {},
        "nodes": [
          {
            "values": {
              "nodeLabel": "gemma3-27b-block",
              "nodeType": "block",
              "manualBlockId": "gemma3-27b-block",
              "preprocessingPolicyRule": {},
              "postprocessingPolicyRule": {},
              "modelParameters": {}
            },
            "IOMap": [{
              "inputs": [{ "name": "input_0", "reference": "input_0" }],
              "outputs": [{ "name": "output_0", "reference": "output_0" }]
            }]
          },
          {
            "values": {
              "nodeLabel": "llama4-scout-17b-block",
              "nodeType": "block",
              "manualBlockId": "llama4-scout-17b-block",
              "preprocessingPolicyRule": {},
              "postprocessingPolicyRule": {},
              "modelParameters": {}
            },
            "IOMap": [{
              "inputs": [{ "name": "input_0", "reference": "input_0" }],
              "outputs": [{ "name": "output_0", "reference": "output_0" }]
            }]
          },
          {
            "values": {
              "nodeLabel": "magistral-small-2506-llama-cpp-block",
              "nodeType": "block",
              "manualBlockId": "magistral-small-2506-llama-cpp-block",
              "preprocessingPolicyRule": {},
              "postprocessingPolicyRule": {
                "policyRuleURI": "post_processor_for_job_caller:0.0.1-stable"
              },
              "modelParameters": {}
            },
            "IOMap": [{
              "inputs": [{ "name": "input_0", "reference": "input_0" }],
              "outputs": [{ "name": "output_0", "reference": "output_0" }]
            }]
          }
        ],
        "graph": {
          "input": [{
            "nodeLabel": "gemma3-27b-block",
            "inputNames": ["input_0"]
          }],
          "output": [{
            "nodeLabel": "magistral-small-2506-llama-cpp-block",
            "outputNames": ["output_0"]
          }],
          "connections": [
            {
              "nodeLabel": "llama4-scout-17b-block",
              "inputs": [{
                "nodeLabel": "gemma3-27b-block",
                "outputNames": ["output_0"]
              }]
            },
            {
              "nodeLabel": "magistral-small-2506-llama-cpp-block",
              "inputs": [{
                "nodeLabel": "llama4-scout-17b-block",
                "outputNames": ["output_0"]
              }]
            }
          ]
        }
      }
    }
  }
}
```

> 🧠 **Tip**: While this vDAG uses *manualBlockId* to explicitly fix each node to a block, you can also configure an **assignment policy** for dynamic block selection based on availability, metadata, or load.

---

### 🚀 Deploying the vDAG

To deploy your vDAG, use this `curl` command:

```bash
#!/bin/bash

curl -X POST -d @./llm-vdag.json \
     -H "Content-Type: application/json" \
     http://MANAGEMENTMASTER:30501/api/createvDAG
```

✅ **Expected Response**:

```json
{
  "data": "vDAG created successfully",
  "success": true
}
```

Once the vDAG is registered, it will be discoverable and usable by any active vDAG controller that matches the `vdag_uri`.

---

### 🔍 Summary: What We Built

| Component       | Value                                                              |
| --------------- | ------------------------------------------------------------------ |
| **vDAG Name**   | `llm-analyzer`                                                     |
| **Version**     | `0.0.6-stable`                                                     |
| **Blocks Used** | `gemma3-27b`, `llama4-scout-17b`, `magistral-small-2506-llama-cpp` |
| **Flow**        | Input → Block 1 → Block 2 → Block 3 → Output                       |
| **Assignment**  | Manual block assignment only                                       |
| **Policies**    | Post-processing applied on final block                             |

---

## 🛡 The vDAG Controller

To manage all this complexity, you deploy a **vDAG controller**. This component acts as a gateway and execution manager for vDAGs. Its responsibilities include:

* Accepting inference tasks and executing them through the defined vDAG
* Enforcing **rate-limits and quotas**, per session or globally
* Monitoring block health via a **health checker policy**
* Verifying output correctness using a **quality checker policy**
* Exposing APIs to manage these policies
* Collecting performance metrics like **latency** and **throughput**

The controller ensures that vDAGs remain reliable, observable, and governable at scale.

---

## Why vDAGs Matter

vDAGs offer a **cloud-native approach to AI orchestration**. They empower teams to:

* Build once and reuse everywhere
* Seamlessly scale parts of a system without touching the whole
* Combine AI and non-AI logic across environments
* Integrate governance, health, and quality into the workflow itself

Whether you’re deploying a full-stack LLM application or stitching together multi-modal pipelines, vDAGs make it easier to scale, adapt, and maintain your AI systems.

---

## Smart Policies That Keep vDAGs Reliable

vDAGs are powerful because they don’t just stitch AI blocks together — they’re **smart, policy-driven workflows**. The **vDAG Controller** supports three important policies that run in the background or at task submission time, helping maintain:

* Consistency of results (Quality)
* Stability of infrastructure (Health)
* Fair use of system resources (Quota)

Let’s explore each of these controller-level policies, with simple examples to show how they work in practice.

---

### 1. Quality Checker Policy: Audit What You Serve

The **Quality Checker Policy** is like having a silent auditor watching your AI outputs. It periodically samples tasks — both the **inputs** and the **results** — and runs a custom check to see whether the outputs meet expectations.

You can use this to:

* Automatically flag suspicious or incorrect results
* Forward samples to an external QA team for manual review
* Validate your pipeline against test cases in real time

**How it works**:

* It runs in the background and doesn’t affect user-facing latency.
* It receives the full request and response pair.
* You decide what to do with the data — log it, analyze it, or send it elsewhere.

**Input Example**:

```json
{
  "vdag_info": { "id": "chatbot-graph" },
  "input_data": {
    "request": { "text": "What is 2 + 2?" },
    "response": { "text": "It's probably 5." }
  }
}
```

**Example Use Case**:
Suppose you're building a math tutoring bot. You can write a quality checker that runs a basic rule like:

```python
if "2 + 2" in input and "4" not in output:
    flag_for_review()
```

Even though the model is the one generating the answer, this policy helps you catch subtle logic errors early.

---

### ❤️ 2. Health Checker Policy: Keep an Eye on Your Blocks

AI blocks — just like any service — can go down, get slow, or behave oddly. That’s why the **Health Checker Policy** exists. It’s called **periodically** (every few seconds or minutes) and receives a report about the health of all blocks in the vDAG.

If a block is unhealthy, the report includes a reason such as:

* API internal error
* Timeout
* Network failure
* Misconfiguration

**Input Example**:

```json
{
  "vdag": { "id": "image-processing-pipeline" },
  "health_check_data": {
    "block-id-123": {
      "success": false,
      "data": {
        "mode": "timeout_error",
        "data": "No response after 5 seconds"
      }
    }
  }
}
```

 **Example Use Case**:
Let’s say you have a block that runs image classification. Your health checker might do:

```python
if not health["success"]:
    send_alert_to_slack(block_id, health["data"]["mode"])
```

You can also track **failure streaks** and disable a block temporarily if it’s been flaky multiple times in a row.

---

### 3. Quota Checker Policy: Rate-Limiting With Precision

The **Quota Checker Policy** ensures that no one overuses your vDAG — especially if you're offering it as a shared service or public API. It allows you to:

* Limit the number of tasks a session can submit
* Track quota usage per user
* Deny requests that exceed the allowed quota

This policy is triggered **every time a task is submitted**.

**Input Example**:

```json
{
  "session_id": "user-abc",
  "quota": 101,
  "quota_table": "<QuotaManagement instance>",
  "input": { "prompt": "Tell me a joke" }
}
```

**Example Use Case**:
Suppose you want to allow 100 requests per user per hour:

```python
if input_data["quota"] > 100:
    return { "allowed": False }
else:
    return { "allowed": True }
```

Now your system won’t be overwhelmed by a single user sending 1,000 requests in a loop.

Behind the scenes, the `QuotaManagement` class handles Redis caching for quotas — including incrementing counts, TTL-based resets, and cleaning expired data.

---

## Why These Policies Matter

Together, these controller policies help your vDAGs remain:

* **Safe** (by detecting anomalies)
* **Healthy** (by monitoring infrastructure)
* **Fair** (by limiting overuse)

And the best part? They’re **pluggable Python classes**. You can easily define your own logic, test it, and deploy it — without rewriting your inference logic or modifying the blocks themselves.

---

## Deploying the vDAG Controller: Your Gateway to AI Workflows

Now that we’ve seen how smart policies keep your system safe and performant, it’s time to bring everything to life by deploying the **vDAG Controller** — the core service that routes tasks, enforces rules, monitors health, and exposes APIs for inference and management.

Think of the **vDAG Controller** as the **central gateway** to your virtual AI workflow. You can have one or more controllers running for the same vDAG, each deployed on different clusters, enabling better scaling and fault tolerance.

Let’s walk through how to create, query, and monitor a controller in action.

---

### Creating a vDAG Controller

To create a controller, all you need is a simple `POST` request. This will schedule the controller pod on the target cluster with the specified configuration.

**Example:**

```bash
curl -X POST http://MANAGEMENTMASTER:30600/vdag-controller/gcp-cluster-2 \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create_controller",
    "payload": {
      "vdag_controller_id": "llm-vdag-controller-001", 
      "vdag_uri": "llm-analyzer:0.0.6-stable",
      "config": {
        "policy_execution_mode": "local",
        "replicas": 1
      },
      "search_tags": []
    }
  }'
```

**Expected Response:**

```json
{
  "data": "Controller created successfully",
  "success": true
}
```

Here:

* `vdag_controller_id` is the unique ID for this controller instance.
* `vdag_uri` points to the vDAG definition you want this controller to serve.
* `policy_execution_mode` can be set to `"local"` or `"remote"` depending on where your policies run.
* `replicas` controls how many controller pods are deployed.

---

### Querying Controller Info

Once deployed, you can fetch details about any controller using a `GET` request.

**Example:**

```bash
curl -X GET http://MANAGEMENTMASTER:30103/vdag-controller/llm-vdag-controller-001
```

**Sample Response:**

```json
{
  "data": {
    "vdag_controller_id": "llm-004",
    "vdag_uri": "llm-analyzer:0.0.6-stable",
    "cluster_id": "gcp-cluster-2",
    "config": {
      "api_url": "http://CLUSTER1MASTER:32696",
      "rest_url": "http://CLUSTER1MASTER:31351",
      "rpc_url": "CLUSTER1MASTER:30095",
      "policy_execution_mode": "local",
      "replicas": 1
    },
    "public_url": "CLUSTER1MASTER:30095",
    "search_tags": ["objedet", "narasimha", "prasanna"]
  },
  "success": true
}
```

**What these fields mean**:

* `api_url`: Used to send **REST inference requests**
* `rest_url`: Used to **manage controller policies**
* `rpc_url`: Used for **gRPC inference**
* `public_url`: Public gRPC endpoint (can be the same as `rpc_url`)

> **You can have multiple controllers serving the same vDAG** from different clusters — which is useful for regional scaling or redundancy.

---

### Monitoring Controller Metrics

You can fetch **performance metrics** for your vDAG (such as FPS, latency, and request counts) by querying the metrics endpoint.

**Example:**

```bash
curl -X POST http://MANAGEMENTMASTER:30203/vdag/query \
  -H "Content-Type: application/json" \
  -d '{
    "vdagURI": "llm-analyzer:0.0.6-stable"
  }'
```

**Sample Response:**

```json
{
  "data": [
    {
      "vdagURI": "llm-analyzer:0.0.6-stable",
      "type": "vdag",
      "inference_requests_total": 0,
      "inference_fps": 0,
      "inference_latency_seconds": 0
    }
  ],
  "success": true
}
```

**Metrics Explained**:

* `inference_requests_total`: How many requests have been processed
* `inference_fps`: Requests per second (throughput)
* `inference_latency_seconds`: Average latency per request
* `timestamp`: When the metric snapshot was taken

---

### Real-World Scenario

Imagine you're deploying an LLM pipeline named `llm-analyzer`. You want:

* A controller running in **GCP Cluster 2**
* Rate limits and quality audits enabled
* A REST endpoint for user apps to send prompts

With just a single POST call, the controller is up and running, and you can now:

* Submit inference via `api_url`
* Track system health and metrics in real time
* Scale up replicas later if needed

---

## Submitting Inference Requests to the vDAG Controller

Once your **vDAG Controller is up and running**, it exposes an API endpoint through which you can **send inference tasks**. This is where your application (frontend, backend, or another system) actually interacts with the vDAG — submitting inputs and receiving AI-generated outputs.

The endpoint for this is given in the controller config as `config.api_url`.

---

### Submitting an Inference Request

Let’s walk through how to submit a sample request to your deployed vDAG.

**Example:**

```bash
curl -X POST http://CLUSTER1MASTER:30893/v1/infer \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-abc-123",
    "seq_no": 3,
    "data": {
      "mode": "chat",
      "gen_params": {
        "temperature": 0.1,
        "top_p": 0.95,
        "max_tokens": 4096
      },
      "messages": [
        {
          "content": [
            {
              "type": "text",
              "text": "Analyze the following image and generate your objective scene report.?"
            },
            {
              "type": "image_url",
              "image_url": {
                "url": "https://akm-img-a-in.tosshub.com/indiatoday/images/story/202311/chain-snatching-caught-on-camera-in-bengaluru-293151697-16x9_0.jpg"
              }
            }
          ]
        }
      ]
    },
    "graph": {},
    "selection_query": {}
  }'
```

---

### Real-World Example

Imagine you're building a multi-modal AI assistant that can understand both text and images. With this setup:

* Your **frontend** captures an image and user prompt.
* The frontend **sends a request** to the vDAG controller's `/v1/infer` endpoint.
* The vDAG handles the rest:

  * Pre-process the image and text
  * Route the task through your AI pipeline (e.g., Vision Encoder → Scene Analyzer → Language Generator)
  * Post-process and return a human-readable summary

All of this is distributed and policy-driven — yet **you interact with it using just a single HTTP call**.

---

### Why It’s Powerful

This setup gives you:

* **One unified API** for chat, image, and structured generation tasks
* **Backend-managed orchestration** — no need to wire together services manually
* **Policy-driven control** over behavior, security, and audit
* **Real-time scalability** — vDAG automatically scales blocks behind the scenes





