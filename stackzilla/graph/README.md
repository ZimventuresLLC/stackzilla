# Graph Resolver
This module implements a graph resolver. For the purpose of Stackzilla, the items within the graph are class objects.
Each class can optionally depend on other classes. For the Stackzilla use case, this corresopnds to blueprint resources which depend on other resources. The resolver will break down the dependencies into _phases_. Within a phase, all classes are guaranteed to not depend on each other. In addition, any dependencies within a phase will have had their dependencies already addressed in a previous phase.

Example class hierarchy:
```
class ClassA:
    """Has no dependencies"""

class ClassB:
    """Depends on ClassA"""

class ClassC:
    ""Depends on ClassB""
```

If the resolver processes this hierarchy it will return 3 phases.
Phase 1: ClassA (since it has no dependencies)
Phase 2: ClassB (since ClassA has been resolved in Phase 1)
Phase 3: ClassC (since ClassC has been resolved in Phase 2)

What does *resolved* mean?
For the Stackzilla application, a dependency is considered resolved once it has been applied.
