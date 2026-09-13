# スマホ写真からの数独読み取り ロードマップ

## ゴール
スマホで撮影した数独の写真から盤面を読み取り、9x9の数値配列として取得する。
将来的には印刷物・手書きの両方に対応したい。

## 全体パイプライン

1. **グリッド検出** — 実装済み（[sudoku_solver/grid_detection.py](../sudoku_solver/grid_detection.py)）
2. **セル分割・空白判定** — 実装済み（[sudoku_solver/cells.py](../sudoku_solver/cells.py)）
3. **数字認識** — 実装済み・精度は要改善（[sudoku_solver/digit_recognition.py](../sudoku_solver/digit_recognition.py)）
4. **エンドツーエンド接続** — 実装済み（[sudoku_solver/pipeline.py](../sudoku_solver/pipeline.py)）
5. ソルバーへ接続 — 未着手

## 現状の資産

- [generate_sudoku.ipynb](../generate_sudoku.ipynb): 合成盤面の生成・描画（学習データ生成用に転用予定、現状は未接続）
- [old/sudoku-test.ipynb](../old/sudoku-test.ipynb): 実写真(`sudoku.jpg`)に対するグリッド検出〜数字認識の最初のプロトタイプ（`/old`に移動済み。ロジックは`sudoku_solver/`パッケージに引き継いで堅牢化した）
  - EasyOCR単体での数字認識は精度が低いことを確認済み（[old/easyocr.png](../old/easyocr.png)参照）→ `pytesseract`を採用する根拠になった

## sudoku_solver パッケージ

notebook内の重複定義を解消し、以下のモジュールに切り出し済み。`tests/`にpytestを整備している。

- **[grid_detection.py](../sudoku_solver/grid_detection.py)**: 画像から盤面の4頂点を検出し、正面ビューに透視変換する
  - 輪郭ベース検出: `RETR_LIST` + 面積フィルタ + 縦横比フィルタ（正方形に近いか）。`approxPolyDP`が4頂点に収束しない場合は`minAreaRect`でフォールバック
  - Hough変換フォールバック: 輪郭ベースが失敗した場合、`HoughLinesP`で検出した直線群の外接範囲から4隅を推定（軸に沿ったグリッドのみ対応、回転には非対応）
  - 最終検証: 縦横比とインク量（内部に黒画素が一定割合あるか）をチェックし、白紙などの誤検出を除外
  - 見つからない場合は`GridNotFoundError`を送出
- **[cells.py](../sudoku_solver/cells.py)**: 正方形画像を9x9セルに分割し（`split_into_cells`）、外周を切り落とした上で黒画素比率から空白セルを判定する（`is_blank_cell`）
- **[digit_recognition.py](../sudoku_solver/digit_recognition.py)**: セル画像1枚から`pytesseract`（`--psm 10`、数字のみのホワイトリスト）で1文字認識する
- **[pipeline.py](../sudoku_solver/pipeline.py)**: 上記3つを繋いだ`read_sudoku_from_image(image_path)`

## 既知の課題

1. **テスト写真が1枚しかない**（`old/sudoku.jpg`は盤面がほぼ画像いっぱいで、フチも綺麗）。背景に物が写り込む・斜めから撮る・影が入るなど、実際のスマホ写真を想定した頑健性は未検証。角度・照明・背景を変えた写真を数枚追加してテストする必要がある
2. **数字認識の精度が低い**: `old/sudoku.jpg`での動作確認では、81マス中の半分以上が空白と誤判定されるか、誤った数字を読んでしまう（例: セル境界の線が"1"のように誤読される）。原因の切り分けが必要:
   - `remove_border`の切り落とし幅が最適か
   - 二値化・リサイズの前処理がpytesseractに適しているか
   - フォント混在（手書き・印刷）に対応するには、いずれ自前の軽量CNN（0〜9の10クラス分類器）が必要になりそう。`generate_sudoku.ipynb`をフォント・ノイズ・回転ありに拡張し学習データを合成する案は保留中
3. **回転した盤面へのHoughフォールバック非対応**: 現状は軸に沿ったグリッドのみ想定。回転写真の頑健性が必要になったら、直線のクラスタリング＋交点計算に拡張する

## 次のアクション候補

- 実際のスマホ写真を数枚集めて `tests/` に追加し、グリッド検出の頑健性を再評価する
- 数字認識の誤読・見逃しについて、セルごとの中間画像を可視化して原因を切り分ける
- ソルバー（[generate_sudoku.ipynb](../generate_sudoku.ipynb)内の`solve`相当のロジック）と`pipeline.read_sudoku_from_image`を接続する
