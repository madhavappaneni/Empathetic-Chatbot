from flask import Flask, request
from flask_cors import CORS
from services.dialog_manager import DialogManager
from services.empathetic_dialog_generator import EmpatheticDialogGenerator
from services.chitchat_generator import ChitChatGenerator
from services.reddit_generator import RedditGenerator
# from services.bert_reranker import rerank
from services.neural_reranker import rerank

app = Flask(__name__)
CORS(app)
dialog_manager = DialogManager()
empathetic_dialog_generator = EmpatheticDialogGenerator()
chitchat_generator = ChitChatGenerator()
reddit_generator = RedditGenerator()


app.debug = True  # Turn on debug mode


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('user_message')

    dialog_manager_response = dialog_manager.process_user_message(user_message)
    print(dialog_manager_response, 'dialog_manager_response')
    empathetic_dialog_response = empathetic_dialog_generator.generate_response(
        user_message, dialog_manager_response['context'])
    print(dialog_manager_response['context'], 'context')
    print(dialog_manager_response['context'], 'cache')

    chitchat_response = chitchat_generator.generate_response(
        user_message, dialog_manager_response['context'])
    reddit_response = reddit_generator.generate_response(
        user_message, '')
    reranked_responses = rerank([empathetic_dialog_response, chitchat_response, reddit_response], user_message)

    return {'dialog_manager_response': dialog_manager_response,
            'reranked_response': reranked_responses[0],
            'empathetic_dialog_response': empathetic_dialog_response,
            'chitchat_response': chitchat_response,
            'reddit_response': reddit_response}


if __name__ == '__main__':
    app.run(port=8080)
    
    
    
# curl -X POST -H "Content-Type: application/json" -d '{"user_message": "How to use Reddit?"}' http://127.0.0.1:8080/chat

