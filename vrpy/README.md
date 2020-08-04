# Hyperheuristic 
Hyperheuristic is a python class with the high-level heuristic implementation for VRPy
    - Selection 
    - Storing, off_line learning 
    - Different move acceptance
    - 

## Contains 
Contains the HyperHeuristic class with methods for choosing subproblem heuristics. 
### High level heuristics 
class methods select_heuristic and move_acceptance takes care of heuristic selection and whether or not a move should be rejected. 
### Storing data 
method3 and method4 store and retrieve data from previous runs of the problem 

the update method updates the relevant parameters in each loop 

choose hyperheuristic selects the chosen hyperheurstic 
    - move acceptance 
    - update 
    - update_parameters
    - Write to file 
    - read from file 

### The HyperHeuristic class for VRPy

## Dependencies 
vrpy.main

## Usage
    - Relevant input parameters: 
        - Heuristic selection: Activation and overrulling: insert the wanted heuristic as a keyword parameter to freeze the heuristic selection 
        - This can also be done by setting the VRPy parameter to False. 
    - Pass 

## 