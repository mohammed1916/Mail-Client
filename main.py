from Functions.Auth.auth import Authenticate
from Functions.Search.search import Search
if __name__ == '__main__':
    # get the Gmail API service
    service = Authenticate.gmail_authenticate()
    print(Search.search_messages(service=service, query="GUVI"))
