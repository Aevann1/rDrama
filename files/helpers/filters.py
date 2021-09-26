from bs4 import BeautifulSoup
from flask import *
from urllib.parse import urlparse
from files.classes import BannedDomain
from sqlalchemy.orm import lazyload

def filter_comment_html(html_text):

	soup = BeautifulSoup(html_text, features="html.parser")

	links = soup.find_all("a")

	domain_list = set()

	for link in links:

		href=link.get("href", None)
		if not href:
			continue

		domain = urlparse(href).netloc

		# parse domain into all possible subdomains
		parts = domain.split(".")
		for i in range(len(parts)):
			new_domain = parts[i]
			for j in range(i + 1, len(parts)):
				new_domain += "." + parts[j]

				domain_list.add(new_domain)

	# search db for domain rules that prohibit commenting
	bans = [x for x in g.db.query(BannedDomain).options(lazyload('*')).filter(BannedDomain.domain.in_(list(domain_list))).all()]

	if bans:
		return bans
	else:
		return []
