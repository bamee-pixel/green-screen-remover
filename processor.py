import cv2
import numpy as np
import base64

def hex_to_hsv(hex_color):
    """
    Converts hex color string to HSV numpy array (OpenCV scale).
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Create a 1x1 image of this color to use cv2.cvtColor for accurate conversion
    # OpenCV expects BGR
    bgr_pixel = np.uint8([[[b, g, r]]])
    hsv_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2HSV)
    return hsv_pixel[0][0]

def process_image(image_data, color_hex, threshold, smoothing):
    """
    Processes the image to remove the background color.

    Args:
        image_data: Raw bytes of the image file.
        color_hex: Hex string of the color to remove (e.g., "#00FF00").
        threshold: Sensitivity (0-100).
        smoothing: Edge smoothing intensity (0-100).

    Returns:
        Processed image bytes (PNG format).
    """
    # Decode image
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

    if img is None:
        raise ValueError("Could not decode image")

    # Ensure image has 4 channels (BGRA) for transparency
    if img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

    # Convert to HSV for color detection
    # We only convert the BGR part of the image
    hsv_img = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2HSV)

    # Get target HSV
    target_hsv = hex_to_hsv(color_hex)
    h_target, s_target, v_target = target_hsv

    # Calculate bounds based on threshold
    # Threshold 0-100 maps to sensitivity ranges
    # Hue: +/- (threshold * 0.9) (Max 90 degrees deviation approx)
    # Saturation: we usually want to filter out low saturation (gray/white)
    # Value: we usually want to filter out very dark or very bright if specific

    t_val = int(threshold)

    # Hue range (0-179 in OpenCV)
    # We scale threshold to be reasonable for Hue (e.g. max +/- 30 or 40 for standard green screen)
    # But if user selects a color, they might want wider.
    # Let's say max range is +/- 45 degrees (which is 90 total)
    h_sens = int(t_val * 0.6)
    s_sens = int(t_val * 1.5) + 20 # Base variance allowed
    v_sens = int(t_val * 1.5) + 40 # Base variance allowed

    lower_bound = np.array([
        max(0, h_target - h_sens),
        max(0, s_target - s_sens),
        max(0, v_target - v_sens)
    ])

    upper_bound = np.array([
        min(179, h_target + h_sens),
        min(255, s_target + s_sens),
        min(255, v_target + v_sens)
    ])

    # Create mask
    mask = cv2.inRange(hsv_img, lower_bound, upper_bound)

    # Wrap-around for Hue (Red is near 0 and 179)
    if h_target - h_sens < 0:
        lower_wrap = np.array([179 + (h_target - h_sens), max(0, s_target - s_sens), max(0, v_target - v_sens)])
        upper_wrap = np.array([179, min(255, s_target + s_sens), min(255, v_target + v_sens)])
        mask2 = cv2.inRange(hsv_img, lower_wrap, upper_wrap)
        mask = cv2.bitwise_or(mask, mask2)
    elif h_target + h_sens > 179:
        lower_wrap = np.array([0, max(0, s_target - s_sens), max(0, v_target - v_sens)])
        upper_wrap = np.array([(h_target + h_sens) - 179, min(255, s_target + s_sens), min(255, v_target + v_sens)])
        mask2 = cv2.inRange(hsv_img, lower_wrap, upper_wrap)
        mask = cv2.bitwise_or(mask, mask2)

    # Invert mask (we want to KEEP the non-green parts)
    # mask: 255 where green, 0 where not.
    # We want alpha: 0 where green, 255 where not.
    alpha_mask = cv2.bitwise_not(mask)

    # Advanced Features: Smoothing
    if smoothing > 0:
        # Morphological open/close to remove noise
        kernel_size = int(smoothing / 20) + 1
        kernel = np.ones((kernel_size, kernel_size), np.uint8)

        # Remove small white spots in the background mask (green spots in foreground)
        # alpha_mask = cv2.morphologyEx(alpha_mask, cv2.MORPH_OPEN, kernel)
        # Remove small black spots in the foreground (non-green spots in background)
        # alpha_mask = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kernel)

        # Blur the edges for softness
        blur_amount = int(smoothing / 5) * 2 + 1 # Must be odd
        if blur_amount > 1:
            alpha_mask = cv2.GaussianBlur(alpha_mask, (blur_amount, blur_amount), 0)

    # Apply Spill Suppression
    # "Step 3... Spill suppression (remove green color bleeding on edges)"
    # A simple way is to desaturate the pixels that were close to being masked but weren't.
    # Or, simpler: convert the green pixels in the image to gray/black before making them transparent
    # so that semi-transparent edges don't look green.

    # For now, let's just update the Alpha channel.

    # Split channels
    b, g, r, a = cv2.split(img)

    # Update alpha
    # If the original image already had transparency, we combine it.
    final_alpha = cv2.bitwise_and(a, alpha_mask)

    img_result = cv2.merge((b, g, r, final_alpha))

    # Encode back to PNG
    success, encoded_img = cv2.imencode('.png', img_result)
    if not success:
        raise ValueError("Could not encode image")

    return encoded_img.tobytes()
