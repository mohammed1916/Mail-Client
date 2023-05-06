from googleapiclient.discovery import build
from Functions.Auth.auth import Authenticate
from Functions.Parse.Parser import EmailParser

if __name__ == '__main__':
    # get the Gmail API service
    service = Authenticate.gmailAuthenticate()
    EmailParser(service).fetchStoreMessages(query="is:unread")
