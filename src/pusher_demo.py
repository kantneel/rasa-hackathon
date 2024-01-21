import pusher
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

pusher_client = pusher.Pusher(
    app_id='1744017',
    key='1e429e2648755b45004d',
    secret=os.environ.get('PUSHER_SECRET'),
    cluster='us3',
    ssl=True
)


def add_slide():
    """Add a new slide."""
    pusher_client.trigger('rasa', 'add_slide', {})


def choose_slide(index):
    """Choose the slide with the given index."""
    pusher_client.trigger('rasa', 'choose_slide', {'index': index})


def update_slide(markdown):
    """Update the slide with the given markdown."""
    pusher_client.trigger('rasa', 'update_slide', {'markdown': markdown})


def set_image(image_url):
    """Set the image on the slide."""
    pusher_client.trigger('rasa', 'set_image', {'image_url': image_url})


def main():
    add_slide()
    choose_slide(0)
    update_slide("Hello World")
    set_image("https://i.imgur.com/nGF1K8f.jpg")


main()
