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

## ソルバー

- [solver.py](../sudoku_solver/solver.py): `generate_sudoku.ipynb`のバックトラッキングを移植。`is_valid_board`で読み取り結果の矛盾（OCR誤読による重複）を事前検出し、`solve_board`は入力を破壊せず解を返す（無効/解なしは`None`）
- `pipeline.solve_sudoku_from_image(image_path)`で画像→解答までを一気通貫実行。矛盾/解なしは`UnsolvableGridError`

## 数字認識の精度改善（2026-09-13時点）

`old/sudoku.jpg`（81マス、正解既知）を使って`tests/test_digit_recognition.py`で継続的に精度検証している。

- 発見した問題と対策:
  1. `is_blank_cell`が常に`False`を返す不具合があった。原因は`remove_border`の固定比率クロップでは太い外枠（盤面外周・3x3ブロック境界）を除去しきれず、Otsu二値化が「ほぼ均一に明るいだけ」の空白セルに対しても無理に閾値を作ってノイズを前景と誤判定していたこと。
     - 対策1: `remove_grid_lines`（[cells.py](../sudoku_solver/cells.py)）を追加。セル四辺から内側へスキャンし、辺に接する暗画素だけを罫線の太さに関わらず除去する
     - 対策2: Otsu二値化をやめ、固定の明度閾値(150)で暗画素比率を見る方式に変更（空白セルは0%、数字セルは8〜14%と明確に分離することを確認済み）
  2. pytesseract（`--psm 10`）は56x56にリサイズしただけの画像だと余白が少なく誤読しやすい（8→9等のグリフ混同）。数字の周囲に白い余白(`copyMakeBorder`)を追加したところ改善した
  3. `--psm 10`は「単一文字」を指定していても稀に複数文字を返すことがある（例: "68"）。数独は1桁しかありえないので、長さ1の数字以外は0（空白）扱いにするガードを追加
  - 精度推移: 68/81 → 75/81（罫線除去+固定閾値） → 78/81（余白追加+複数文字ガード）
  - 「連結成分分析で最大の塊だけ残す」処理も試したが、数字の一部が別成分に分離されるケースで逆に精度が下がったため不採用（`git log`参照、コードには残していない）
- 残る3マスの誤り（見逃し、誤った数字への誤読ではない）はいずれもpytesseract自体のグリフ認識の限界と見られる。空白への見逃しは無効な数独を作らないため、間違った数字を書き込むより実害が小さい
- 現状は`--psm 10`のパラメータ調整でここまで改善したが、手書き文字や多様なフォントに対応するにはいずれ自前の軽量CNN（0〜9の10クラス分類器）が必要になりそう。`generate_sudoku.ipynb`をフォント・ノイズ・回転ありに拡張し学習データを合成する案は保留中

## 既知の課題

1. **テスト写真が1枚しかない**（`old/sudoku.jpg`は盤面がほぼ画像いっぱいで、フチも綺麗）。背景に物が写り込む・斜めから撮る・影が入るなど、実際のスマホ写真を想定した頑健性は未検証。角度・照明・背景を変えた写真を数枚追加してテストする必要がある
2. **回転した盤面へのHoughフォールバック非対応**: 現状は軸に沿ったグリッドのみ想定。回転写真の頑健性が必要になったら、直線のクラスタリング＋交点計算に拡張する

## 次のアクション候補

- 実際のスマホ写真を数枚集めて `tests/` に追加し、グリッド検出の頑健性を再評価する
- 合成的な頑健性テスト（画像を回転・変形・ノイズ付加してグリッド検出をテスト）
- 手書き・多様なフォント対応のための軽量CNN数字分類器の検討
