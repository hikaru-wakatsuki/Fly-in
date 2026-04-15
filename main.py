import sys
from pydantic import ValidationError
from parse_input_file import Zone, DronesNetwork, parse_input_file
from create_graph import create_graph
from typing import Dict, List, Tuple
from drones_scheduler import run_simulation
from output_visualize import visualize


def main() -> None:
    """
    ドローンシミュレーションの処理フローを制御

    実行手順:
        1. コマンドライン引数の検証
        2. 入力ファイルを解析し `DronesNetwork` を生成
        3. ネットワークからグラフを構築
        4. 使用する経路数を決定
        5. スタートからゴールまでの複数経路を探索
        6. シミュレーションを実行しログを生成
        7. ログを出力
        8. 可視化を実行
    """
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <input_file>")
        sys.exit(1)
    if len(sys.argv) == 2:

        try:
            network: DronesNetwork = parse_input_file(sys.argv[1])
        except (ValidationError, TypeError, ValueError) as error:
            print(error)
            sys.exit(1)

        try:
            graph: Dict[Zone, List[Tuple[Zone, int]]] = create_graph(network)
        except ValueError as error:
            print(error)
            sys.exit(1)

        logs: List[List[str]] = run_simulation(
            network.nb_drones, network.start_hub, network.end_hub,
            graph)

        for log in logs:
            print(" ".join(log))
        visualize(logs, graph, network.start_hub, network.nb_drones)


if __name__ == "__main__":
    main()
