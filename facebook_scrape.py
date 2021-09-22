import sys
from typing import Callable
from pyfacebook import GraphAPI
import json
from datetime import datetime


class Credentials:
    def __init__(self, json_file_path: str):
        self.file_path = json_file_path
        self.creds = {}

    def get_app_id(self):
        return self.creds['app_id']

    def get_app_secret(self):
        return self.creds['app_secret']

    def get_long_lived_token(self):
        return self.creds['long_lived_access_token']

    def get_long_lived_api(self):
        return self.api

    def process_creds(self):
        try:
            with open(self.file_path, 'r') as file:
                self.creds = json.load(file)

        except:
            print(f"{self.file_path} file not found")
            resp = input("Create credentials? y/n : ")
            if resp.lower() == 'y':
                self.create_creds()
                self.create_long_lived_token()
            else:
                sys.exit(0)

    def validate_creds(self):
        required_keys = ['app_id', 'app_secret', 'long_lived_access_token']
        available_keys = list(self.creds.keys())
        altered = False
        for key in available_keys:
            if key in required_keys:
                if len(self.creds[key]) == 0:
                    if key in ['app_id', 'app_secret']:
                        altered = True
                        self.instruction_app_id_app_secret()
                        value = input(f"{key} : ")
                        self.creds[key] = value
                    elif key in ['long_lived_access_token']:
                        self.create_long_lived_token()
            else:
                altered = False
                if key in ['app_id', 'app_secret']:
                    self.instruction_app_id_app_secret()
                    value = input(f"{key} : ")
                    self.creds[key] = value
                elif key in ['long_lived_access_token']:
                    self.create_long_lived_token()
        if altered:
            with open(self.file_path, 'w') as file:
                json.dump(self.creds, file)
            print("Credentials are set")
        else:
            try:
                self.api = GraphAPI(app_id=self.get_app_id(), app_secret=self.get_app_secret(),
                                    access_token=self.get_long_lived_token())

                print(self.api.get_object("/me"))
            except Exception as e:
                print(e)
                print(
                    "Long lived token is not valid (may be expired). It is always considered that app_id,app_secret are valid")
                resp = input("Reset authentication? y/n : ")
                if resp.lower() == 'y':
                    with open(self.file_path, 'w') as file:
                        self.creds['long_lived_access_token'] = ""
                        json.dump(self.creds, file)
                    cred.process_creds()
                    cred.validate_creds()
                else:
                    sys.exit(0)

    def create_short_lived_token(self) -> str:
        """
        This token expires in one hr
        Prints a link in the console, user will copy and open the link in a browser where facebook is logged in
        Then user will get a new link in the address bar.
        Copy the link and paste it in the console.
        App will handle the rest
        """
        resp = input("Do you have a short_lived_user_access_token? y/n : ")
        if resp.lower() == 'y':
            token = input("token : ")
            try:
                self.api = GraphAPI(app_id=self.creds['app_id'], app_secret=self.creds['app_secret'],
                                    access_token=token)
                return str(self.api.access_token)
            except:
                return None

        else:
            self.api = GraphAPI(app_id=self.creds['app_id'], app_secret=self.creds['app_secret'], oauth_flow=True)
            open_url = self.api.get_authorization_url()
            print(open_url)
            print("1. Open above link in a browser where facebook is already logged in.\n"
                  "2. Copy the new link from address bar generated by that link\n"
                  "3. Paste the link below and press enter\n")
            resp_url = input("Token URL : ")
            try:
                self.api.exchange_user_access_token(response=resp_url)
                return str(self.api.access_token)
            except:
                return None

    def create_long_lived_token(self):
        """
        Expires in 60 days
        Creates a long lived token using app_id and app_secret
        To create a long lived token we will need to create a short lived token then
        use that to create long lived token
        """
        short_lived_token = self.create_short_lived_token()
        if short_lived_token is None:
            print("Authentication Error. Try again")
            self.create_long_lived_token()
        else:
            try:
                long_lived = self.api.exchange_long_lived_user_access_token()
                self.api = GraphAPI(app_id=self.get_app_id(), app_secret=self.get_app_secret(),
                                    access_token=long_lived['access_token'])
                self.creds['long_lived_access_token'] = long_lived['access_token']
                with open(self.file_path, 'w') as file:
                    json.dump(self.creds, file)
                    print("Long lived Token created and saved")
            except:
                print("Authentication Error. Try again")
                self.create_long_lived_token()

    def instruction_app_id_app_secret(self):
        print(
            "You must provide valid app_id and app_secret of one of the apps from https://developers.facebook.com/apps\n"
            "Make sure you mark all permission of that app for no confusion")

    def create_creds(self):
        self.instruction_app_id_app_secret()
        app_id = input("app_id : ")
        app_secret = input("app_secret: ")
        self.creds = {
            "app_id": app_id,
            "app_secret": app_secret,
            "long_lived_access_token": ""
        }
        with open(self.file_path, 'w') as file:
            json.dump(self.creds, file)


class PageCommentIterator:
    def __init__(self, page_api: GraphAPI, get_page_post_comments_func: Callable, page_data: dict, post_data: dict):
        self.page_data = page_data
        self.post_data = post_data
        self.page_api = page_api
        self.get_page_post_comments = get_page_post_comments_func
        self.comments = {"data": []}
        self.next_cursor = ""
        self.current_selected_comment = 0
        self.done = False

    def load_comments(self):
        if len(self.comments['data']) == self.current_selected_comment:
            self.current_selected_comment = 0
        if self.current_selected_comment == 0:
            if len(self.next_cursor) == 0:
                self.comments = self.get_page_post_comments(self.page_api, self.page_data, self.post_data,
                                                            has_next=False,
                                                            next_cursor="")
                if len(self.comments['data']) == 0:
                    self.done = True
                else:
                    self.next_cursor = self.comments['paging']['cursors']['after']
            else:
                self.comments = self.get_page_post_comments(self.page_api, self.page_data, self.post_data,
                                                            has_next=True,
                                                            next_cursor=self.next_cursor)
                if len(self.comments['data']) == 0:
                    self.done = True
                else:
                    self.next_cursor = self.comments['paging']['cursors']['after']

    def __iter__(self):
        return self

    def __next__(self):
        self.load_comments()
        if self.done:
            raise StopIteration
        else:
            if len(self.comments['data']) > self.current_selected_comment:
                comment_ = self.comments['data'][self.current_selected_comment]
                self.current_selected_comment += 1  # updates in load_posts
                return comment_


class PagePostIterator:
    def __init__(self, page_api: GraphAPI, get_page_published_posts_func: Callable, page_data: dict):
        self.page_data = page_data
        self.page_api = page_api
        self.get_page_published_posts = get_page_published_posts_func
        self.posts = {"data": []}
        self.next_cursor = ""
        self.current_selected_post = 0
        self.done = False

    def load_posts(self):
        if len(self.posts['data']) == self.current_selected_post:
            self.current_selected_post = 0
        if self.current_selected_post == 0:
            if len(self.next_cursor) == 0:
                self.posts = self.get_page_published_posts(self.page_api, self.page_data, has_next=False,
                                                           next_cursor="")
                if len(self.posts['data']) == 0:
                    self.done = True
                else:
                    self.next_cursor = self.posts['paging']['cursors']['after']
            else:
                self.posts = self.get_page_published_posts(self.page_api, self.page_data, has_next=True,
                                                           next_cursor=self.next_cursor)
                if len(self.posts['data']) == 0:
                    self.done = True
                else:
                    self.next_cursor = self.posts['paging']['cursors']['after']

    def __iter__(self):
        return self

    def __next__(self):
        self.load_posts()
        if self.done:
            raise StopIteration
        else:
            if len(self.posts['data']) > self.current_selected_post:
                post_ = self.posts['data'][self.current_selected_post]
                self.current_selected_post += 1  # updates in load_posts
                return post_


class FacebookPageApi:
    def __init__(self, creds: Credentials):
        self.creds = creds
        self.api = creds.get_long_lived_api()

    def get_my_pages(self):
        return self.api.get_object("/me/accounts")

    def get_page_api(self, page_data: dict):
        page_api = GraphAPI(app_id=self.creds.get_app_id(), app_secret=self.creds.get_app_secret(),
                            access_token=page_data['page_access_token'])
        return page_api

    def get_page_published_posts(self, page_api: GraphAPI, page_data: dict, has_next=False, next_cursor=""):

        if not has_next:
            posts_data = page_api.get_object(f"/{page_data['page_id']}/published_posts")
            return posts_data
        else:
            posts_data = page_api.get_object(f"/{page_data['page_id']}/published_posts?after={next_cursor}")
            return posts_data

    def get_page_post_comments(self, page_api: GraphAPI, page_data: dict, post_data: dict, has_next=False,
                               next_cursor=""):

        if not has_next:
            comments_data = page_api.get_object(f"/{self.get_post_id(post_data)}/comments")
            return comments_data
        else:
            comments_data = page_api.get_object(f"/{self.get_post_id(post_data)}/comments?after={next_cursor}")
            return comments_data

    def get_post_text(self, post: dict):
        return post.setdefault("message", "STORY")

    def get_post_id(self, post: dict):
        return post['id']

    def get_comment_text(self, comment: dict):
        return comment.setdefault("message", "NONE")

    def get_reactions_count(self, page_api: GraphAPI, post: dict):
        """
        Supports v12.0
        :param page_api:
        :param post:
        :return:
        """
        reactions = page_api.get_object(
            object_id=f"/{self.get_post_id(post)}?fields=reactions.type(LIKE).limit(0).summary(1).as(like),reactions.type(LOVE).limit(0).summary(1).as(love),reactions.type(HAHA).limit(0).summary(1).as(haha),reactions.type(WOW).limit(0).summary(1).as(wow),reactions.type(SAD).limit(0).summary(1).as(sad),reactions.type(ANGRY).limit(0).summary(1).as(angry)&limit=10")
        print(reactions)
        return {"like": reactions['like']['summary']['total_count'],
                "love": reactions['love']['summary']['total_count'],
                "wow": reactions['wow']['summary']['total_count'],
                "haha": reactions['haha']['summary']['total_count'],
                "sad": reactions['sad']['summary']['total_count'],
                "angry": reactions['angry']['summary']['total_count']}

    def get_reactions_count_using_insights(self, page_api: GraphAPI, post: dict):
        reactions_insight = page_api.get_object(
            object_id=f"/{self.get_post_id(post)}/insights/post_reactions_by_type_total/lifetime")
        reactions = {}
        if len(reactions_insight['data']) > 0:
            reactions = reactions_insight['data'][0]['values'][0]['value']
        else:
            print(f"Something wrong with reactions insights. May be no reactions found")
            print(reactions_insight)
        return {"like": reactions.setdefault("like", 0), "love": reactions.setdefault("love", 0),
                "wow": reactions.setdefault("wow", 0), "haha": reactions.setdefault("haha", 0),
                "sad": reactions.setdefault("sorry", 0), "angry": reactions.setdefault("anger", 0), }

    def select_specific_page(self, pages_data):
        print("Enter 'exit' to exit")
        pages = pages_data['data']

        while True:
            for page_no in range(0, len(pages)):
                print(f"[{page_no}] : {pages[page_no]['name']}")
            try:
                selected = input("select page no : ")
                if selected.lower() == 'exit':
                    return "EXIT"
                selected = int(selected)
                if selected >= len(pages):
                    raise Exception("Invalid page number")
                return {"page_name": pages[selected]['name'], 'page_id': pages[selected]['id'],
                        'page_access_token': pages[selected]['access_token']}
            except:
                print("Invalid page no. Try again")
                continue


def validation_phase():
    cred = Credentials("credentials.json")
    cred.process_creds()
    cred.validate_creds()
    user_api = FacebookPageApi(creds=cred)
    pages = user_api.get_my_pages()
    return cred, user_api, pages


def core_phase(cred, user_api, pages):
    selected_page = user_api.select_specific_page(pages)
    if selected_page == 'EXIT':
        return "EXIT"
    # print(selected_page)
    print(f"{selected_page['page_name'].center(50, '_')}")
    selected_page_api = user_api.get_page_api(page_data=selected_page)
    total_post = 0
    output_file = f"{selected_page['page_name']}_{datetime.now().timestamp()}.json"
    # results = {'page_name':'','posts': [{'post_text': "", 'reactions': {}, 'comments': []}]}
    results = {'page_name': selected_page['page_name'], 'posts': []}
    in_total_comment = 0
    for post in PagePostIterator(selected_page_api, user_api.get_page_published_posts, selected_page):
        text = user_api.get_post_text(post)
        if text == "STORY":
            continue
        post_data = {'post_text': "", 'reactions': {}, 'comments': []}
        total_post += 1
        print("".center(50, "_"))
        print(f"POST - {total_post}".center(50, "#"))
        print(f"ID - {user_api.get_post_id(post)}".center(50, "#"))
        reacts = user_api.get_reactions_count_using_insights(selected_page_api, post)
        print(f"{reacts}")
        print("".center(50, "_"))
        print(text)
        post_data['post_text'] = text
        post_data['reactions'] = reacts
        print("COMMENTS ARE".center(50, "*"))
        total_comment = 0
        for comment in PageCommentIterator(selected_page_api, user_api.get_page_post_comments, selected_page, post):
            cmt = user_api.get_comment_text(comment)
            if cmt == "NONE":
                continue
            total_comment += 1
            in_total_comment += 1
            print(f"COMMENT - {total_comment}".center(50, "-"))
            print(cmt)
            post_data['comments'].append(cmt)
        results['posts'].append(post_data)
    print(
        f"{total_post} posts scraped from {selected_page['page_name']}. Total comments on {total_post} posts = {in_total_comment}")
    with open(output_file, 'w') as out_file:
        json.dump(results, out_file)
    print(f"Page scraped and saved in json file {output_file}")


if __name__ == "__main__":
    cred, user_api, pages = validation_phase()
    while True:
        if core_phase(cred, user_api, pages) == 'EXIT':
            break
