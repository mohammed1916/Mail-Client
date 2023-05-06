import base64
import os
import quopri
import re
import sqlite3
import sys


class EmailParser:
    def __init__(self, service):
        self.service = service
        self.messages = []

    def fetchStoreMessages(self, query):
        # Fetch messages matching the query
        self.messages = self.service.users().messages().list(
            userId='me', q=query).execute()
        self.store()

    def store(self):
        # Create a SQLite database and table to store email data
        dbPath = os.path.dirname(os.path.abspath(sys.argv[0])) + '/Data/DB/'
        conn = sqlite3.connect(dbPath + 'emails.db')
        c = conn.cursor()
        c.execute(
            'CREATE TABLE IF NOT EXISTS emails (id TEXT PRIMARY KEY, subject TEXT, sender TEXT, receiver TEXT, internal_date TEXT, body TEXT)')

        # Insert email data into the table
        for message in self.messages['messages']:
            message_id, subject, sender, receiver, internal_date, body = self.parseData(
                message)
            # print(type(internal_date), internal_date)

            # Insert the email data into the database
            c.execute('INSERT OR REPLACE INTO emails (id, subject, sender, receiver, internal_date, body) VALUES (?, ?, ?, ?, ?, ?)',
                      (message_id, subject, sender, receiver, internal_date, body))

        # Commit changes and close the database connection
        conn.commit()
        conn.close()

    def parseData(self, message):
        message_id = message['id']
        message_data = self.service.users().messages().get(
            userId='me', id=message_id).execute()
        payload = message_data['payload']
        headers = payload['headers']

        # Extract the subject and sender email address from the message data
        subject = ''
        sender = ''
        receiver = ''
        internal_date = ''
        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
            elif header['name'] == 'From':
                sender = header['value']
            elif header['name'] == 'Delivered-To':
                receiver = header['value']
            elif header['name'] == 'Date':
                internal_date = header['value']

        # Look for text/plain and text/html body parts in the message payload
        body = ''
        for part in payload.get('parts', [payload]):
            if part.get('mimeType') == 'text/plain':
                body = part.get('body', {}).get('data', '')
                break
            elif part.get('mimeType') == 'text/html':
                body = part.get('body', {}).get('data', '')
                # Convert HTML entities to Unicode
                body = quopri.decodestring(
                    body.encode('utf-8')).decode('utf-8')
                # Remove HTML tags
                body = re.sub('<[^<]+?>', '', body)
                break

        # Decode the body content from base64
        if body:
            body = base64.urlsafe_b64decode(body).decode('utf-8')

        return message_id, subject, sender, receiver, internal_date, body
