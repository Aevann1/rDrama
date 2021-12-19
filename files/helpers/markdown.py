from .get import *

from mistletoe.span_token import SpanToken
from mistletoe.html_renderer import HTMLRenderer
import re

from flask import g


# add token/rendering for @username mentions


class UserMention(SpanToken):

	pattern = re.compile("(^|\s|\n)@((\w|-){1,25})")
	parse_inner = False

	def __init__(self, match_obj):
		self.target = (match_obj.group(1), match_obj.group(2))
		
class SubMention(SpanToken):

	pattern = re.compile("(^|\s|\n)r/(\w{3,25})")
	parse_inner = False

	def __init__(self, match_obj):

		self.target = (match_obj.group(1), match_obj.group(2))
		
class RedditorMention(SpanToken):

	pattern = re.compile("(^|\s|\n)u/((\w|-){3,25})")
	parse_inner = False

	def __init__(self, match_obj):

		self.target = (match_obj.group(1), match_obj.group(2))
		
class SubMention2(SpanToken):

	pattern = re.compile("(^|\s|\n)/r/(\w{3,25})")
	parse_inner = False

	def __init__(self, match_obj):

		self.target = (match_obj.group(1), match_obj.group(2))
		
class RedditorMention2(SpanToken):

	pattern = re.compile("(^|\s|\n)/u/((\w|-){3,25})")
	parse_inner = False

	def __init__(self, match_obj):

		self.target = (match_obj.group(1), match_obj.group(2))

class CustomRenderer(HTMLRenderer):

	def __init__(self, **kwargs):
		super().__init__(UserMention,
						 SubMention,
						 RedditorMention,
						 SubMention2,
						 RedditorMention2,
						 )

		for i in kwargs:
			self.__dict__[i] = kwargs[i]

	def render_user_mention(self, token):
		space = token.target[0]
		target = token.target[1]

		user = get_user(target, graceful=True)


		if not user: return f"{space}@{target}"

		return f'''{space}<a href="{user.url}"><img alt="@{user.username}'s profile picture" loading="lazy" src="/uid/{user.id}/pic" class="pp20">@{user.username}</a>'''
			
	def render_sub_mention(self, token):
		space = token.target[0]
		target = token.target[1]
		return f'{space}<a href="https://old.reddit.com/r/{target}" rel="nofollow noopener noreferrer" class="d-inline-block">r/{target}</a>'
		
	def render_redditor_mention(self, token):
		space = token.target[0]
		target = token.target[1]
		return f'{space}<a href="https://old.reddit.com/u/{target}" rel="nofollow noopener noreferrer" class="d-inline-block">u/{target}</a>'


class Renderer(HTMLRenderer):

	def __init__(self, **kwargs):
		super().__init__(UserMention,
						 SubMention,
						 RedditorMention,
						 SubMention2,
						 RedditorMention2,
						 )

		for i in kwargs:
			self.__dict__[i] = kwargs[i]

	def render_user_mention(self, token):
		space = token.target[0]
		target = token.target[1]

		user = get_user(target, graceful=True)

		if not user: return f"{space}@{target}"

		return f'{space}<a href="{user.url}">@{user.username}</a>'
			
	def render_sub_mention(self, token):
		space = token.target[0]
		target = token.target[1]
		return f'{space}<a href="https://old.reddit.com/r/{target}" rel="nofollow noopener noreferrer" class="d-inline-block">r/{target}</a>'
		
	def render_redditor_mention(self, token):
		space = token.target[0]
		target = token.target[1]
		return f'{space}<a href="https://old.reddit.com/u/{target}" rel="nofollow noopener noreferrer" class="d-inline-block">u/{target}</a>'