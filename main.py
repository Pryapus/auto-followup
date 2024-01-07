import base64
import email
import os
from auth import main as get_gmail_service
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.utils import parseaddr
from googleapiclient.errors import HttpError
from openai import OpenAI
from datetime import datetime
import re

# Get the current date and time
current_datetime = datetime.now()
service = get_gmail_service()

load_dotenv()
client = OpenAI()

def list_labels():
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        return labels
    except Exception as e:
        print(f'An error occurred: {e}')
        return None

def search_emails(email_list):
    try:
        query = ' OR '.join([f'({email})' for email in email_list]) + ' newer_than:1y'
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])

        emails_data = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='raw').execute()
            msg_str = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
            mime_msg = email.message_from_bytes(msg_str)


            email_data = {
                'SUBJECT': mime_msg.get('subject'),
                'Raw Snippet': msg.get('snippet'),
                'Date': mime_msg.get('date'),
                'From': mime_msg.get('from'),
                'thread_id': message.get('threadId'),
                'from_mail': parseaddr(mime_msg.get('from'))[1]
            }
            emails_data.append(email_data)
        return emails_data
    except HttpError as error:
        print(f'An error occurred: {error}')
        print(error.content)
        return None

def get_or_create_label(service, label_name):
    # List all labels
    labels = service.users().labels().list(userId='me').execute().get('labels', [])

    # Check if our label exists
    for label in labels:
        if label['name'].lower() == label_name.lower():
            return label['id']

    # If not, create it
    new_label = {'name': label_name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
    created_label = service.users().labels().create(userId='me', body=new_label).execute()
    return created_label['id']

def modify_thread(service, thread_id, label_id):
    # Apply the label to the thread
    add_labels = {'addLabelIds': [label_id], 'removeLabelIds': []}
    service.users().threads().modify(userId='me', id=thread_id, body=add_labels).execute()

def create_draft_reply(service, thread_id, recipient_emails, reply_text, label_name='auto-followup'):
    try:
        # Create a MIMEText object for the reply
        message = MIMEText(reply_text)
        message['to'] = ', '.join(recipient_emails)  # Set multiple recipients
        message['subject'] = 'Re: '

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create the draft
        draft = {'message': {'raw': raw_message, 'threadId': thread_id}}
        created_draft = service.users().drafts().create(userId='me', body=draft).execute()

        # Apply label to the thread
        label_id = get_or_create_label(service, label_name)
        modify_thread(service, thread_id, label_id)

        print(f"Draft created and thread labeled: {created_draft['id']}")
        return created_draft
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None
   
def generate_reply(email_data, yourmail):
    system = f"""Please generate a follow-up email body keeping the style, language, and tone of the original conversation. Don't add new ideas; just continue from where the last email left off. The goal is to remind the recipient(s) in a friendly manner.

    Use the same language as the previous emails.

    Additionally, list the email addresses that should receive this reply, considering the entire conversation. Do not include any {yourmail} email addresses, as they are internal.

    Do not write a subject line or add more to the signature than the first name.

    Assume no follow-up call is scheduled.

    Specify which thread_id to reply to. Choose the most relevant thread_id and mention it at the end by writing 'thread_id=examplethreadid'.

    Today is {current_datetime}

    e.g.,
    This is a sample reply...

    recipients: example@example.com, another@example.com

    thread_id=292309109
    """
    user = f"Here is email data: {email_data}"

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    )
    draft_reply = response.choices[0].message.content

    # Extract thread_id and recipients
    thread_id_match = re.search(r'thread_id=(.*?)$', str(draft_reply))
    recipients_match = re.search(r'recipients: (.*?)\n', str(draft_reply), re.IGNORECASE)

    if thread_id_match:
        thread_id = thread_id_match.group(1).strip()
        draft_reply = re.sub(r'thread_id=(.*?)$', '', str(draft_reply))
    else:
        raise Exception("OpenAI response didn't have the proper thread_id formatting. Change the prompt")
    
    if recipients_match:
        recipients = recipients_match.group(1).strip().split(', ')
        draft_reply = re.sub(r'recipients: (.*?)\n', '', str(draft_reply))

    recipients = []
    if recipients_match:
        recipients = recipients_match.group(1).strip().split(', ')
    else:
        raise Exception("OpenAI response didn't list recipients. Adjust the prompt")

    return draft_reply, thread_id, recipients

def main(email_input, yourmail):
    emails_data = search_emails(email_input)
    draft_reply, thread_id, emails = generate_reply(emails_data, yourmail)

    # Pass the list of emails directly to create_draft_reply
    create_draft_reply(service, thread_id, emails, draft_reply)



if __name__ == '__main__':
    input_string = input("Enter a list of emails separated by commas: ")
    email_list = input_string.split(',')
    email_list = [email.strip() for email in email_list]
    yourmail = "@yourcompmail.com"
    main(email_list, yourmail)
