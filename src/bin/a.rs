use itertools::Itertools;
use proconio::{input, marker::Chars};
use rand::prelude::*;
use rand_chacha::ChaCha20Rng;

// 定数 入力は捨てglobalに定義
const N: usize = 100;
const K: usize = 8;
const H: usize = 50;
const W: usize = 50;
const T: usize = 2500;

// 型の定義
type Mat = Vec<Vec<char>>;
type Action = usize;
type ScoreType = i32;
type Output = String;

// グリッド探索用
const DIJ: [(usize, usize); 4] = [(0, !0), (0, 1), (!0, 0), (1, 0)];
const DIR: [char; 4] = ['L', 'R', 'U', 'D'];

// 好みで変更する
const TIME_LIMIT: f64 = 3.9;
const SEED: u64 = 20210325;

/// 時間を管理するクラス
struct TimeKeeper {
    start_time_: f64,
    time_threshold_: f64,
}
impl TimeKeeper {
    /// 時間制限を秒単位で指定してインスタンスをつくる。
    pub fn new(time_threshold: f64) -> Self {
        TimeKeeper {
            start_time_: Self::get_time(),
            time_threshold_: time_threshold,
        }
    }
    /// インスタンス生成した時から指定した時間制限を超過したか判断する。
    pub fn is_timeover(&self) -> bool {
        Self::get_time() - self.start_time_ - self.time_threshold_ >= 0.
    }
    /// インスタンスを生成した時(0.0)から指定した時間制限(1.0)までの割合を返す
    /// 焼きなましのときに使う
    pub fn _ratio(&self) -> f64 {
        (Self::get_time() - self.start_time_) / self.time_threshold_
    }
    /// 経過時間をミリ秒単位で返す
    pub fn time(&self) -> usize {
        ((Self::get_time() - self.start_time_) * 1000.) as usize
    }
    fn get_time() -> f64 {
        let t = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap();
        t.as_secs() as f64 + t.subsec_nanos() as f64 * 1e-9
    }
}

#[derive(Debug, Clone)]
struct Board {
    turn_: usize,
    id_: usize,
    character_: (usize, usize),
    seen_: Vec<Vec<bool>>,
    game_score_: ScoreType,
    evaluated_score_: ScoreType,
}

impl Board {
    fn new(maps: &Vec<Mat>, id: usize) -> Self {
        let mut _character = vec![];
        let mut seen_ = vec![vec![false; W]; H];
        for i in 0..H {
            for j in 0..W {
                if maps[id][i][j] == '@' {
                    _character.push((i, j));
                    seen_[i][j] = true;
                    break;
                }
            }
        }
        if let Some(character_) = _character.pop() {
            Board {
                turn_: 0,
                id_: id,
                character_,
                seen_,
                game_score_: 0,
                evaluated_score_: 0,
            }
        } else {
            panic!()
        }
    }

    /// [どのゲームでも実装する]: 探索用の盤面評価をする
    /// 探索ではゲーム本来のスコアに別の評価値をプラスするといい探索ができるので、ここに工夫の余地がある。
    pub fn evaluate_score(&mut self) {
        self.evaluated_score_ = self.game_score_;
    }

    /// [どのゲームでも実装する]: ゲームの終了判定
    pub fn is_done(&self) -> bool {
        self.turn_ == T
    }
    /// [どのゲームでも実装する]: 指定したactionでゲームを1ターン進める
    pub fn advance(&mut self, maps: &Vec<Mat>, action: Action) {
        let ni = self.character_.0.wrapping_add(DIJ[action].0);
        let nj = self.character_.1.wrapping_add(DIJ[action].1);
        self.turn_ += 1;
        if maps[self.id_][ni][nj] == '#' {
            // 向かう先が壁なら何もしない(移動もしない)
            return;
        }
        // キャラクターの位置更新
        self.character_.0 = ni;
        self.character_.1 = nj;

        if maps[self.id_][ni][nj] == 'x' {
            // 移動先が罠ならその盤面は終了
            self.turn_ = T;
            return;
        }

        // 移動先が初めて通るところならばコインが存在する
        if !self.seen_[ni][nj] {
            self.game_score_ += 1;
            self.seen_[ni][nj] = true;
        }
    }
}

/// 100盤面から8盤面をランダムに選ぶ
fn choice_boards(rng: &mut ChaCha20Rng, _maps: &Vec<Mat>) -> Vec<usize> {
    let mut ret = (0..N).into_iter().collect::<Vec<_>>();
    ret.shuffle(rng);
    while ret.len() > K {
        ret.pop();
    }
    ret
}

/// 4方向の移動を試し、選んだ8盤面それぞれに適用して一番スコアのいい移動の方向を返す
fn greedy_action(maps: &Vec<Mat>, boards: &Vec<Board>) -> Option<Action> {
    let mut best_action = !0;
    let mut best_score = std::i32::MIN;
    for action in 0..4 {
        let mut score = 0;
        for i in 0..K {
            let mut board = boards[i].clone();
            if board.is_done() {
                // 罠にハマってる盤面は無視
                continue;
            }
            board.advance(maps, action);
            board.evaluate_score();
            score += board.evaluated_score_;
        }
        if score > best_score {
            best_score = score;
            best_action = action;
        }
    }
    if best_action != !0 {
        return Some(best_action);
    }
    None
}

fn main() {
    input! {
        _n:usize,
        _k:usize,
        _h:usize,
        _w:usize,
        _t:usize,
        maps: [[Chars;H];N],
    }
    let timekeeper = TimeKeeper::new(TIME_LIMIT);
    let mut rng = ChaCha20Rng::seed_from_u64(SEED);

    let choice = choice_boards(&mut rng, &maps);
    // 選んだ番号からBoardを生成
    let mut boards = choice
        .iter()
        .map(|&i| Board::new(&maps, i))
        .collect::<Vec<_>>();

    let mut turn = 0;
    let mut output: Output = String::new();
    while turn < T {
        if timekeeper.is_timeover() {
            break;
        }
        if let Some(action) = greedy_action(&maps, &boards) {
            turn += 1;
            output.push(DIR[action]);
            for i in 0..K {
                boards[i].advance(&maps, action);
            }
        }
    }
    println!("{}", choice.iter().join(" "));
    println!("{}", output);
    eprintln!("{}", timekeeper.time());
}
