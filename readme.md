## Easy Gmail Follow-Up

This is a little project of mine that creates a simple way to follow up on emails. It uses the Gmail API to search for all conversations you had with a mail and then creates a proper follow-up email and puts it into the auto-followup folder that will be created in your Gmail.


## Enable Gmail API

Go to the Google Cloud Console.

Create a new project by clicking on the project drop-down and selecting New Project.

In the new project dialog, enter a project name and select a billing account as applicable. Then click Create.

Once the project is created, select it from the projects list.

Click on Library in the left-hand menu.

In the Library page, search for Gmail and select Gmail API from the results list.

On the Gmail API page, click Enable.

## Create OAuth credentials.json file

Once the Gmail API is enabled, click on Create Credentials.

In the Create credentials step, select OAuth client ID.

If you haven't configured the OAuth consent screen yet, you'll be asked to do so. Fill in the required fields. For the User Type, you can select External if the app is used by people outside of your organization.

Once the OAuth consent screen is configured, you'll be back at the Create OAuth client ID step. For the Application type, select Desktop app and give it a name.

Click Create. Your client ID and client secret will be shown. Click OK.

Back in the Credentials page, you'll see the client ID you just created. Click on the download icon on the right to download the credentials.json file.

Move the downloaded credentials.json file to your project directory.




