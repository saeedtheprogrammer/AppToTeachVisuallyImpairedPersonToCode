from flask import Flask, request, jsonify, send_from_directory  # Import send_from_directory for serving files
import cv2
import numpy as np
import base64
import re

app = Flask(__name__)

@app.route('/')
def index():
    # Serve the index.html file from the static folder
    return send_from_directory('static', 'index.html')

# Route to process image data
@app.route('/process_image', methods=['POST'])
def process_image():
    data = request.json
    image_data = data['image']
    
    # Decode the base64 image data
    image_data = re.sub('^data:image/.+;base64,', '', image_data)
    image = np.frombuffer(base64.b64decode(image_data), dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    
    # Detect shapes and colors
    shapes, colors = detect_shapes_and_colors(image)
    generated_code = convert_to_code(shapes, colors)

    return jsonify({'generated_code': generated_code})

# Function to detect shapes and colors
def detect_shapes_and_colors(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    shapes = []
    colors = []

    # Analyze each contour
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        x, y, w, h = cv2.boundingRect(approx)
        color = detect_color(image[y:y+h, x:x+w])

        # Determine the shape
        if len(approx) == 3:
            shapes.append("Triangle")
        elif len(approx) == 4:
            shapes.append("Square")
        elif len(approx) > 4:
            shapes.append("Circle")

        colors.append(color)

    return shapes, colors

# Function to detect the dominant color in a region
def detect_color(region):
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)

    # Define ranges for red, green, blue, and yellow colors
    lower_red = np.array([0, 50, 50])
    upper_red = np.array([10, 255, 255])
    lower_green = np.array([50, 50, 50])
    upper_green = np.array([70, 255, 255])
    lower_blue = np.array([110, 50, 50])
    upper_blue = np.array([130, 255, 255])
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])

    if cv2.inRange(hsv, lower_red, upper_red).any():
        return "Red"
    elif cv2.inRange(hsv, lower_green, upper_green).any():
        return "Green"
    elif cv2.inRange(hsv, lower_blue, upper_blue).any():
        return "Blue"
    elif cv2.inRange(hsv, lower_yellow, upper_yellow).any():
        return "Yellow"
    else:
        return "Unknown"

# Function to convert shapes and colors to code
def convert_to_code(shapes, colors):
    code = ""
    variables = {}
    current_operation = None  # Store current operation

    for i, (shape, color) in enumerate(zip(shapes, colors)):
        if shape == "Triangle":  # Variables
            if color == "Blue":
                variable_name = "x"
                code += f"{variable_name} = "
                variables[variable_name] = None  # Placeholder for value
            elif color == "Red":
                variable_name = "y"
                code += f"{variable_name} = "
                variables[variable_name] = None
            elif color == "Green":
                variable_name = "z"
                code += f"{variable_name} = "
                variables[variable_name] = None

        elif shape == "Square":  # Operations
            if color == "Red":
                current_operation = "="  # Assignment
                code += "="
            elif color == "Yellow":
                if current_operation is None:
                    current_operation = "+"  # Addition
                    code += " + "

        elif shape == "Circle":  # Numbers
            if color == "Green":
                value = "2"  # Assign value for number 2
                code += f"{value} "
                variables["x"] = 2  # Assign value to x
            elif color == "Blue":
                value = "3"  # Assign value for number 3
                code += f"{value} "
                variables["y"] = 3  # Assign value to y

    # Final result with assigned values
    if current_operation == "+":
        code += f"# Resulting in z = {variables.get('x', 0) + variables.get('y', 0)}"
    
    return code.strip()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
