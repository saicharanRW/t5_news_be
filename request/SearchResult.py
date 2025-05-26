class SearchResult:
    def __init__(self):
        self.url = ''
        self.title = ''
        self.content = ''

    def printIt(self):
        print('url\t->', self.url)
        print('title\t->', self.title)
        print('content\t->', self.content)
        print()
        
    def getUrl(self):
        return self.url
    
    def getTitle(self):
        return self.title
    
    def getContent(self):
        return self.content

    def writeFile(self, filename):
        try:
            with open(filename, 'a', encoding='utf-8') as file:
                file.write(f"url: {self.url}\n")
                file.write(f"title: {self.title}\n")
                file.write(f"content: {self.content}\n\n")
        except IOError as e:
            print('File error:', e)