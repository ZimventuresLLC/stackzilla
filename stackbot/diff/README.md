# Blueprint Diffing
StackBot needs to be able to detect differences between blueprints.

Multiple levels need to be diffed:
- Individual parameters
- Resources

Individual parameters can differ by
- newly defined
- removed
- modified

Complete resources can differ by
- newly defined
- removed
- modified
    [optional] requires rebuild

Is there a way to develop a difing engine that is independent from the blueprint system?
    - Should not "know" about the database vs. on-disk copies of the blueprint
    - Add "sandboxing" to the importer so that the same directory can be imported multiple times
    