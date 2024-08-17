import exceptions
import requests
import yt_dlp as youtube_dl

class AudioDownloader:
    download_count = 0

    def __init__(self, url, account):
        self.filename = ''
        self.account = account

        self._url_validation(url)
        self._account_validation(account)
        self._download(url)

    @staticmethod
    def _url_validation(url):
        try:
            request = requests.get(url)
        except:
            raise exceptions.InputError

    @staticmethod
    def _account_validation(account):
        if '@gmail.com' in account['username']:
            return
        
        raise exceptions.LoginError

    def _download_audio(self, video_url):
        video_info = youtube_dl.YoutubeDL().extract_info(url = video_url,download=False)
        self.filename = f"tmp/{video_info['title']}.mp3"
        self.title = video_info['title']
        options={
            'format':'bestaudio/best',
            'keepvideo':False,
            'outtmpl':self.filename,
            'username':self.account['username'],
            'password':self.account['password'],
        }
        with youtube_dl.YoutubeDL(options) as ydl:
            ydl.download([video_info['webpage_url']])

    def _download(self, url):
        try:    
            self._download_audio(url)
            AudioDownloader.download_count += 1
        except:
            raise exceptions.DownloadError

