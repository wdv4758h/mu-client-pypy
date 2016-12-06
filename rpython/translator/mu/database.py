"""
Tasks to be done at database stage:
- lower the debug operations to mu_ccalls
- collect all global definitions
    - types
    - constants
    - external functions
    - global cells
    - graphs & function references
- assign a Mu name to each global entity and local variable
- process external C functions
    - create a C function source file that redirects macro calls to function calls
    - find corresponding functions in libraries suggested
    - rename some functions based on platforms
- trace heap objects
"""