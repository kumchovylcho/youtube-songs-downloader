from pytube import YouTube
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

SERVICE_ACCOUNT_FILE = "search.json"

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
youtube = build(API_SERVICE_NAME,
                API_VERSION,
                credentials=credentials)


class SongSearch:
    HTTP_ERROR_MSG = "An HTTP error occurred:"

    def __init__(self,
                 part: str,
                 type: str,
                 order: str
                 ):
        self.part = part
        self.type = type
        self.order = order

    @staticmethod
    def check_song_existence(song_name):
        song_name = song_name.lower()
        for root, dirs, files in os.walk("."):
            if 'venv' in dirs:
                dirs.remove('venv')
            if '.idea' in dirs:
                dirs.remove('.idea')

            for file in files:
                if file in ['.env', '.gitignore']:
                    continue

                saved_song = file.split(".")[0].lower()

                if saved_song == song_name or saved_song in song_name or song_name in saved_song:
                    return os.path.join(root, file)

    def search_videos(self,
                      query,
                      video_searches: int,
                      ):
        try:
            search_response = youtube.search().list(
                q=query,
                part=self.part,
                type=self.type,
                maxResults=video_searches,
                order=self.order
            ).execute()

            return [x["id"]["videoId"] for x in search_response["items"]]

        except HttpError as e:
            print(self.HTTP_ERROR_MSG)
            print(e)
            return []


class DownloadSong:
    SUCCESSFUL_DOWNLOAD_MSG = "has been successfully downloaded."
    EXCEPTION_MSG = "An error occurred:"

    def __init__(self, song_searcher: SongSearch,
                 file_format: str):
        self.song_searcher = song_searcher
        self.file_format = file_format

    def download_audio(self,
                       song_url,
                       folder_destination,
                       song_name: str
                       ):
        try:
            yt = YouTube(song_url)

            video = yt.streams. \
                filter(only_audio=True). \
                order_by('abr'). \
                desc(). \
                first()

            video.download(output_path=folder_destination,
                           filename=song_name + self.file_format,
                          )

            print(f"{yt.title} {self.SUCCESSFUL_DOWNLOAD_MSG}")

        except Exception as e:
            print(self.EXCEPTION_MSG)
            print(str(e))


class ManageApp:
    HOW_MANY_SONGS_QUESTION_MSG = "How many songs do you want? "
    SEARCH_KEYWORD_MSG = "Enter keywords to search for a YouTube video or `stop` to stop the program: "
    DESTINATION_OF_SONGS_MSG = "Enter the folder name (leave blank to save without folder) song/s is saved inside project folder: "
    VIDEOS_NOT_FOUND_MSG = "No videos found based on the provided keywords."
    STOP_PROGRAM_COMMAND_MSG = "stop"

    DEFAULT_VIDEO_URL = "https://www.youtube.com/watch?v="

    REDUNDANT_SYMBOLS = (("/", ""),
                         ("\\", ""),
                         ("<", ""),
                         (">", ""),
                         (":", ""),
                         ('"', ""),
                         ("|", ""),
                         ("?", ""),
                         ("*", ""),
                         ("&amp", "n")
                         )

    def __init__(self):
        self.audio_searcher = SongSearch("snippet",
                                         "video",
                                         "viewCount"
                                        )
        self.audio_downloader = DownloadSong(self.audio_searcher,
                                            ".mp3"
                                            )

        self.creating_songs = True


    def get_user_wanted_songs(self, msg: str):
        user_choice = input(msg)

        if user_choice.isdigit():
            return int(user_choice)

        self.get_user_wanted_songs(msg)

    def get_keywords(self):
        return input(self.SEARCH_KEYWORD_MSG)

    def get_destination(self):
        return input(self.DESTINATION_OF_SONGS_MSG) or '.'

    @staticmethod
    def get_song_title(song_url: str):
        r = requests.get(song_url)

        soup = BeautifulSoup(r.text,
                             features="html.parser"
                             )

        title = str(soup.find_all(name="title")[0])

        for delete_val, replace_val in ((" - YouTube", ""),
                                        ("<title>", ""),
                                        ("</title>", "")
                                        ):
            title = title.replace(delete_val, replace_val)

        return title

    def remove_redundant_symbols_from_song_title(self, song_name: str):
        for del_symbol, replace_value in self.REDUNDANT_SYMBOLS:
            song_name = song_name.replace(del_symbol, replace_value)

        return song_name

    def download_songs(self, video_ids, destination):
        for song_id in video_ids:
            song_title = self.remove_redundant_symbols_from_song_title(
                self.get_song_title(f"{self.DEFAULT_VIDEO_URL}{song_id}")
                )

            exist_path = self.audio_searcher.check_song_existence(song_title)
            if exist_path:
                print(f"{song_title} --------- already exists inside {exist_path}")
                continue

            self.audio_downloader.download_audio(f"{self.DEFAULT_VIDEO_URL}{song_id}",
                                                 destination,
                                                 song_title,
                                                 )

    def run_app(self):
        while self.creating_songs:
            keyword = self.get_keywords()

            if keyword.lower() == self.STOP_PROGRAM_COMMAND_MSG:
                self.creating_songs = False
                continue

            how_many_songs = self.get_user_wanted_songs(self.HOW_MANY_SONGS_QUESTION_MSG)
            destination = self.get_destination()

            video_ids = self.audio_searcher.search_videos(keyword,
                                                          how_many_songs
                                                          )

            if not video_ids:
                print(self.VIDEOS_NOT_FOUND_MSG)
                continue


            self.download_songs(video_ids,
                                destination
                                )


app = ManageApp()
app.run_app()