from tqdm import tqdm
from utils import load_jsonl, save_jsonl

def merge_output(mp_num, input_dir):
    dataset = []
    for i in tqdm(range(mp_num)):
        dataset.extend(load_jsonl(f'{input_dir}/output_gpu_{i}.jsonl'))
    
    save_jsonl(f'{input_dir}/merge_result.jsonl', dataset)

if __name__ == '__main__':
    import argparse

    # parse parameter
    parser = argparse.ArgumentParser(description="Merge output")
    parser.add_argument('--mp_num', type=int, help='the multiprocess number for inference')
    parser.add_argument('--input_dir', type=str, help='the path of input dir')
    args = parser.parse_args()

    merge_output(args.mp_num, args.input_dir)
