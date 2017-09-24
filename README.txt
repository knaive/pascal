A simple pascal interpreter following this series of articles:  https://ruslanspivak.com/


Run these two commands to get a picture of AST for code in pascal_code.txt.
    # python genastdot.py pascal_code.txt > ast.dot 
    # dot -Tpng -o ast.png ast.dot
You have to install graphviz to run the dot command