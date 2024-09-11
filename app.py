from flask import Flask
from flask import Flask, request, render_template_string, jsonify,render_template,send_from_directory
from  text_to_speech import TextToSpeech
import os
app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/text-to-speech",methods=['POST'])
def text_to_speech():
    try:
        data = request.get_json()
        text = str(data['text'])
        text_to_speech = TextToSpeech()
        audio_file = text_to_speech.generate_speech(text)
        if os.path.exists(audio_file):
            return send_from_directory(os.getcwd(), audio_file, as_attachment=True)
    except Exception as e:
        error_response = {
            'status': 'failure',
            'message': 'An error occurred while querying service',
            'error_details': str(e)
        }
        return jsonify(error_response), 400



