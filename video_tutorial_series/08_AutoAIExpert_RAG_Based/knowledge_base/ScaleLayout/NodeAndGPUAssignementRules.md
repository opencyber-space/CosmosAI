## Node and GPU Assignment

**NOTE** Use this for Deployment Planning in Scalelayout.

- Once sets are created, assign them to nodes and GPUs.
- Rules:
  - If multiple sets have the same usecase, distribute them across different servers.
    - Improves fault tolerance: if one server fails, the usecase is still available elsewhere.
    - Balances GPU and CPU usage across nodes.
  - Do not push all nodes to their limits initially.
    - Distribute sets horizontally across all GPUs/nodes before stacking multiple sets on a single GPU.
    - This balances heat generation and resource usage.
  - As much as possible see to it that all cameras in a set are put in single gpu before moving to next gpu. Because, the funcdamental concept of a set is to contain cameras that are related to each other in some way, so it makes sense to keep them together.
  

---

## FAQ (for RAG Retrieval)

**Q1: Why should I distribute sets with the same usecase across different servers?**  
A: This improves fault tolerance—if one server fails, the usecase remains available on other servers. It also helps balance resource usage.

**Q2: Should I fill up one node/GPU before using others?**  
A: No, distribute sets horizontally across all GPUs/nodes first. Only stack multiple sets on a single GPU after all are utilized. This prevents hotspots and balances load.

**Q3: What is the benefit of not pushing all nodes to their limits initially?**  
A: It helps avoid overheating, resource contention, and improves overall system stability and performance.

**Q4: How does this assignment strategy affect scaling?**  
A: It makes scaling easier and safer, as resources are evenly used and failures have less impact.

**Q5: Can I assign all sets of a usecase to a single node for simplicity?**  
A: This is not recommended, as it reduces fault tolerance and can overload a single node or GPU.

---