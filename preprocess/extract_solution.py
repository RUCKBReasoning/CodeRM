import re
from os import system
from tqdm import tqdm
from utils import load_jsonl, save_jsonl

def extract_code(markdown_text):
    pattern = r'```python\n(.*?)\n```' 
    matches = re.findall(pattern, markdown_text, re.DOTALL)

    if len(matches) == 0:
        pattern = r'```\n(.*?)\n```'
        matches = re.findall(pattern, markdown_text, re.DOTALL)
    
    return matches

def extract_sol(data_path, id_path, save_path):
    dataset = load_jsonl(data_path)

    output = []
    id_dataset = load_jsonl(id_path)
    for i in tqdm(range(len(dataset))):
        assert id_dataset[i]['messages'][0]['content'] == dataset[i]['messages'][0]['content']
        sol_list = []
        for response in dataset[i]['responses']:
            code = extract_code(response)
            if len(code) == 1:
                sol = code[0]
                sol_list.append(sol)

        output.append({
            'task_id': id_dataset[i]['task_id'],
            'solutions': sol_list
        })
    
    save_jsonl(save_path, output)

if __name__ == '__main__':
    import argparse

    # parse parameter
    parser = argparse.ArgumentParser(description="Extract solution")
    parser.add_argument('--data_path', type=str, help='the path of inference result after merging')
    parser.add_argument('--id_path', type=str, help='the corresponding messages file which is used for inference')
    parser.add_argument('--output_path', type=str, help='the output path')
    args = parser.parse_args()

    extract_sol(args.data_path, args.id_path, args.output_path)
