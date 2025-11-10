from google_auth import get_youtube_service

def search_youtube(keyword):
    service = get_youtube_service()

    request = service.search().list(
        q=keyword,
        part="snippet",
        type="video",
        maxResults=10
    )
    response = request.execute()

    results = []
    for item in response["items"]:
        results.append({
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "published": item["snippet"]["publishedAt"]
        })
    
    return results

if __name__ == "__main__":
    keyword = input("Keyword ricerca YouTube: ")
    data = search_youtube(keyword)
    for x in data:
        print(x)