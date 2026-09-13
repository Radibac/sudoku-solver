"""スマホ写真から数独の盤面（9x9グリッド）を検出し、正面ビューに補正する。

old/sudoku-test.ipynb のプロトタイプを土台に、以下の点を堅牢化している:
- RETR_EXTERNAL だけでなく RETR_LIST も候補にし、面積・正方形らしさでフィルタする
- approxPolyDP が厳密に4頂点へ収束しない場合は minAreaRect でフォールバックする
- 輪郭ベースの検出が失敗した場合、Hough変換で検出した直線群から盤面の外接矩形を推定する
  （回転にはあまり強くないが、輪郭が崩れやすい低コントラストな写真でのフォールバックとして使う）
"""

import cv2
import numpy as np


class GridNotFoundError(RuntimeError):
    """画像から数独の盤面らしき四角形が見つからなかった場合に送出する。"""


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """グレースケール画像から二値化画像を作る。image はグレースケール1chを想定。"""
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    return cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )


def order_points(pts: np.ndarray) -> np.ndarray:
    """4頂点を [左上, 右上, 左下, 右下] の順に並べ替える。"""
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[3] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[2] = pts[np.argmax(diff)]

    return rect


def _quad_aspect_ratio(rect: np.ndarray) -> float:
    """order_points 済みの4頂点から縦横比 (幅/高さ) を計算する。"""
    top_left, top_right, bottom_left, bottom_right = rect
    width = (np.linalg.norm(top_right - top_left) + np.linalg.norm(bottom_right - bottom_left)) / 2
    height = (np.linalg.norm(bottom_left - top_left) + np.linalg.norm(bottom_right - top_right)) / 2
    if height == 0:
        return 0.0
    return width / height


def _find_grid_corners_contour(
    binary_image: np.ndarray,
    min_area_ratio: float,
    max_aspect_deviation: float,
) -> np.ndarray | None:
    """輪郭ベースの検出。見つからない場合は None を返す（例外は上位で判断する）。"""
    image_area = binary_image.shape[0] * binary_image.shape[1]
    contours, _ = cv2.findContours(binary_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < image_area * min_area_ratio:
            continue

        hull = cv2.convexHull(contour)
        peri = cv2.arcLength(hull, True)
        approx = cv2.approxPolyDP(hull, 0.02 * peri, True)

        if len(approx) == 4:
            pts = approx.reshape(4, 2).astype("float32")
        else:
            # 頂点数がぴったり4に収束しない場合は、外接する最小回転矩形で近似する
            rotated = cv2.minAreaRect(hull)
            pts = cv2.boxPoints(rotated).astype("float32")

        rect = order_points(pts)
        aspect = _quad_aspect_ratio(rect)
        if aspect == 0 or abs(aspect - 1.0) > max_aspect_deviation:
            continue

        candidates.append((area, rect))

    if not candidates:
        return None

    candidates.sort(key=lambda c: c[0], reverse=True)
    return candidates[0][1]


def _find_grid_corners_hough(
    gray_image: np.ndarray,
    min_line_length_ratio: float = 0.4,
) -> np.ndarray | None:
    """Hough変換で検出した直線群の外接範囲から盤面の4頂点を推定する。

    輪郭ベースの検出が失敗するような、低コントラスト・グリッド線が輪郭として
    繋がりにくい写真向けのフォールバック。回転した盤面には対応できない
    （軸に沿ったグリッドを前提とする）。
    """
    h, w = gray_image.shape
    edges = cv2.Canny(gray_image, 50, 150)
    min_line_length = int(min(h, w) * min_line_length_ratio)
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=80,
        minLineLength=min_line_length, maxLineGap=10,
    )
    if lines is None:
        return None

    horizontal_ys = []
    vertical_xs = []
    for line in lines[:, 0]:
        x1, y1, x2, y2 = line
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if abs(angle) < 10 or abs(abs(angle) - 180) < 10:
            horizontal_ys.extend([y1, y2])
        elif abs(abs(angle) - 90) < 10:
            vertical_xs.extend([x1, x2])

    if not horizontal_ys or not vertical_xs:
        return None

    top, bottom = min(horizontal_ys), max(horizontal_ys)
    left, right = min(vertical_xs), max(vertical_xs)
    if bottom - top < min_line_length or right - left < min_line_length:
        return None

    pts = np.array(
        [[left, top], [right, top], [left, bottom], [right, bottom]], dtype="float32"
    )
    return order_points(pts)


def _has_min_ink_ratio(binary_image: np.ndarray, rect: np.ndarray, min_ink_ratio: float) -> bool:
    """候補領域の内部に、グリッド線や数字（黒画素）が最低限含まれているかを確認する。

    真っ白な紙や壁のような「四角いが中身が何もない」領域を盤面と誤検出するのを防ぐ。
    binary_image は preprocess_image の出力（THRESH_BINARY）で、黒(0)がインク部分。
    """
    x, y, w, h = cv2.boundingRect(rect.astype(np.int32))
    x, y = max(x, 0), max(y, 0)
    crop = binary_image[y:y + h, x:x + w]
    if crop.size == 0:
        return False
    ink_ratio = float(np.count_nonzero(crop == 0)) / crop.size
    return ink_ratio >= min_ink_ratio


def find_grid_corners(
    gray_image: np.ndarray,
    binary_image: np.ndarray,
    min_area_ratio: float = 0.15,
    max_aspect_deviation: float = 0.25,
    min_ink_ratio: float = 0.01,
) -> np.ndarray:
    """グレースケール画像から数独盤面と思われる四角形の4頂点を返す（order_points済み）。

    まず輪郭ベースの検出を試み、失敗した場合はHough変換によるフォールバックを試す。
    どちらの経路で見つかった候補も、縦横比とインク量（グリッド線・数字の有無）で最終検証する。

    min_area_ratio: 画像全体に対する最小面積比。これより小さい輪郭は候補から除外する。
    max_aspect_deviation: 縦横比1.0からの許容ずれ。数独盤面はほぼ正方形であるという前提。
    min_ink_ratio: 候補領域内に必要な最低限の黒画素比率。真っ白な領域の誤検出を防ぐ。
    """
    rect = _find_grid_corners_contour(binary_image, min_area_ratio, max_aspect_deviation)

    if rect is None:
        hough_rect = _find_grid_corners_hough(gray_image)
        if hough_rect is not None:
            aspect = _quad_aspect_ratio(hough_rect)
            if aspect != 0 and abs(aspect - 1.0) <= max_aspect_deviation:
                rect = hough_rect

    if rect is not None and _has_min_ink_ratio(binary_image, rect, min_ink_ratio):
        return rect

    raise GridNotFoundError(
        "数独の盤面らしき四角形が見つかりませんでした（輪郭・Hough変換のいずれでも検出失敗）。"
        "min_area_ratio / max_aspect_deviation / min_ink_ratio の調整、または撮影条件の見直しが必要です。"
    )


def warp_to_square(image: np.ndarray, rect: np.ndarray) -> np.ndarray:
    """order_points済みの4頂点を使って正面ビューへ透視変換する。"""
    top_left, top_right, bottom_left, bottom_right = rect
    side = max(
        np.linalg.norm(top_left - bottom_right),
        np.linalg.norm(top_right - bottom_left),
    )
    if side < 10:
        raise GridNotFoundError(f"検出された盤面サイズが小さすぎます（side={side:.1f}px）。")

    dst = np.array(
        [[0, 0], [side - 1, 0], [0, side - 1], [side - 1, side - 1]], dtype="float32"
    )
    matrix = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, matrix, (int(side), int(side)))


def detect_grid(image_path: str) -> tuple[np.ndarray, np.ndarray]:
    """画像ファイルから数独盤面を検出し、正面ビューに補正した画像と4頂点を返す。"""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"画像の読み込みに失敗しました: {image_path}")

    binary = preprocess_image(img)
    rect = find_grid_corners(img, binary)
    warped = warp_to_square(img, rect)
    return warped, rect
