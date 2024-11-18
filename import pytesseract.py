from flask import Flask, request, jsonify
import pytesseract
import cv2
import numpy as np
import re

# Set up Tesseract path if needed
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)

# Function to process image for OCR and text recognition
def process_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return "Error: Unable to load image. Check the file path."

    # Resize image
    new_width = 500
    height, width = image.shape[:2]
    aspect_ratio = width / height
    new_height = int(new_width / aspect_ratio)
    resized_image = cv2.resize(image, (new_width, new_height))

    # Convert to HSV and filter for red regions
    hsv_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)

    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])
    mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)

    red_mask = cv2.bitwise_or(mask1, mask2)
    red_regions = cv2.bitwise_and(resized_image, resized_image, mask=red_mask)

    # Convert to grayscale and enhance contrast
    gray_image = cv2.cvtColor(red_regions, cv2.COLOR_BGR2GRAY)
    contrast_image = cv2.convertScaleAbs(gray_image, alpha=3, beta=30)

    # Apply sharpening filter
    sharpening_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened_image = cv2.filter2D(contrast_image, -1, sharpening_kernel)

    # Apply binary thresholding
    _, binary_image = cv2.threshold(sharpened_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological transformations
    kernel = np.ones((1, 1), np.uint8)
    processed_image = cv2.erode(binary_image, kernel, iterations=1)
    processed_image = cv2.dilate(processed_image, kernel, iterations=1)

    # OCR with refined configuration
    text = pytesseract.image_to_string(
        processed_image, config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-*/=x'
    )

    # Correct OCR errors
    text = text.replace("S", "5").replace("o", "0").replace("O", "0").replace("I", "1").replace("l", "1")
    text = text.replace("÷", "/").replace("f", "/").replace("x", "*")

    # Parse and evaluate expressions
    expressions = re.findall(r"[A-Za-z]+\s*=\s*[\d\+\-\*/\s]+", text)
    evaluated_results = []

    for expression in expressions:
        try:
            variable, calculation = expression.split("=")
            variable = variable.strip()
            calculation = calculation.strip()
            result = eval(calculation)
            result_text = f"{variable} = {calculation} = {result}"
            evaluated_results.append(result_text)
        except Exception as e:
            evaluated_results.append(f"Could not evaluate expression: {expression}")

    return "\n".join(evaluated_results)

@app.route('/process_image', methods=['POST'])
def process_image_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    file_path = f"./{file.filename}"
    file.save(file_path)

    # Process the image and get the result
    result = process_image(file_path)

    return jsonify({"result": result})

# Main function to run the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
