import os
import re
from datetime import timedelta
from googleapiclient.discovery import build


api_key = os.environ.get('YT_API_KEY')
youtube = build("youtube", "v3", developerKey=api_key)



def get_video_seconds(duration):
    hours_pattern = re.compile(r'(\d+)H')
    minutes_pattern = re.compile(r'(\d+)M')
    seconds_pattern = re.compile(r'(\d+)S')

    hours = hours_pattern.search(duration)
    minutes = minutes_pattern.search(duration)
    seconds = seconds_pattern.search(duration)

    hours = int(hours.group(1)) if hours else 0
    minutes = int(minutes.group(1)) if minutes else 0
    seconds = int(seconds.group(1)) if seconds else 0

    video_seconds = timedelta(
        hours=hours,
        minutes=minutes,
        seconds=seconds
    ).total_seconds()

    return video_seconds


def duration_calculator(total_seconds, granularity=4):
    intervals = (
        ('weeks', 604800),  # 60 * 60 * 24 * 7
        ('days', 86400),    # 60 * 60 * 24
        ('hours', 3600),    # 60 * 60
        ('minutes', 60),
        ('seconds', 1),
    )
    result = []

    for name, count in intervals:
        value = int(total_seconds // count)
        if value:
            total_seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append(f"{value} {name}")
    return ', '.join(result[:granularity])


def get_playlist_id(youtube_link):
    # TODO: Fix this => It shouldn't work for links like https://www.youtube.com/watch?v=acOktTcTVEQ
    p = re.compile('^([\S]+list=)?([\w_-]+)[\S]*$')
    m = p.match(youtube_link)
    if m:
        return m.group(2)
    else:
        return 'Invalid Playlist Link'


def analyze(playlist_id):
    nextPageToken = None
    total_seconds = 0
    no_of_videos = 0
    videos = []
    
    while True:
        pl_request = youtube.playlistItems().list(
            part="contentDetails, snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=nextPageToken
        )

        pl_response = pl_request.execute()

        vid_ids = []

        for vid in pl_response['items']:
            contentDetails = vid["contentDetails"]
            snippet = vid["snippet"]

            playlist_title = snippet["title"]
            added_to_playlist = snippet["publishedAt"]
            channel_title = snippet["channelTitle"]
            position = snippet["position"]
            video_id = contentDetails["videoId"]
            # published_at = contentDetails["videoPublishedAt"]
    
            vid_ids.append(video_id)

        vid_request = youtube.videos().list(
            part="contentDetails, statistics, snippet",
            id=",".join(vid_ids)
        )

        vid_response = vid_request.execute()
        for vid in vid_response['items']:
            contentDetails = vid["contentDetails"]
            statistics = vid["statistics"]

            title = vid["snippet"]["title"]
            published_at = vid["snippet"]["publishedAt"]
            video_id = vid['id']
            duration = contentDetails["duration"]
            # TODO: Make a try except for all
            try:
                view_count = statistics["viewCount"]
                like_count = statistics["likeCount"]
                dislike_count = statistics["dislikeCount"]
                comment_count = statistics["commentCount"]
                
            except:
                view_count = 0
                like_count = 0
                dislike_count = 0
                comment_count = 0

            video_link = f'https://youtu.be/{video_id}'

            videos.append(
                {
                    'title': title,
                    'published_at': published_at,
                    'views': int(view_count),
                    'likes': int(like_count),
                    'dislikes': int(dislike_count),
                    'comments': int(comment_count),
                    'url': video_link
                }
            )
            video_seconds = get_video_seconds(duration)

            total_seconds += video_seconds
        
        nextPageToken = pl_response.get('nextPageToken')

        no_of_videos += len(vid_ids)

        if not nextPageToken:
            break
    
    # Duration at different Speeds
    time = {}
    time["total_duration"] = duration_calculator(total_seconds)
    time["average_length"] = duration_calculator(total_seconds/no_of_videos)
    time["at_1_25"] = duration_calculator(total_seconds/1.25)
    time["at_1_5"] = duration_calculator(total_seconds/1.5)
    time["at_1_75"] = duration_calculator(total_seconds/1.75)
    time["at_2"] = duration_calculator(total_seconds/2)
    time["at_2_25"] = duration_calculator(total_seconds/2.25)
    time["at_2_5"] = duration_calculator(total_seconds/2.5)
    time["at_3"] = duration_calculator(total_seconds/3)

    # Popularity
    popular_videos = {}
    popular_videos["most_viewed"] = sorted(videos, key=lambda vid: vid['views'], reverse=True)
    popular_videos["most_liked"] =  sorted(videos, key=lambda vid: vid['likes'], reverse=True)
    popular_videos["most_disliked"] = sorted(videos, key=lambda vid: vid['dislikes'], reverse=True)
    popular_videos["most_commented"] = sorted(videos, key=lambda vid: vid['comments'], reverse=True)
    popular_videos["recently_uploaded"] = sorted(videos, key=lambda vid: vid['published_at'], reverse=True)
    popular_videos["oldest"] = sorted(videos, key=lambda vid: vid['published_at'])
    

    return [time, no_of_videos, popular_videos]

    

