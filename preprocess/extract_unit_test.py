import re
import ast
import json
from tqdm import tqdm
from utils import load_jsonl, save_jsonl

UNITTEST_FORMAT = """{code}

suite = unittest.TestLoader().loadTestsFromTestCase({class_name})
runner = unittest.TextTestRunner(stream=output, verbosity=2)
result = runner.run(suite)
locals_dict['result'] = result
"""

def extract_code(markdown_text):
    # match the value in ```python{code}```
    pattern = r'```python\n(.*?)\n```'
    matches = re.findall(pattern, markdown_text, re.DOTALL)

    if len(matches) == 0:
        pattern = r'```\n(.*?)\n```'
        matches = re.findall(pattern, markdown_text, re.DOTALL)
    
    return matches

def extract_class_names(code):
    # parse code and generate AST
    try:
        tree = ast.parse(code)
    except Exception as e:
        return []
    # traverse AST to find class definitions and extract class names
    class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    return class_names

def remove_import_lines(code):
    # Define a regular expression pattern that matches lines of the form 'from your_module import xxx' or 'from your_module import xxx # xxx'
    pattern = r'^from\s+your_module\s+import\s+\w+(\s+#.*)?$'
    
    # Use the re.sub() method to remove matching rows
    cleaned_code = re.sub(pattern, '', code, flags=re.MULTILINE)
    
    return cleaned_code

def extract_imports(code):
    imports = []
    try:
        tree = ast.parse(code)
    
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""))
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                for alias in node.names:
                    imports.append(f"from {module} import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""))
    except:
        return ['import unittest']
    
    return imports

def remove_func(code):
    imports = '\n'.join(extract_imports(code))
    code = code[code.find('\nclass'):]   
    if '\ndef' in code:
        code = code[:code.find('\ndef')]
        lines = code.splitlines()
        while '#' in lines[-1]:
            lines = lines[:-1]
        code = '\n'.join(lines)

    return imports + '\n' + code

def extract_unit_test(response):
    code = extract_code(response)
    unit_test = ""
    if len(code) == 1:
        code = code[0]
        class_names = extract_class_names(code)
        if len(class_names) == 1:
            if "__name__ == '__main__'" in code:
                code = code.replace("if __name__ == '__main__':\n    unittest.main()", "")
            if '__name__ == "__main__"' in code:
                code = code.replace('if __name__ == "__main__":\n    unittest.main()', "")
            code = remove_import_lines(code)
            code = remove_func(code)
            unit_test = UNITTEST_FORMAT.format_map({'code': code.rstrip('\n'), 'class_name': class_names[0]})
    return unit_test

def main(input_path, output_path, id_path):
    dataset = load_jsonl(input_path)
    id_dataset = load_jsonl(id_path)
    output = []
    for i in tqdm(range(len(dataset))):
        assert id_dataset[i]['messages'][0]['content'] == dataset[i]['messages'][0]['content']
        ut_set = set()
        for response in dataset[i]['responses']:
            unit_test = extract_unit_test(response)
            if unit_test != "" and unit_test not in ut_set:
                ut_set.add(unit_test)
        
        with open(output_path, 'a+') as fp:
            fp.write(json.dumps({
            'task_id': id_dataset[i]['task_id'],
            'unit_tests': list(ut_set)
        }, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    import argparse

    # parse parameter
    parser = argparse.ArgumentParser(description="Extract solution")
    parser.add_argument('--input_path', type=str, help='the path of inference result after merging')
    parser.add_argument('--id_path', type=str, help='the corresponding messages file which is used for inference')
    parser.add_argument('--output_path', type=str, help='the output path')
    args = parser.parse_args()

    main(args.input_path, args.output_path, args.id_path)
