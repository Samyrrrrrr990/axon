# How Axon's caching works

Every node's output is cached on disk, keyed by the node's settings plus the
outputs of everything upstream. When you change one node and press Run, Axon
recomputes only the part of the pipeline that actually changed. The rest loads
instantly from cache and is marked with a lightning bolt.

Nodes that call language models are never cached, so every run gives you a
fresh response.
