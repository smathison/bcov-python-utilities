import requests
import urllib2, json

###################################
#YOUR ACCOUNT ID
account_id = "YOUR_ACCOUNT_ID"

#YOUR BASE 64 ENCODED CONCAT CLIENT ID AND CLIENT SECRET
client_string = "YOUR_CLIENT_STRING"

#YOUR INGEST PROFILE
ingest_profile = "multi-platform-standard-static"

#YOUR CUSTOM SEARCH QUERY - THIS IS REQUIRED
search_query = 'created_at:2018-02-01T12:30:31.527Z..2018-03-01T12:30:31.527Z'
####################################


token = ''
list_of_video_ids = []
number_of_videos = ''

#Get access token
def get_access_token():
	url = "https://oauth.brightcove.com/v3/access_token"

	payload = "grant_type=client_credentials"
	headers = {
	    'authorization': "Basic " + str(client_string),
	    'content-type': "application/x-www-form-urlencoded",
	    'cache-control': "no-cache"
	    }

	response = requests.request("POST", url, data=payload, headers=headers)

	access_token = response.text

	resp_dict = json.loads(access_token)

	global token 

	token = resp_dict['access_token']


def get_number_of_videos():
	
	global number_of_videos 
	number_of_videos = ''

	#Get all videos - need to edit this to get only a list of video IDs and store in a variable. Then go through each video one at a time and get the poster and thumbnail URL, reingest with a new profile
	
	#BELOW URL FOR USE WITHOUT CUSTOM SEARCH QUERY
	#url = "https://cms.api.brightcove.com/v1/accounts/" + str(account_id) + "/counts/videos"

	url = "https://cms.api.brightcove.com/v1/accounts/" + str(account_id) + "/counts/videos?q=" + search_query
	headers = {
	    'authorization': "Bearer " + token,
	    'cache-control': "no-cache"
	    }

	response = requests.request("GET", url, headers=headers, timeout=10)

	number_formatted = json.loads(response.text)

	number_of_videos = number_formatted['count']

def get_video_ids():
#Get all videos - need to edit this to get only a list of video IDs and store in a variable. Then go through each video one at a time and get the poster and thumbnail URL, reingest with a new profile
	
	offset = 0
	completed = 0
	global list_of_video_ids 
	list_of_video_ids = []

	print("There are " + str(number_of_videos) + " videos to process. Retrieving videos...")

	while completed < number_of_videos:

		url = "https://cms.api.brightcove.com/v1/accounts/" + str(account_id) + "/videos?q=" + search_query + "&limit=100&offset=" + str(offset)

		#BELOW URL FOR USE WITHOUT CUSTOM SEARCH QUERY
		#url = "https://cms.api.brightcove.com/v1/accounts/" + str(account_id) + "/videos?limit=100&offset=" + str(offset)

		headers = {
		    'authorization': "Bearer " + token,
		    'cache-control': "no-cache"
		    }

		videos = requests.request("GET", url, headers=headers, timeout=10)

		video_list = json.loads(videos.text)
		#print(video_list)

		current_list = []

		for video in video_list:
			current_list.append(video['id'])	

		list_of_video_ids.extend(current_list)

		offset += 100
		completed += 100
		print("Successfully retrieved videos up to " + str(offset))
		get_access_token()	

#Iterate over lisf_of_video_ids, fetching the poster URL for each and reingesting using new profile
def process_images():
	i = 0

	while i < len(list_of_video_ids):
		try:

			video_id = list_of_video_ids[i]

			url = "https://cms.api.brightcove.com/v1/accounts/" + str(account_id) + "/videos/" + video_id + "/images"

			headers = {
			    'authorization': "Bearer " + token,
			    'content-type': "application/json",
			    'cache-control': "no-cache"
			    }

			response = requests.request("GET", url, headers=headers, timeout=10)

			formatted = json.loads(response.text)

			if formatted != {}:
				 
				if 'poster' in formatted:


					poster_object = formatted['poster']

					poster_src = poster_object['src']

					url = "https://ingest.api.brightcove.com/v1/accounts/" + str(account_id) + "/videos/" + video_id + "/ingest-requests"

					payload = "{\n    \"profile\": \"%s\",\n    \"poster\": {\n        \"url\": \"%s\"\n     }\n}" % (ingest_profile, poster_src)
					headers = {
						    'authorization': "Bearer " + token,
						    'content-type': "application/json",
						    'cache-control': "no-cache"
						    }

					response2 = requests.request("POST", url, data=payload, headers=headers, timeout=10)

					print(video_id + " poster processed successfully...")
					print(response2.text)

				else:
					print(video_id + " does not have a poster image, skipping...")

				if 'thumbnail' in formatted:
					thumbnail_object = formatted['thumbnail']

					thumbnail_src = thumbnail_object['src']

					url = "https://ingest.api.brightcove.com/v1/accounts/" + str(account_id) + "/videos/" + video_id + "/ingest-requests"

					payload = "{\n    \"profile\": \"%s\",\n    \"thumbnail\": {\n        \"url\": \"%s\"\n     }\n}" % (ingest_profile, thumbnail_src)
					headers = {
					    'authorization': "Bearer " + token,
					    'content-type': "application/json",
					    'cache-control': "no-cache"
					    }

					response3 = requests.request("POST", url, data=payload, headers=headers, timeout=10)


					print(video_id + " thumbnail processed successfully...")
					print(response3.text)

				else:
					print(video_id + " does not have a thumbnail image, skipping...")	

				get_access_token()
				i += 1

			else: 
				print(video_id + " does not have any images, skipping...")
				get_access_token()
				i += 1	

		except requests.exceptions.RequestException as e: 
    			print e
    

get_access_token()

get_number_of_videos()

get_video_ids()

process_images()