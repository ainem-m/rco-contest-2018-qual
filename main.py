from typing import List, Tuple, Optional
from time import time
import sys
import random

#####
# サンプルコード
# 100盤面の中から8盤面をランダムに選ぶ
# 各ターンごとに一番スコアの高くなる方向を選ぶ貪欲法
# 2200ms 10,000点ぐらい


# 定数たち：入力は捨ててglobalに定義
N: int = 100
K: int = 8
H: int = 50
W: int = 50
T: int = 2500
INF: int = 1000000

# 型の定義
Action = int
Actions = List[int]
ScoreType = int
Output = List[str]
Coordinate = Tuple[int, int]

# グリッド探索用
DIJ: List[Coordinate] = [(0, -1), (0, 1), (-1, 0), (1, 0)]
DIR: List[str] = ["L", "R", "U", "D"]

# 好みで変更する
TIME_LIMIT: float = 3.9
SEED: int = 20210325


def eprint(*args, **kwargs):
    """標準エラー出力に出力するprint"""
    print(*args, file=sys.stderr, **kwargs)


class Board:
    """一つの盤面の状態を表すクラス
    maps List[List[str]]: 入力で与えられる盤面
    id int: 選ぶ盤面のid
    seen List[List[bool]]: キャラが通ったかどうか
    character Tuple[int, int]: キャラの現在地座標
    turn int: 経過ターン、罠にハマっている場合はturn==T
    game_score ScoreType: その盤面で獲得したスコア
    evaluated_score ScoreType: 盤面探索用の評価値
    """

    def __init__(
        self,
        maps: List[List[str]],
        id: int,
        seen: List[List[bool]] = [],
        character: Tuple[int, int] = tuple(),
        turn: int = 0,
        game_score: ScoreType = 0,
        evaluated_score: ScoreType = 0,
    ) -> None:
        # それぞれ初期値が与えられている場合はその値で初期化する
        self.seen_ = [[False for _ in range(W)] for _ in range(H)]
        if seen:
            self.seen_ = [seen[i][:] for i in range(H)]
        if not character:
            for i in range(H):
                for j in range(W):
                    if maps[id][i][j] == "@":
                        self.character_: Coordinate = (i, j)
                        self.seen_[i][j] = True
                        break
        else:
            self.character_ = character
        self.turn_: int = 0 if not turn else turn
        self.id_: int = id
        self.game_score_: int = 0 if not game_score else game_score
        self.evaluated_score_: int = 0 if not evaluated_score else evaluated_score

    def evaluate_score(self) -> None:
        """
        [どのゲームでも実装する]: 探索用の盤面評価をする
        探索ではゲーム本来のスコアに別の評価値をプラスするといい探索ができるので、ここに工夫の余地がある。
        """
        self.evaluated_score_ = self.game_score_

    def is_done(self) -> bool:
        """
        [どのゲームでも実装する]: ゲームの終了判定
        """
        return self.turn_ == T

    def advance(self, maps: List[List[str]], action: Action) -> None:
        """
        [どのゲームでも実装する]: 指定したactionでゲームを1ターン進める
        """
        ni: int = self.character_[0] + DIJ[action][0]
        nj: int = self.character_[1] + DIJ[action][1]
        self.turn_ += 1
        if maps[self.id_][ni][nj] == "#":
            # 向かう先が壁なら何もしない(移動もしない)
            return
        # キャラクターの位置更新
        self.character_ = (ni, nj)

        if maps[self.id_][ni][nj] == "x":
            # 移動先が罠ならその盤面は終了
            self.turn_ = T
            return

        # 移動先が初めて通るところならばコインが存在する
        if not self.seen_[ni][nj]:
            self.game_score_ += 1
            self.seen_[ni][nj] = True

    def peek(self, maps, action):
        ni: int = self.character_[0] + DIJ[action][0]
        nj: int = self.character_[1] + DIJ[action][1]
        return maps[self.id_][ni][nj] == 'o' and not self.seen_[ni][nj]


def show(maps: List[List[str]], board: Board) -> None:
    """盤面クラスの状態を標準エラーに出力する

    Args:
        maps (List[List[str]]): 入力で与えられる盤面
        board (Board): 表示したい盤面クラス
    """
    for i in range(H):
        for j in range(W):
            if board.seen_[i][j]:
                eprint("\x1b[46m@\x1b[0m ", end="")
            else:
                eprint(maps[board.id_][i][j], "",  end="")
        eprint()


def clone(maps: List[List[str]], board: Board) -> Board:
    """盤面クラスの複製
    pythonはこれが絶望的に遅い

    Args:
        maps (List[List[str]]): 入力で与えられる盤面
        board (Board): 複製したい盤面クラス

    Returns:
        Board: 複製した盤面クラス
    """
    return Board(
        maps,
        id=board.id_,
        seen=board.seen_,
        character=board.character_,
        turn=board.turn_,
        game_score=board.game_score_,
        evaluated_score=board.evaluated_score_,
    )


def choice_boards(maps: List[List[str]]) -> List[int]:
    """ランダムに100盤面から8盤面を選ぶ

    Args:
        maps (List[List[str]]): 入力で与えられる盤面

    Returns:
        List[int]: 選んだ8盤面のID
    """
    ret = [i for i in range(N)]
    random.shuffle(ret)
    return ret[:8]


def greedy_action(maps: List[List[str]], boards: List[Board]) -> Optional[int]:
    """4方向の移動を試し、選んだ8盤面それぞれに適用して一番スコアのいい移動の方向を返す

    Args:
        maps (List[List[str]]): 入力で与えられる盤面
        boards (List[Board]): 盤面

    Returns:
        Optional[int]: 良い行動が見つからなかった場合Noneを返す
    """
    best_action: Action = -1
    best_score: ScoreType = -INF
    for action in range(4):
        score: int = 0
        for i in range(K):
            board: Board = clone(maps, boards[i])
            if board.is_done():
                # 罠にハマってる盤面は無視
                continue
            board.advance(maps, action)
            board.evaluate_score()
            score += board.evaluated_score_
        if score > best_score:
            best_score = score
            best_action = action
    if best_action >= 0:
        return best_action
    else:
        return None


def main():
    _ = input()  # N, K, H, W, Tは受け取らずglobalで定義
    maps: List[List[str]] = [[input() for _ in range(H)] for _ in range(N)]
    start_time: float = time()
    random.seed(SEED)  # SEED値を固定
    choice: List[int] = choice_boards(maps)
    boards: List[Board] = [Board(maps, i) for i in choice]
    turn: int = 0
    output: Output = []
    loop_cnt: int = 0
    while turn < T:
        loop_cnt += 1
        action: Action = greedy_action(maps, boards)
        if action is None:
            break
        turn += 1
        output.append(DIR[action])
        for i in range(K):
            boards[i].advance(maps, action)
    print(" ".join(str(i) for i in choice))
    print("".join(output))
    eprint(f"loop = {loop_cnt}")
    eprint(f"time = {time() - start_time:.3f} s")


if __name__ == "__main__":
    main()
