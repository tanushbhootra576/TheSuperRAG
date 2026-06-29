import traceback
from langchain_community.document_loaders import YoutubeLoader
try:
    loader = YoutubeLoader.from_youtube_url('https://www.youtube.com/watch?v=0sZ3iTjB1f0', add_video_info=False, language=['en', 'hi', 'en-IN', 'hi-IN'], translation='en')
    print(loader.load())
except Exception as e:
    traceback.print_exc()
