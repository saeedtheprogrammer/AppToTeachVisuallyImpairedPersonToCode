from flask import Blueprint

# Create a blueprint for the home controller
home_controller = Blueprint('home_controller', __name__)

@home_controller.route('/')
def home():
    return "Welcome to the Image Processor Application!"
