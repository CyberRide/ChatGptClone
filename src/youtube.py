from pytube import YouTube

def download_video(video_url):
    yt = YouTube(video_url)
    video = yt.streams.first()
    
    return video.download()
