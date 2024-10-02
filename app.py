import os
import base64
from flask import Flask, request, jsonify
from io import BytesIO
from PIL import Image
from rembg import remove
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BACKDROP_IMAGE_PATH = os.path.join('assets', 'backdrop.jpg')
FRAME_IMAGE_PATH = os.path.join('assets', 'frame.png')

def remove_background(input_image):
    img_data = input_image.read()
    output = remove(img_data)
    result_img = Image.open(BytesIO(output)).convert("RGBA")
    return result_img

def resize_backdrop(backdrop_path, target_size):
    backdrop = Image.open(backdrop_path).convert("RGBA")
    backdrop_resized = backdrop.resize(target_size)
    return backdrop_resized

def composite_person_on_backdrop(person_image, backdrop):
    person_width, person_height = person_image.size
    backdrop_width, backdrop_height = backdrop.size
    final_image = backdrop.copy()
    y_offset = backdrop_height - person_height  # Align at bottom
    x_offset = (backdrop_width - person_width) // 2  # Center horizontally
    final_image.paste(person_image, (x_offset, y_offset), person_image)
    return final_image

def overlay_frame(frame_path, composited_image, output_size):
    frame_image = Image.open(frame_path).convert("RGBA")
    frame_resized = frame_image.resize(output_size)
    final_image_with_frame = composited_image.copy()
    final_image_with_frame.paste(frame_resized, (0, 0), frame_resized)
    return final_image_with_frame

@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        person_image_file = request.files['person_image']
        person_image = remove_background(person_image_file)
        target_size = person_image.size
        backdrop_image = resize_backdrop(BACKDROP_IMAGE_PATH, target_size)
        composited_image = composite_person_on_backdrop(person_image, backdrop_image)
        final_image = overlay_frame(FRAME_IMAGE_PATH, composited_image, target_size)

        # Save the final image to a BytesIO object
        img_byte_arr = BytesIO()
        final_image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)  # Reset pointer to the start

        # Convert the image to a base64 string
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

        # Respond with the base64 image
        return jsonify({
            "message": "Image processed successfully",
            "output_image": f"data:image/png;base64,{img_base64}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Main entry point
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8800)
