from googleapiclient.discovery import build
from Functions.Auth.auth import Authenticate
from Functions.Search.search import Search

# Define rule-based operations function


def process_emails(service):
    # Define the search query for the emails you want to process
    query = 'is:unread '

    # Search for emails matching the query
    response = service.users().messages().list(userId='me', q=query).execute()

    # Process each email
    if 'messages' in response:
        for message in response['messages']:
            msg = service.users().messages().get(
                userId='me', id=message['id']).execute()
            print(msg)


if __name__ == '__main__':
    # get the Gmail API service
    try:
        service = Authenticate.gmail_authenticate()
    except Exception:
        print(f'An error occurred: {Exception}')
    print(Search.search_messages(service=service, query="is:unread"))
    # process_emails(service)
