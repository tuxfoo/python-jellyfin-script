#!/bin/python3.10

# Version 0.4
# A script to update the metadata of a jellyfin server
# The intention is to fix the issues with the musicbrainz plugin such as:
#   - Missing musicbrainz track ids
#   - Issues with multi disc albums that do not have a disc number
#   - Issues with multi disc albums that have been split into multiple albums (In this case the script will merge the albums back into one album)
#   - Shuffle a whole playlist and create a new playlist from it (Jellyfin only shuffles 299 tracks at a time and cannot create a playlist from the shuffled tracks)

# This script is mostly for those who do not want to make any changes to the media files themselves


import requests
import json
import os
import sys
import getpass
import getopt
from random import shuffle

# Settings, You will need to change these to match your setup
jellyfin_server = "https://jellyfin.example.org"
jellyfin_api_key = "your jellyfin api key"



jellyfin_meta = "&SortBy=IndexNumber&mediaTypes=Audio"
jellyfin_metas = [
    "&Fields=ProviderIds",
    ",Genres",
    ",Tags",
    ",Studios",
    ",ParentId",
    ",MediaSources"
]
for meta in jellyfin_metas:
    jellyfin_meta += meta
musicbrainz_server = "https://musicbrainz.org/ws/2"


# Make sure the script is run with the correct arguments
if len(sys.argv) < 2:
    print("Usage: jellyfin_meta_data_updater.py [<musicbrainz_album_id> | all] [--dry-run] [--use-musicbrainz-metadata] [--verify-off] [--skip-existing] [--merge <album_id>] [--sort-alpha] [--help] [shuffle=<new_playlist_name>]")
    sys.exit(1)

# The first argument is the jellyfin album id
jellyfin_album_id = sys.argv[1]
# Not impleted yet - Will run without making any changes to the jellyfin server
dry_run = False
# Not impleted yet - Use all musicbrainz metadata instead of jellyfin metadata
use_musicbrainz_metadata = False
# Verify the changes before updating the jellyfin server
verify=True
# Skip albums that already have musicbrainz track ids
skip_existing = False
# Does not work - Merge albums that have been split into multiple albums, this can be a string or comma separated list of album ids
merge=None

new_playlist_name=None

sort_alpha=False
# Process optional arguments that can be in any order
try:
    opts, args = getopt.getopt(sys.argv[2:], "dbvsm:a", ["dry-run", "use-musicbrainz-metadata", "verify-off", "skip-existing", "merge=", "sort-alpha", "help", "shuffle="])
except getopt.GetoptError as err:
    print(err)
    sys.exit(1)

for opt, arg in opts:
    if opt == "--dry-run":
        dry_run = True
    elif opt == "--use-musicbrainz-metadata":
        use_musicbrainz_metadata = True
    elif opt == "--verify-off":
        verify = False
    elif opt == "--skip-existing":
        skip_existing = True
    elif opt == "--sort-alpha":
        sort_alpha = True
    elif opt == "--merge":
        merge = arg
        if merge == None:
            print("Error: You must specify an album id to merge")
            sys.exit(1)
    elif opt == "--help":
        help()
    elif opt == "--shuffle":
        new_playlist_name = arg
        if new_playlist_name == None:
            print("Error: You must specify a new playlist name")
            sys.exit(1)
    else:
        print("Usage: jellyfin_meta_data_updater.py [<musicbrainz_album_id> | all] [--dry-run] [--use-musicbrainz-metadata] [--verify-off] [--skip-existing] [--merge <album_id>]")
        sys.exit(1)

def help_doc():
    print("Usage: jellyfin_meta_data_updater.py [<musicbrainz_album_id> | all] [--dry-run] [--use-musicbrainz-metadata] [--verify-off] [--skip-existing] [--merge <album_id>]")
    print("You can use all instead of a musicbrainz album id to process all albums, eg: jellyfin_meta_data_updater.py all")
    print("--skip-existing: Skip albums that already have musicbrainz track ids")
    print("--sort-alpha: Sort the tracks by path (In case some weirdo has a multi disc album with the tracks labled 101 instead of 01 and in the same folder)")
    print("If you encountered the bug where jellyfin splits a multi disc album into multiple albums then you can still add metabrain id to tracks with the --merge option to merge the albums back into one album, eg: jellyfin_meta_data_updater.py <musicbrainz_album_id 1st Album> --merge <album_id 2nd, album_id 3rd>")
    sys.exit(1)

if jellyfin_album_id == "--help":
    help_doc()

def get_playlist(jellyfin_server, jellyfin_playlist_id):
    # Placeholder
    # A function to get a playlist from the jellyfin server
    headers = {
        "x-emby-authorization": f"MediaBrowser Client=\"jellyfin_meta_data_updater.py\", Device=\"jellyfin_meta_data_updater.py\", DeviceId=\"jellyfin_meta_data_updater.py\", Version=\"0.1\""
    }
    headers['x-mediabrowser-token'] = tokens[0]
    url = f"{jellyfin_server}/Playlists/{jellyfin_playlist_id}/Items?userId={tokens[1]}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.reason}")
        sys.exit(1)
    return response.json()

def save_playlist(playlist_name, playlist_items):
    # Placeholder
    # A function to save a playlist to the jellyfin server
    headers = {
        "x-emby-authorization": f"MediaBrowser Client=\"jellyfin_meta_data_updater.py\", Device=\"jellyfin_meta_data_updater.py\", DeviceId=\"jellyfin_meta_data_updater.py\", Version=\"0.1\"",
        "Content-Type": "application/json"
    }
    headers['x-mediabrowser-token'] = tokens[0]
    data = {
        "Name": playlist_name,
        "Ids": playlist_items,
        "MediaType": "Audio",
        "UserId": tokens[1]
    }
    url = f"{jellyfin_server}/Playlists"
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 204:
        print(f"Error: {response.status_code} {response.reason}")
        sys.exit(1)
    print(f"Created playlist: {playlist_name}")
    print(f"New playlist id: {response.json()}")
    return

def shuffle_playlist(playlist_id):
    # A function to shuffle a playlist on the jellyfin server
    playlist=get_playlist(jellyfin_server, playlist_id)

    playlist_items=[]
    for item in playlist["Items"]:
        playlist_items.append(item["Id"])

    shuffle(playlist_items)
    save_playlist(new_playlist_name, playlist_items)
    return

def jellyfin_auth_by_user(username, password):
    # Authenticate by user when elevated permissions are required
    headers = {
        "x-emby-authorization": f"MediaBrowser Client=\"jellyfin_meta_data_updater.py\", Device=\"jellyfin_meta_data_updater.py\", DeviceId=\"jellyfin_meta_data_updater.py\", Version=\"0.1\"",
        "Content-Type": "application/json"
    }
    data = {
        "Username": username,
        "Pw": password
    }
    url = f"{jellyfin_server}/Users/AuthenticateByName"
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.reason}")
        sys.exit(1)
    return response.json().get("AccessToken"), response.json().get("User").get("Id")

def prompt_for_username_password():
    username = input("Username: ")
    password = getpass.getpass('Password:')
    return jellyfin_auth_by_user(username, password)

def get_albums(jellyfin_server):
    # Get all the albums from the jellyfin server
    # Requires authentication
    headers = {
        "x-emby-authorization": f"MediaBrowser Client=\"jellyfin_meta_data_updater.py\", Device=\"jellyfin_meta_data_updater.py\", DeviceId=\"jellyfin_meta_data_updater.py\", Version=\"0.1\""
    }
    headers['x-mediabrowser-token'] = tokens[0]
    url = f"{jellyfin_server}/Items?userId={tokens[1]}&SortBy=SortName&IncludeItemTypes=MusicAlbum&filters=IsFolder&Recursive=true&Fields=ProviderIds"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"URL: {url}")
        print(f"Error: {response.status_code} {response.reason}")
        sys.exit(1)
    return response.json()["Items"]

def get_album_musicbrains_ids(jellyfin_server, jellyfin_api_key, jellyfin_album_id):
    # Get the album artist id from the jellyfin server
    headers = {
        "x-emby-token": jellyfin_api_key
    }
    url = f"{jellyfin_server}/Items?Ids={jellyfin_album_id}&Fields=ProviderIds"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.reason}")
        sys.exit(1)
    # Check if the album has a musicbrainz album id
    if "MusicBrainzAlbum" in response.json()["Items"][0]["ProviderIds"] and "MusicBrainzReleaseGroup" in response.json()["Items"][0]["ProviderIds"]:
        musicbrainz_album_id = response.json()["Items"][0]["ProviderIds"]["MusicBrainzAlbum"]
        release_id = response.json()["Items"][0]["ProviderIds"]["MusicBrainzReleaseGroup"]
        return musicbrainz_album_id, release_id, response.json()["Items"][0]["Name"]
    else:
        return False, response.json()["Items"][0]["Name"]

def get_album_tracks(jellyfin_server, jellyfin_api_key, jellyfin_album_id):
    # Get all the tracks from the jellyfin server for the album
    headers = {
        "x-emby-token": jellyfin_api_key
    }
    url = f"{jellyfin_server}/Items?ParentId={jellyfin_album_id}{jellyfin_meta}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"URL: {url}")
        print(f"Error: {response.status_code} {response.reason}")
        sys.exit(1)
    if response.json()["TotalRecordCount"] == 0:
        print(f"Error: No tracks found for album id: {jellyfin_album_id}, it is problably a multi disc album")
        url = f"{jellyfin_server}/Items?ParentId={jellyfin_album_id}&fields=ParentId,MediaSources&includeItemTypes=Folder&SortBy=SortName"
        discs = requests.get(url, headers=headers)
        if discs.status_code != 200:
            print(f"URL: {url}")
            print(f"Error: {discs.status_code} {discs.reason}")
            sys.exit(1)
        tracks = []
        for disc in discs.json()["Items"]:
            url = f"{jellyfin_server}/Items?ParentId={disc['Id']}{jellyfin_meta}"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"URL: {url}")
                print(f"Error: {response.status_code} {response.reason}")
                sys.exit(1)
            tracks += response.json()["Items"], True
    else:
        tracks = response.json()["Items"]
    return tracks, False

def get_single_track_info(jellyfin_server, jellyfin_api_key, jellyfin_track_id):
    # Get all the tracks from the jellyfin server for the album
    headers = {
        "x-emby-token": jellyfin_api_key
    }
    url = f"{jellyfin_server}/Items?Ids={jellyfin_track_id}"
    response = requests.get(url, headers=headers)
    if response.json()["TotalRecordCount"] == 0:
        print(f"Error: No tracks found for album id: {jellyfin_album_id}")
        url = f"{jellyfin_server}/Items?ParentId={jellyfin_album_id}"
        response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"URL: {url}")
        print(f"Error: {response.status_code} {response.reason}")
        sys.exit(1)
    track = response.json()
    return track

def get_musicbrainz_track_ids(musicbrainz_server, musicbrainz_album_id):
    # Get the musicbrainz track ids from the musicbrainz server
    headers = {
        "Accept": "application/json",
        "User-Agent": "jellyfin_meta_data_updater.py/0.1"
    }
    url = f"{musicbrainz_server}/release/{musicbrainz_album_id}?inc=recordings"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"URL: {url}")
        print(f"Error: {response.status_code} {response.reason}")
        sys.exit(1)
    return response.json()

def jellyfin_musicbrain_trackid_update(jellyfin_server, track_data, musicbrainz_track, musicbrainz_track_data):
    # Update the jellyfin server with the musicbrainz track id
    # Requires authentication
    headers = {
        "x-emby-authorization": f"MediaBrowser Client=\"jellyfin_meta_data_updater.py\", Device=\"jellyfin_meta_data_updater.py\", DeviceId=\"jellyfin_meta_data_updater.py\", Version=\"0.1\"",
        "Content-Type": "application/json"
    }
    headers['x-mediabrowser-token'] = tokens[0]

    # If the track numbers don't match then skip
    '''
    if int(track_data["IndexNumber"]) != int(musicbrainz_track["number"]):
        print(f"Track number mismatch, skipping")
        return
    '''
    # Check musicbrainz_track_ids to see if there are multiple discs
    if len(musicbrainz_track_data) > 1:
        print(f"Multiple discs found")
        for disc in musicbrainz_track_data:
            if disc["format"] == "DVD-Video":
                if "ParentIndexNumber" not in track_data:
                    track_data["ParentIndexNumber"] = ""
                break
            for track in disc["tracks"]:
                if track == musicbrainz_track:
                    print(f"Disc: {disc['position']}")
                    print(f"Track: {track['number']}")
                    track_data["IndexNumber"] = track["number"]
                    track_data["ParentIndexNumber"] = disc["position"]
                    break
    else:
        track_data["ParentIndexNumber"] = ""
    # Check if the track has the required keys
    if "Studios" not in track_data:
        track_data["Studios"] = []
    if "PremiereDate" not in track_data:
        track_data["PremiereDate"] = ""
    if "ProductionYear" not in track_data:
        track_data["ProductionYear"] = ""
    if "Genres" not in track_data:
        track_data["Genres"] = []
    data = {
        "Id": track_data["Id"],
        "Name": track_data["Name"],
        "IndexNumber": track_data["IndexNumber"],
        "Album": track_data["Album"],
        # Only add the Name Keys for all the AlbumArtists
        "AlbumArtists": [ { "Name": artist["Name"] } for artist in track_data["AlbumArtists"] ],
        "ArtistItems": [ { "Name": artist["Name"] } for artist in track_data["ArtistItems"] ],
        "Genres": track_data["Genres"],
        "Tags": [],
        "Studios": [ { "Name": studio["Name"] } for studio in track_data["Studios"] ],
        "PremiereDate": track_data["PremiereDate"],
        "ProductionYear": track_data["ProductionYear"],
        "ParentIndexNumber": track_data["ParentIndexNumber"],
        "ProviderIds": {
            # If keys are not set then then the values are set to null
            "MusicBrainzTrack": musicbrainz_track["id"],
            "MusicBrainzAlbumArtist": "",
            "MusicBrainzAlbum": "",
            "MusicBrainzArtist": "",
            "MusicBrainzReleaseGroup": "",
            "AudioDbAlbum": "",
            "AudioDbArtist": ""
        }
    }
    if merge != None:
        # Attempt to merge the albums by changing the ParentId for each track
        data['AlbumId'] = jellyfin_album_id
        data['ParentId'] = jellyfin_album_id
        data['AlbumPrimaryImageTag'] = track_data['AlbumPrimaryImageTag']
        data['ImageBlurHashes'] = track_data['ImageBlurHashes']
        # Lock the album to prevent jellyfin automatically splitting the album again
        data['LockData'] = True

    print(f"Data: {json.dumps(data)}")
    url = f"{jellyfin_server}/Items/{track_data['Id']}"

    response = "Null"
    if not dry_run:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 204:
            print(f"URL: {url}")
            print(f"Error: {response.status_code} {response.reason}")
            sys.exit(1)
    else:
        print(f"Data: {data}")

    return response

def get_multi_disc_children(jellyfin_server, jellyfin_api_key, jellyfin_album_id):
    # Get all the tracks from the jellyfin server for the album
    headers = {
        "x-emby-token": jellyfin_api_key
    }
    url = f"{jellyfin_server}/Items?ParentId={jellyfin_album_id}&fields=ParentId,MediaSources&includeItemTypes=Folder&SortBy=SortName"
    print(f"URL: {url}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.reason}")
        sys.exit(1)
    return response.json()["Items"]

def jellyfin_album_musicbrainz_trackid_update(jellyfin_server, album_tracks, musicbrainz_track_data):
    # Get all the tracks from the jellyfin server for the album
    #print(json.dumps(musicbrainz_track_data, indent=4))
    m_indx = 0
    # jf_indx is used to split the tracks into discs
    jf_indx = 0
    AlbumPrimaryImageTag = None
    ImageBlurHashes = None
    for item in album_tracks:
        if item["Type"] != "Audio":
            continue
        jf_indx += 1
        print(f"Loop Index: {str(jf_indx)}")
        print(f"Track: {item['Name']}")
        print(f"Track id: {item['Id']}")
        print(f"Track Artists:")
        for artist in item["Artists"]:
            print(artist)
        print(f"Provider id: {str(item['ProviderIds'])}")
        # Check if the track has IndexNumber Key
        if "IndexNumber" in item:
            print(f"Track number: {str(item['IndexNumber'])}")
        else:
            print("Track number: None")
        # If MusicBrainzTrack is already set then skip
        disc_track_count = int(musicbrainz_track_data[m_indx]["track-count"])

        if "MusicBrainzTrack" in item["ProviderIds"]:
            print(f"MusicBrainzTrack: {item['ProviderIds']['MusicBrainzTrack']}")
            print("MusicBrainzTrack already set, skipping")
            if int(jf_indx) >= int(musicbrainz_track_data[m_indx]['track-count']):
                m_indx += 1
                jf_indx = 0
            continue
        # Check if current index exists and return if not, to prevent out of range error      
        if m_indx >= len(musicbrainz_track_data):
            print("Musicbrainz track data index out of range, skipping")
            return
        if m_indx == 0:
            AlbumPrimaryImageTag = item['AlbumPrimaryImageTag']
            ImageBlurHashes = item['ImageBlurHashes']
            item['AlbumPrimaryImageTag'] = AlbumPrimaryImageTag
            item['ImageBlurHashes'] = ImageBlurHashes
        if not musicbrainz_track_data[m_indx]['tracks'][jf_indx-1]['recording']['video']:
            #print(json.dumps(musicbrainz_track_data[m_indx]['tracks'][item["IndexNumber"]-1]))
            jellyfin_musicbrain_trackid_update(jellyfin_server, item, musicbrainz_track_data[m_indx]['tracks'][jf_indx-1], musicbrainz_track_data)
        # Check of the item index is higher than the number of tracks in the disc
        if jf_indx >= int(disc_track_count):
            m_indx += 1
            jf_indx = 0
    return
        
def jellyfin_search_musicbrainz_track_id_exists(album_tracks):
    # Search the album tracks for the MusicBrainzTrack id
    for item in album_tracks[0]:
        if "MusicBrainzTrack" in item["ProviderIds"]:
            return True
    return False

def unnest_items(item, key, item_type="Audio"):
    # A function to unnest all dicts and return a single list of dicts
    items_list=[]
    if type(item) == dict or type(item) == list or type(item) == tuple:
        for k in item:
            if type(k) == list:
                items_list += unnest_items(k, key, item_type)      
            if type(k) == dict:
                if key in k:
                    if type(k) == dict:
                        if k["Type"] == item_type:
                            items_list.append(k)
    return items_list

def sort_tracks_by_index_number(album_tracks):
    # Sort the album tracks by IndexNumber
    album_tracks.sort(key=lambda x: x["IndexNumber"])
    # If ParentIndexNumber is set then sort by ParentIndexNumber
    if "ParentIndexNumber" in album_tracks[0]:
        album_tracks.sort(key=lambda x: x["ParentIndexNumber"])
    return album_tracks

def process_album(album):
    album_artist_id=get_album_musicbrains_ids(jellyfin_server, jellyfin_api_key, album)
    # skip albums without a musicbrainz album id
    # check if first item in tuple is a boolean
    if isinstance(album_artist_id[0], bool):
        if not album_artist_id[0]:
            print(f"No musicbrainz album id found for album: {album_artist_id[1]}, {album}, Skipping")
            return False, album_artist_id[1], "NOALBUMMBID"
    
    print(f"Getting tracks data for album: {album} from jellyfin server: {jellyfin_server}")

    album_tracks=get_album_tracks(jellyfin_server, jellyfin_api_key, album)
    if merge != None:
        if type(merge) == list:
            for album_id in merge:
                album_tracks+=get_album_tracks(jellyfin_server, jellyfin_api_key, album_id)
        else:
            album_tracks+=get_album_tracks(jellyfin_server, jellyfin_api_key, merge)
        # Nest once because I am too lazy to fix test the unnest_items function in multi scenarios
        tracks=[]
        tracks.append(album_tracks)
        album_tracks=tracks
    #print(json.dumps(album_tracks, indent=4))
    # Check if the track in the album contains a musicbrainz track id and is Type Audio and contains Audio key
    album_tracks=unnest_items(album_tracks[0], "Name", "Audio")
    print(f"Getting musicbrainz track data for album: {album_artist_id[2]}, {album_artist_id[0]} from musicbrainz server: {musicbrainz_server}")
    musicbrainz_track_data=get_musicbrainz_track_ids(musicbrainz_server, album_artist_id[0])

    if sort_alpha:
        album_tracks.sort(key=lambda x: x["MediaSources"][0]["Path"])
    #print(json.dumps(musicbrainz_track_data, indent=4))
    # Show information from both musicbrainz and jellyfin for comparison and confirmation
    if verify:
        if album_tracks == []:
            nested_albums=get_multi_disc_children(jellyfin_server, jellyfin_api_key, album)
            for item in nested_albums:
                if item["Type"] == 'Folder':
                    nested_album_tracks=get_album_tracks(jellyfin_server, jellyfin_api_key, item["Id"])
                    album_tracks+=unnest_items(nested_album_tracks, "Name", "Audio")
            album_tracks=unnest_items(album_tracks, "Name", "Audio")

        # check the first and last track are lists
        if type(album_tracks) != list or album_tracks == []:
            print("Error: There was a problem retrieving the metadata from Jellyfin")
            return False, album_artist_id[2], "METADATARETRIEVALERROR"
        
        first_track=album_tracks
        last_track=album_tracks

        #print(json.dumps(musicbrainz_track_data['media'], indent=4))
        # Check the Name key exists for first and last track
        if  "Name" not in first_track[0] or "Name" not in last_track[-1]:
            print("Error: There was a problem retrieving the metadata from Jellyfin")
            return False, album_artist_id[2], "METADATARETRIEVALERROR"
        # Compare album titles
        print(f"album title; Jellyfin  : {album_artist_id[2]}, Musicbrainz: {musicbrainz_track_data['title']}")
        # Compare first track
        print(f"first track; Jellyfin  : {first_track[0]['Name']}, Musicbrainz: {musicbrainz_track_data['media'][0]['tracks'][0]['recording']['title']}")
        # Compare last track
        print(f"last track; Jellyfin   : {last_track[-1]['Name']}, Musicbrainz: {musicbrainz_track_data['media'][-1]['tracks'][-1]['recording']['title']}")
        # Compare number of tracks
        # Get the number of tracks from each disc on musicbrainz and add them together
        mb_tracks=0
        for disc in musicbrainz_track_data['media']:
            mb_tracks += int(disc['track-count'])
        print(f"number of tracks; Jellyfin: {len(album_tracks)}, Musicbrainz: {mb_tracks}")
        if "MusicBrainzTrack" in first_track[0]["ProviderIds"] and "MusicBrainzTrack" in last_track[-1]["ProviderIds"]:
                print(f"MusicBrainzTrack already set for tracks in this album")
                if skip_existing:
                    print("Skipping")
                    return False, album_artist_id[2], "ALREADYSET"
        # Check if album if Vinyl
        print(musicbrainz_track_data["media"][0]["format"])
        if "Vinyl" in musicbrainz_track_data["media"][0]["format"]:
            # Prompt and accept all input to continue
            confirmation = input("This script does not work with Vinyl Albums, Are you sure Jellyfin detected album MBID correctly?:")
            print("Aborting")
            return False, album_artist_id[2], "VINYL"
        if merge != None:
            print("Merge currently does not work as intended (Does not merge), it will however update all the albums with the correct metabrainz track ids.")
        confirmation = input("Confirm? [y/N]: ")
        if confirmation.lower() != "y":
            print("Aborting")
            return False, album_artist_id[2], "ABORTED"
    print(f"Updating album: {album_artist_id[1]}, {album} with musicbrainz track ids")
    jellyfin_album_musicbrainz_trackid_update(jellyfin_server, album_tracks, musicbrainz_track_data['media'])

    #print(get_single_track_info(jellyfin_server, jellyfin_api_key, jellyfin_album_id))
    return True, album_artist_id[2], "UPDATED"

skipped_albums = []
print("This works for single disc albums only")
print("It relies on the MBID for the album being correctly set in jellyfin")
print("Sometimes the MBID is not set correctly in jellyfin")
print("By default the script will output a comparison of the album and tracks from jellyfin and musicbrainz for confirmation")
print("Enter username and password for jellyfin server")
tokens=prompt_for_username_password()
if sys.argv[1] != "all":
    jellyfin_album_id = sys.argv[1]
    if new_playlist_name != None:
        shuffle_playlist(jellyfin_album_id)
        exit()
    process_album(jellyfin_album_id)
elif sys.argv[1] == "all":
    if merge:
        print("Merge cannot be used with all")
        sys.exit(1)
    albums = get_albums(jellyfin_server)
    print("Processing all albums")
    for album in albums:
        current_album=process_album(album["Id"])
        if not current_album[0]:
            skipped_albums.append({current_album[1], current_album[2]})
    # Print skipped albums
    print("Skipped albums:")
    for album in skipped_albums:
        print(album)