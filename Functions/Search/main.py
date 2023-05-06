from datetime import datetime, timedelta
import json
import os
import re
import sqlite3
import sys


class Search:
    # Iterate over messages and apply rules
    def __init__(self, service):
        self.service = service
        self.messages = []
        dbPath = os.path.dirname(os.path.abspath(sys.argv[0])) + '/Data/DB/'
        print(dbPath)
        self.conn = sqlite3.connect(dbPath + 'emails.db')
        self.cursor = self.conn.cursor()
        # load rules from JSON file
        with open(os.path.dirname(os.path.abspath(__file__))+'/rules.json', 'r') as rules_file:
            self.rules = json.load(rules_file)

    # function to convert time frame to number of days
    def convert_timeframe(self, time_frame):
        time_frame = time_frame.lower()
        days = 0
        if 'day' in time_frame:
            days = int(re.findall(r'\d+', time_frame)[0])
        elif 'week' in time_frame:
            days = int(re.findall(r'\d+', time_frame)[0]) * 7
        elif 'month' in time_frame:
            days = int(re.findall(r'\d+', time_frame)[0]) * 30
        elif 'year' in time_frame:
            days = int(re.findall(r'\d+', time_frame)[0]) * 365
        return days

    def processMails(self):
        self.messages = self.cursor.execute("SELECT * FROM emails;").fetchall()
        # Build the SQL query based on the search rules
        query = 'SELECT * FROM emails WHERE '
        predicates = []
        for rule in self.rules['rules']:
            predicates = []
            rulePredicate = rule['predicate']
            ruleConditions = rule['conditions']
            ruleActions = rule['actions']
            # print('rule: ', rule)
            # print('\nrulePredicate:', rulePredicate)
            # print('\nruleConditions:', ruleConditions)
            # print('\nruleActions:', ruleActions)

            for ruleCondition in ruleConditions:
                condition = ''

                field = ruleCondition['field']
                predicate = ruleCondition['predicate']
                value = ruleCondition['value']

                if field == 'Received Date/Time':
                    num_days = self.convert_timeframe(value)
                    # filter emails based on received date
                    today = datetime.now()
                    time_threshold = today - timedelta(days=num_days)
                    if predicate == 'greater than':
                        condition = f"internal_date > '{time_threshold.strftime('%a, %d %b %Y %H:%M:%S %z')}'"
                    elif predicate == 'less than':
                        condition = f"internal_date < '{time_threshold.strftime('%a, %d %b %Y %H:%M:%S %z')}'"
                    else:
                        raise ValueError(
                            f"Invalid predicate for field '{field}': {predicate}")
                else:
                    col = ''
                    if field == 'From':
                        col = 'sender'
                    elif field == 'Subject':
                        col = 'subject'
                    elif field == 'Message':
                        col = 'body'

                    if predicate == 'equals':
                        condition = f"{col} = '{value}'"
                    elif predicate == 'does not equal':
                        condition = f"{col} != '{value}'"
                    elif predicate == 'contains':
                        condition = f"{col} LIKE '%{value}%'"
                    elif predicate == 'does not contain':
                        condition = f"{col} NOT LIKE '%{value}%'"
                    else:
                        raise ValueError(
                            f"Invalid predicate for field '{field}': {predicate}")
                print('condition:💎', condition)
                predicates.append(condition)
            print('predicates:🔥', predicates)

            if rulePredicate == "all":
                query = f"SELECT * FROM emails WHERE {' AND '.join(predicates)}"
            elif rulePredicate == "any":
                query = f"SELECT * FROM emails WHERE {' OR '.join(predicates)}"

            # Execute the SQL query
            print('query:🚀', query)
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            print('results:✅', results)

            # Perform Action
            for action in ruleActions:
                if action['type'] == 'mark_as_read':
                    for result in results:
                        # print(result)
                        result_id = result[0]
                        self.service.users().messages().modify(userId='me', id=result_id,
                                                               body={'removeLabelIds': ['UNREAD']}).execute()
                        # self.cursor.execute('UPDATE emails SET is_read = ? WHERE id = ?', (1, result_id))
                elif action['type'] == 'mark_unread':
                    for result in results:
                        result_id = result[0]
                        self.service.users().messages().modify(userId='me', id=result_id,
                                                               body={'addLabelIds': ['UNREAD']}).execute()
                        # self.cursor.execute('UPDATE emails SET is_read = ? WHERE id = ?', (0, result_id))
                elif action['type'].startswith('move'):
                    """
                    CHAT
                    SENT
                    INBOX
                    IMPORTANT
                    TRASH
                    DRAFT
                    SPAM
                    CATEGORY_FORUMS
                    CATEGORY_UPDATES
                    CATEGORY_PERSONAL
                    CATEGORY_PROMOTIONS
                    CATEGORY_SOCIAL
                    STARRED
                    UNREAD
                    """
                    for result in results:
                        result_id = result[0]
                        labels = self.service.users().labels().list(
                            userId='me').execute().get('labels', [])
                        label_id = None
                        label_name = action['value']
                        for label in labels:
                            # print(label['id'])
                            if label['name'] == label_name:
                                label_id = label['id']
                                break
                        if label_id:
                            self.service.users().messages().modify(userId='me', id=result_id,
                                                                   body={'addLabelIds': [label_id]}).execute()
                            # self.cursor.execute('UPDATE emails SET is_deleted = ? WHERE id = ?', (1, result_id))
                        else:
                            print(f'Error: Label "{label_name}" not found')
        self.conn.close()


# if __name__ == '__main__':
#     Search().processMails()
