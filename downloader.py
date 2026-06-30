class Downloader:
    def __init__(self, path, max_concurrent=3):
        self.path = path

    async def start(self):
        print("Downloader started")
