## Instruction on how to configure the facebook page scrapping bot

### Facebook App Setup

1. Create a facebook developer account
2. Create a new app [type:None] from https://developers.facebook.com/apps/create/
3. Open the app, go to setting/basic and copy app_id and app_secret
4. Open graph api explorer from https://developers.facebook.com/tools/explorer/
5. Select Facebook App that you just created
6. Click 'Generate Access Token' and allow everything [the account you are using right now its pages will be
   scraped [if you are admin]]
7. When 6th step is done and a token is generated, mark all of the permission you see in permissions
8. Then again click 'generate access token' and follow the procedure
9. When 8th step is done, you will see a new Access Token is generated.
   ``Copy the access token``

### Python Bot setup

1. Install python 3.9
2. on terminal 'pip install -r requirements.txt'
3. when all of the requirements are installed, run ``facebook_scrape.py``
4. You are good to go. The scraper bot is self-explanatory
