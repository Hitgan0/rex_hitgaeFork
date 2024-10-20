from typing import Dict
import pandas as pd

from src.relationalAlgebra.REsymbols import symbols, setOpSymbols, joinOpSymbols, singleOpSymbols, allRelationSymbols
from src.relationalAlgebra.relationNodes import relationNode, setOperationNode, singleOpNode, joinOpNode, joinOpWithConditionNode


# Converts any text version of operation strings into standard symbols: "intersect" --> "∧"
def symbolize( line: str ) -> str:
    result = line
    for symbol in symbols:
        result = result.replace(symbol, symbols[symbol])
        result = result.replace(symbol.upper(), symbols[symbol])
    return result


# Validates possible character for relation name, only allows letters and numbers
def validRelationChar( char: str ) -> bool:
    return char.isalnum() and char not in allRelationSymbols


# Relation Parser to convert string to relational algebra node tree representation
def relationalParser( line: str , relations: Dict[str, pd.DataFrame] = None, debug = False) -> relationNode:

    lhsNode = None
    rhsNode = None
    op = ""
    condition = ""

    if debug:
        print(f"Starting to parse: {line}")

    index = 0
    mode = "start"
    while(index < len(line) + 1):

        # If relation node pieces found, make the appropriate relation node
        if mode == "build":
            # build relation node and set parsing mode back to looking for operation symbol
            if op in setOpSymbols:
                if (lhsNode is None or rhsNode is None or op == ""):
                    raise ValueError("One or more varaibles not set in set operation building") 
                if debug:
                    print(f"Index {index}: Making set operation of {op} between {lhsNode} and {rhsNode}")
                newNode = setOperationNode( LHSVariable=lhsNode, RHSVariable=rhsNode, setOp=op, userInput=line[0:index])

            elif op in singleOpSymbols:
                if (lhsNode is None or op == "" or condition == ""):
                    raise ValueError("One or more varaibles not set in singleton building") 
                if debug:
                    print(f"Index {index}: Making singleton operation of {op} for {lhsNode} with condition:{condition}")
                newNode = singleOpNode(SingleVariable=lhsNode, singleOp=op, condition=condition, userInput=line[0:index])

            elif op in joinOpSymbols:
                
                if (lhsNode is None or op == "" or rhsNode is None):
                    raise ValueError("One or more varaibles not set in join building") 
                if debug:
                    print(f"Index {index}: Making join operation of {op} for {lhsNode} | {rhsNode} with condition: {condition}")
                if condition == "":
                    newNode = joinOpNode(LHSVariable=lhsNode, RHSVariable=rhsNode, joinOp=op, userInput=line[0:index])
                else:
                    newNode = joinOpWithConditionNode(LHSVariable=lhsNode, RHSVariable=rhsNode, joinOp=op, condition=condition, userInput=line[0:index])

            else:
                raise ValueError(f"Operation not found, current op {op}")

            # Reset variables for parsing
            lhsNode = newNode
            rhsNode = None
            mode = "operation"
            op = ""
            condition = ""
            continue

        if index == len(line):
            break
        char = line[index]
        if char == " ": #skip whitespace
            index += 1
            continue
        if debug:
            print(f"Index {index}: with char -- {char}")       

        # Finding a condition/boolean
        if char == '{':  # No mode check, if condition found for operation that does not require it, error will be thrown when building node
            conditionLine = ""
            index += 1
            while index < len(line):
                char = line[index]
                if char == '}':
                    break
                
                conditionLine += char
                index += 1
            
            if debug:
                print(f"Index {index}: found conditon: {conditionLine}")
            
            condition = conditionLine
            index+=1
        # Finding a symbol for an operation
        elif char in symbols.values() and (mode in {"start", "operation"}):

            # check based on symbol, set op and op type, make mode according to op

            # check if you are start and op with op R line AND THERE IS NO LHS NODE
            
            if char in setOpSymbols:
                mode = "relation"
            elif char in singleOpSymbols:
                if mode != "start":
                    raise ValueError("Single operation found not at the start!")
                mode = "relation"               
            elif char in joinOpSymbols:
                mode = "relation"
            else:
                raise ValueError(f"Unexpected Symbol at index:{index}")

            op = char

            if debug:
                print(f"Index {index}: Found operation {op}")
            index += 1
        # Building a relation variable/node
        elif (validRelationChar(char) or char == '(') and (mode in {"start", "relation"}):
            # Parenthesis case for nested expressions
            if char == '(':
                parenthesisLine = ""
                parenthesisCount = 1
                index += 1
                while(parenthesisCount != 0 and index < len(line)):
                    char = line[index]
                    if char == '(':
                        parenthesisCount += 1
                    elif char == ')':
                        parenthesisCount -= 1
                    
                    if parenthesisCount != 0:
                        parenthesisLine += char
                    index += 1
                
                if parenthesisLine == "":
                    raise ValueError(f"Parenthesis match has no arguments at index: {index}")
            
                newNode = relationalParser(line = parenthesisLine, relations=relations, debug=debug)
                newNode.userInput = '(' + newNode.userInput + ')'
            else:
                relation = ""
                while(index < len(line) and validRelationChar(char)):

                    relation += char
                    index += 1
                    if index != len(line):
                        char = line[index]
                
                if relation == "":
                    raise ValueError(f"Expected relation at index {index} with line: {line}")
                if relations is not None and relation not in relations:
                    raise ValueError(f"Relation {relation} not known, found at index {index}")

                if debug:
                    print(f"Index {index}: Found relation {relation}, making node.")

                newNode = relationNode(userInput=relation, 
                                    resultDF = relations[relation] if relations is not None else None)
            if op in singleOpSymbols:
                lhsNode = newNode
                mode = "build"
            elif lhsNode is None:
                lhsNode = newNode
                mode = "operation"
            else:
                rhsNode = newNode
                mode = "build"
        else:
            raise ValueError(f"Search mode: {mode} at index: {index}, got {char} instead.")
        
    # Error checking nothing was left over
    if lhsNode is None:
        raise ValueError("No valid relation built")
    if op != "" or condition != "" or rhsNode is not None:
        raise ValueError(f"Still expecting more arguments, currently built node: {lhsNode} versus remaining line: {line}")
    
    if debug:
        print(f"Index {index}: Returning node: {lhsNode}")
    return lhsNode


if __name__ == "__main__":
    df1 = pd.DataFrame({
        'A': [7, 2, 8, 1, 3],
        'B': ['a', 'b', 'c', 'd', 'e'],
        'C': [10.5, 20.3, 30.1, 40.7, 50.9],
        'D': [True, False, True, False, True],
        'E': ['apple', 'banana', 'orange', 'grape', 'kiwi']
    })

    df2 = pd.DataFrame({
        'A': [4, 1, 5, 6, 9],
        'B': ['x', 'y', 'z', 'w', 'v'],
        'C': [15.2, 25.6, 35.8, 45.3, 55.1],
        'D': [False, True, False, True, False],
        'E': ['pineapple', 'mango', 'strawberry', 'blueberry', 'watermelon']
        })
    df3 = pd.DataFrame({
        'F': [2, 3, 4, 7, 8],
        'G': ['a', 'y', 'c', 'w', 'd'],
        'H': [45.2, 15.6, 65.8, 35.3, 53.1],
        'I': [True, True, False, False, False],
        'J': ['apple', 'mango', 'orange', 'blueberry', 'kiwi']
        })    
    df4 = pd.DataFrame({'ID': [1, 2, 3],
                        'Name': ['Alice', 'Bob', 'Charlie']})

    df5 = pd.DataFrame({'ID': [1, 2, 4],
                        'Age': [25, 30, 35]})
    dataFrameDictionary = {}
    dataFrameDictionary['R'] = df1
    dataFrameDictionary['S'] = df2
    dataFrameDictionary['T'] = df3
    dataFrameDictionary['U'] = df4
    dataFrameDictionary['V'] = df5


    #testLine = "project_ {A,C,E} R"
    testLine = "select_ {E = apple} R"
    #testLine = "U join_ V"
    #testLine = "U * V"
    #testLine = "U X V"
    print("Here is the current line: " + testLine)
    
    testLine = symbolize(testLine)

    rootNode = relationalParser(line=testLine, debug=True)

    print("This is testLine after symbolize: " + testLine)
    print("Here is our query: " + str(rootNode))
    print(rootNode.resolve(dataFrameDictionary))
    print('\n' * 4)