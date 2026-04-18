import re
import argparse

def split_camel_case(s):
    regex = (
        r'(?<=[a-z])(?=[A-Z])|'
        r'(?<=[A-Z])(?=[A-Z][a-z])|'
        r'(?<=[A-Z][A-Z])(?=[A-Z][a-z])|'
        r'(?<=[a-zA-Z])(?=\d)|'
        r'(?<=\d)(?=[a-zA-Z])'
    )
    return re.split(regex, s)


def make_snake_from_camel(camel_str:str):
    fragments = split_camel_case(camel_str)
    if fragments:
        fragments_lower = [split.lower() for split in fragments]
        return "_".join(fragments_lower)
    else:
        raise ValueError(f"Camel case string: {camel_str} cannot be split")
    

def main():
    parser = argparse.ArgumentParser(description="Split camelCase or PascalCase string.")
    
    ## ✅ Correct place to define arguments
    #parser.add_argument("--camel", type=str, required=True, help="The camel string")
	
	# Define a positional argument instead of optional one
    parser.add_argument("camel", type=str, help="The camelCase or PascalCase string")
    
    args = parser.parse_args()
    
    # Now you can use args.camel
    #print(f"Received input: {args.camel}")
    print(make_snake_from_camel(args.camel))

if __name__ == "__main__":
    #camel_str = input("Enter camel string: ")
    #print(make_snake_from_camel(camel_str))
    main()
