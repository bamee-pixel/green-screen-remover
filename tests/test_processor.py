import cv2
import numpy as np
import pytest
from processor import process_image, hex_to_hsv

def test_hex_to_hsv():
    # Green #00FF00
    # In OpenCV HSV: H=60, S=255, V=255.
    # Hue range 0-179. 60 degrees is 30 in OpenCV? No, OpenCV Hue is 0-179 (degrees/2).
    # Green is 120 degrees. 120/2 = 60.
    hsv = hex_to_hsv('#00FF00')
    assert hsv[0] == 60 # Hue
    assert hsv[1] == 255 # Sat
    assert hsv[2] == 255 # Val

def test_process_image_green_screen():
    # Create a simple image: Green background with a Red square
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:] = (0, 255, 0) # Green background (BGR)

    # Red square in the middle
    cv2.rectangle(img, (40, 40), (60, 60), (0, 0, 255), -1)

    success, encoded = cv2.imencode('.png', img)
    image_bytes = encoded.tobytes()

    result_bytes = process_image(image_bytes, "#00FF00", threshold=50, smoothing=0)

    # Decode result
    nparr = np.frombuffer(result_bytes, np.uint8)
    result_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

    # Check dimensions
    assert result_img.shape[0] == 100
    assert result_img.shape[1] == 100
    assert result_img.shape[2] == 4 # BGRA

    # Check center (Red square) - should be opaque
    center_pixel = result_img[50, 50]
    assert center_pixel[3] == 255 # Alpha 255
    assert center_pixel[2] == 255 # R 255

    # Check corner (Green background) - should be transparent
    corner_pixel = result_img[10, 10]
    assert corner_pixel[3] == 0 # Alpha 0

def test_process_image_no_green():
    # Red image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:] = (0, 0, 255)

    success, encoded = cv2.imencode('.png', img)
    image_bytes = encoded.tobytes()

    result_bytes = process_image(image_bytes, "#00FF00", threshold=50, smoothing=0)

    nparr = np.frombuffer(result_bytes, np.uint8)
    result_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

    # Should be all opaque
    assert result_img[50, 50][3] == 255
