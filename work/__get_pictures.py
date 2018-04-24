#!/usr//bin/python3


# Get image URLs from html page:


import re
import requests

def main():
	r = requests.get('https://cs.wikipedia.org/wiki/Pablo_Picasso')
	myList = re.findall(r'<img.*?>', r.text);
	for img in myList:
		print(re.search(r'src="(.*?)"',img).group(1))


main()
