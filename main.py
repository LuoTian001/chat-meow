from meow.web.app import create_app
from chat import create_chat
import logging

if __name__ == '__main__':
    chat_logger = logging.basicConfig(
        level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    create_chat()
    create_app()
