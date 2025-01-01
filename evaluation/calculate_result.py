import json
import random
import statistics
from tqdm import tqdm

def load_jsonl(filename):
    with open(filename, "r") as f:
        return [json.loads(line) for line in f]

def calc_best_of_n(dataset, sol_num, ut_num, task_sol_results, task_sol_ut_results):
    sol_ids = [i for i in range(100)]
    ut_ids = [i for i in range(100)]

    accuracy = 0
    detail = []
    for data in dataset:
        task_id = data['task_id']

        # obtain the ut_id list that each solution pass
        sol_pass_ut_set = dict()
        random.shuffle(ut_ids)
        for i in range(sol_num):
            sol_id = sol_ids[i]

            for j in range(ut_num):
                ut_id = ut_ids[j]

                if sol_id not in sol_pass_ut_set:
                    sol_pass_ut_set[sol_id] = set()
                key = f"{task_id}-{sol_id}-{ut_id}"
                if key in task_sol_ut_results and task_sol_ut_results[key] == 'pass':
                    sol_pass_ut_set[sol_id].add(ut_id)

        # rerank by the passed unit test number
        sol_pass_ut_set = sorted(sol_pass_ut_set.items(), key=lambda item: len(item[1]), reverse=True)
        top_pass_ut_num = len(sol_pass_ut_set[0][1])
        top_sol_list = []
        for value in sol_pass_ut_set:
            if len(value[1]) == top_pass_ut_num:
                top_sol_list.append(value)
            else:
                break
        
        select_sol_ids = []
        max_consistency = 0
        for v1 in top_sol_list:
            consistency = 0
            for v2 in top_sol_list:
                if v1[1] == v2[1]:
                    consistency += 1
            if consistency > max_consistency:
                select_sol_ids = [v1[0]]
                max_consistency = consistency
            elif consistency == max_consistency:
                select_sol_ids.append(v1[0])

        num = 0
        for v in select_sol_ids:
            if task_sol_results[f'{task_id}-{v}'] == 'pass':
                num += 1
        accuracy += num / len(select_sol_ids)

    accuracy = round(accuracy / len(dataset), 4)               
    return accuracy

def get_result_on_sol_and_ut(benchmark, sol_model, ut_model, sol_num, ut_num, sample_num):
    dataset = load_jsonl(f'data/benchmark/input_{benchmark}_sol.jsonl')

    # label each solution
    if benchmark != 'livecodebench':
        sol_anno = load_jsonl(f'data/result/{benchmark}/sol_{sol_model}_200_anno.jsonl')
        result_key = 'plus_status'
    else:
        sol_anno = load_jsonl(f'data/result/{benchmark}/sol_{sol_model}_100_anno.jsonl')
        result_key = 'result'
    task_sol_results = dict()
    for data in tqdm(sol_anno):
        for sol_id in range(len(data['solutions'])):
            task_sol_results[f"{data['task_id']}-{sol_id}"] = data['solutions'][sol_id][result_key]

    # label each unit test
    task_sol_ut_results = dict()
    ut_result = load_jsonl(f'output/{benchmark}/{sol_model}_sol_{ut_model}_ut/details/100_sol_100_ut_result.jsonl')

    for data in tqdm(ut_result):
        task_sol_ut_results[f"{data['task_id']}-{data['sol_id']}-{data['ut_id']}"] = data['result']

    # calcluate best-of-n
    y = []
    for _ in range(sample_num):
        accuracy = calc_best_of_n(dataset, sol_num, ut_num, task_sol_results, task_sol_ut_results)
        y.append(accuracy)

    y_mean = statistics.mean(y)
    # y_std = statistics.stdev(y)

    print(f"y_mean: {y_mean}")
    # print(f"y_std: {y_std}")

if __name__ == '__main__':
    import argparse

    # parse parameter
    parser = argparse.ArgumentParser(description="calculate result")
    parser.add_argument('--benchmark', type=str, help='evaluate benchmark')
    parser.add_argument('--sol_model', type=str, help='the model that generate solutions')
    parser.add_argument('--ut_model', type=str, help='the model that generate unit test')
    parser.add_argument('--sol_num', type=int, help='the number of generated solutions')
    parser.add_argument('--ut_num', type=int, help='the number of generated unit test')
    parser.add_argument('--sample_num', type=int, help='the number of bootstrape sampling')
    args = parser.parse_args()

    get_result_on_sol_and_ut(args.benchmark, args.sol_model, args.ut_model, args.sol_num,
                            args.ut_num, args.sample_num)
