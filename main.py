import argparse
import requests
import os
from getpass import getpass
from pathlib import Path

def authenticate(url,username):
    if username == None:
        while True:
            username = input("Enter Username: ") or None
            if username:
                break
            else:
                print("Username cant be empty")
    while True:
        password = getpass() or None
        if password:
            break
        else:
            print("Invalid password.")

    AUTH_HEADER = (
        'MediaBrowser '
        'Client="Python Script", '
        'Device="Python Script Device", '
        'DeviceId="python-script-unique-id-12345", '
        'Version="12.1.0"'
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTH_HEADER
    }

    auth_data = {
        "Username": username,
        "Pw": password
    }

    endpoint = f"{url}/Users/authenticatebyname"
    print(endpoint)
    try:
        response = requests.post(endpoint, json=auth_data, headers=headers)
        if response.status_code == 200:
            result = response.json()

            access_token = result.get("AccessToken")
            user_id = result.get("User", {}).get("Id")
            headers["Authorization"] += f', Token="{access_token}"'
            print("✅ Authentication successful!\n")

            items_url = f"{url}/Users/{user_id}/Items"
            items_response = requests.get(items_url, headers=headers)

            if items_response.status_code == 200:

                return headers

        else:
            print(f"❌ Failed to authenticate. Status code: {response.status_code}")
            print(response.text)
            print(f"\nScript Stopped")
            exit()

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        print(f"\nScript Stopped")
        exit()

def jellyfin_search(url,headers,type=None,title=None):
    url = f"{url}/Items"
    if type == None:
        type = (input("Is this a tv show or movie? (tv)/movie: ") or "tv").lower()
    if type == 'movie':
        includeItemTypes = "Movie"
    if type == 'tv' or type == 'tv show':
        includeItemTypes = "Series"
        type = "tv show"
    #TO DO - Get music downloading working
    # if type == 'music':
    #     includeItemTypes = "Audio"

    while True:
        if title == None:
            title = input(f"{type} title: ")
        search_params = {
            "SearchTerm": title,
            "IncludeItemTypes": includeItemTypes,
            "Recursive": True,
            "Fields": "Overview,ProductionYear"
        }

        try:
            response = requests.get(url, headers=headers, params=search_params)
            if response.status_code == 200:
                search_results = response.json()
                items = search_results.get("Items", [])
                if len(items) == 0:
                    print(f"🔍 Found {len(items)} {type} matching '{title}'. Try again")
                else:
                    print(f"🔍 Found {len(items)} {type} matching '{title}':\n")
                    return type, items
            else:
                print(f"❌ Search failed. Status code: {response.status_code}")
                print(response.text)
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

def jellyfin_search_parse(type,items):
    if len(items) > 1:
        print(f"Select the correct {type} you want to download:\n")
        count = 1
        for item in items:
            if item != None:
                title = item.get("Name")
                year = item.get("ProductionYear", "Unknown Year")
                print(f"{count}) {title} ({year})")
                count = count + 1
        while True:
            index = int(input(f"Enter selection(1): ") or 1)
            if (index + 1) <= count and index > 0:
                index = (index - 1)
                break
            else:
                print("Invalid selection. Try again")
    else:
        index = 0
    result_title = items[index].get("Name")
    result_id = items[index].get("Id")
    result_year = items[index].get("ProductionYear", "Unknown Year")
    return result_title, result_id, result_year

def get_media_info(id,url,headers):
    file_info_url = f"{url}/Items/{id}"
    try:
        response = requests.get(file_info_url,headers=headers)
        if response.status_code == 200:
            results = response.json()
            file_type = (results.get("Path")).split('.')[-1]
            return file_type
        else:
            print(f"❌ failed to get file metadata. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def movie_selection(title,id,year,url,headers):
    return_results = []
    movie_url = f"{url}/Items/{id}"
    try:
        response = requests.get(movie_url,headers=headers)
        if response.status_code == 200:
            search_results = response.json()
            items = search_results.get("MediaSources", [])
            if len(items) > 1:
                print(f"🔍 Found {len(items)} media files results matching '{title}':\n")
                print(f"Select the version you want to download:\n")
                count = 1
                for item in items:
                    if item != None:
                        name = item.get("Name")
                        id = item.get("Id")
                        file_type = (item.get("Path")).split('.')[-1]
                        media_object = dict(title=title,year=year,name=name,id=id,file_type=file_type)
                        return_results.append(media_object)
                        print(f"{count}) {title} - {name}")
                        count = count + 1
                print(f"{count}) All")
                while True:
                    index = input(f"Enter number for selection: ")
                    if int(index) == count:
                        index = "all"
                        break
                    elif (int(index) - 1) < count:
                        index = (int(index) - 1)
                        break
                    else:
                        print("Invalid selection. Try again")
            else:
                index = 0
                name = items[index].get("Name")
                id = items[index].get("Id")
                file_type = (items[index].get("Path")).split('.')[-1]
                media_object = dict(title=title,year=year,name=name,id=id,file_type=file_type)
                return_results.append(media_object)
            if index == "all":
                return return_results
            else:
                return [return_results[index]]
        else:
            print(f"❌ Search failed. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def tv_season_selection(title,id,url,headers,all=None):
    return_results = []
    season_results = []
    seasons_url = f"{url}/Shows/{id}/Seasons"
    try:
        response = requests.get(seasons_url,headers=headers)
        if response.status_code == 200:
            search_results = response.json()
            items = search_results.get("Items", [])
            if len(items) > 1:
                print(f"🔍 Found {len(items)} seasons for '{title}':\n")
                print(f"Select season to download:\n")
                count = 1
                for item in items:
                    if item != None:
                        name = int(item.get("Name").split(' ')[-1])
                        season_id = item.get("Id")
                        season_object = dict(series=title,name=name,season_id=season_id,parent_id=id)
                        season_results.append(season_object)
                        print(f"{count}) {title} - Season {name}")
                        count = count + 1
                if all == None:
                    print(f"{count}) All")
                    while True:
                        index = input(f"Enter number for selection: ")
                        if int(index) == count:
                            index = "all"
                            break
                        elif (int(index) - 1) < count:
                            index = (int(index) - 1)
                            break
                        else:
                            print("Invalid selection. Try again")
                else:
                    index = "all"
            else:
                print(f"🔍 Found {len(items)} seasons for '{title}':\n")
                for item in items:
                    if item != None:
                        name = int(item.get("Name").split(' ')[-1])
                        season_id = item.get("Id")
                        season_object = dict(series=title,name=name,season_id=season_id,parent_id=id)
                        season_results.append(season_object)
                if all == None:
                    index = 0
                else:
                    index = "all"
            if index == "all":
                for season in season_results:
                    result_dict = season
                    series_name = result_dict.get("series", result_dict.get("SeriesName"))
                    season_name = result_dict.get("name", result_dict.get("Name"))
                    parent_id = result_dict.get("parent_id", result_dict.get("SeriesId"))
                    season_id = result_dict.get("season_id", result_dict.get("Id"))
                    episode_results = tv_episode_selection(series_name,title,season_name,parent_id,season_id,index,url,headers)
                    return_results.append(episode_results)
                return return_results
            else:
                result_dict = season_results[0]
                series_name = result_dict.get("series", result_dict.get("SeriesName"))
                season_name = result_dict.get("name", result_dict.get("Name"))
                parent_id = result_dict.get("parent_id", result_dict.get("SeriesId"))
                season_id = result_dict.get("season_id", result_dict.get("Id"))
                episode_results = tv_episode_selection(series_name,title,season_name,parent_id,season_id,index,url,headers)
                return_results.append(episode_results)
                return return_results
        else:
            print(f"❌ Search failed. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def tv_episode_selection(series,title,season,parent_id,season_id,selection,url,headers):
    episode_results = []
    episode_url = f"{url}/Shows/{parent_id}/Episodes"
    params = {
        "seasonId": season_id
    }
    try:
        response = requests.get(episode_url,headers=headers, params=params)
        if response.status_code == 200:
            search_results = response.json()
            items = search_results.get("Items", [])
            if len(items) > 1:
                print(f"\n🔍 Found {len(items)} episodes for '{title} - Season {season}':")
                if selection != 'all':
                    print(f"Select episode to download:\n")
                count = 1
                for item in items:
                    if item != None:
                        name = item.get("Name")
                        id = item.get("Id")
                        file_type = get_media_info(id,url,headers)
                        episode_object = dict(series=series,season=season,episode=count,name=f"{name}",file_type=file_type,id=f"{id}")
                        episode_results.append(episode_object)
                        print(f"{count}) {title} - Season {season} - Episode {count} - {name}")
                        count = count + 1
                if selection == "all":
                    index = "all"
                else:
                    print(f"{count}) All")
                    while True:
                        index = input(f"Enter number for selection: ")
                        if int(index) == count:
                            index = "all"
                            break
                        elif (int(index) - 1) < count:
                            index = (int(index) - 1)
                            break
                        else:
                            print("Invalid selection. Try again")
            else:
                print(f"🔍 Found {len(items)} episodes for '{title} - Season {season}':\n")
                for item in items:
                    if item != None:
                        name = item.get("Name")
                        id = item.get("Id")
                        file_type = get_media_info(id,url,headers)
                        episode_object = dict(series=series,season=season,episode=count,name=f"{name}",file_type=file_type,id=f"{id}")
                        episode_results.append(episode_object)
                index = 0
            if index == "all":
                return episode_results
            else:
                return [episode_results[index]]
        else:
            print(f"❌ Search failed. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def jelllyfin_download(id=None,file_path=None,file_name=None,url=None,headers=None):
    file_info_url = f"{url}/Items/{id}/Download"
    try:
        with requests.get(file_info_url,stream=True,headers=headers) as response:
            if response.status_code == 200:
                path = Path(f"{file_path}/")
                path.mkdir(parents=True, exist_ok=True)
                full_path_name = f"{path}/{file_name}"
                with open(full_path_name, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                return f"✅ {file_name}: downloaded successfully"
            else:
                print(f"❌ {file_name}: Failed to download. Status code: {response.status_code}")
        print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


parser = argparse.ArgumentParser(description="Download media from a jellyfin server")
parser.add_argument('-url', '--url', required=False, default=None, help="Enter Jellyfin hostname")
parser.add_argument('-path', '--path', required=False, default=None, help="Where do you want to save downloads to?")
parser.add_argument('-u', '--username', required=False, default=None, help="Enter Jellyfin username")
parser.add_argument('-t', '--type', required=False, default=None, help="Enter media type: tv, movie, music")
parser.add_argument('-n', '--title', required=False, default=None, type=str, help="Enter title of the media you want to download")
parser.add_argument('-a', '--all', required=False, default=None, action='store_true', help="Download all episodes")
parser.add_argument('-o', '--overwrite', required=False, action=argparse.BooleanOptionalAction, help="Overwrite any existing downloads, Default prompts you")
parser.add_argument('-no', '--no_overwrite', required=False, action=argparse.BooleanOptionalAction, help="Do not overwrite any existing downloads, Default prompts you")
args = parser.parse_args()

if args.overwrite and args.no_overwrite:
    overwrite_media = None
elif args.overwrite:
    overwrite_media = True
elif args.no_overwrite:
    overwrite_media = False
else:
    overwrite_media = None

if args.url == None:
    while True:
        jellyfin_url = input("Enter jellyfin url(https://<hostname/ip>): ") or None
        if jellyfin_url:
            break
        else:
            print("Jellyfin url can't be empty")
else:
    jellyfin_url = args.url

if args.path == None:
    root_destination = input(f"Enter download destination({Path.home()}/Downloads): ") or f"{Path.home()}/Downloads"
else:
    root_destination = args.path

auth = authenticate(jellyfin_url,args.username)
type, search = jellyfin_search(jellyfin_url,auth,args.type,args.title)
title, id, year= jellyfin_search_parse(type,search)

if type == "movie":
    selected_media = movie_selection(title,id,year,jellyfin_url,auth)
    for item in selected_media:
        movie_title = item.get("title")
        movie_name = item.get("name")
        movie_year = item.get("year")
        movie_id = item.get("id")
        file_type = item.get("file_type")
        series = None
        season = None
        file_path = (f"{root_destination}/{movie_title} ({movie_year})").replace(':','')
        file_name = (f"{movie_title} ({movie_year}).{file_type}").replace(':','')
        full_path = f"{file_path}/{file_name}"
        if os.path.exists(full_path):
            print(f"{file_path}/{file_name} - Already exists!")
            if overwrite_media == True:
                overwrite = "y"
            elif overwrite_media == False:
                overwrite = "n"
            else:
                while True:
                    overwrite = (input("Overwrite file? y/(n): ") or "n").lower()
                    if overwrite == 'y' or overwrite == 'n':
                        break
                    else:
                        print("Please type 'y' or 'n'")
            if overwrite == "y":
                print("Overwriting")
                print(f"Download Starting: {file_path}/{file_name}. Please wait...")
                download_status = jelllyfin_download(id,file_path,file_name,jellyfin_url,auth)
                print(download_status)
            elif overwrite == "n":
                print(f"{file_path}/{file_name} - Skipped")
                continue
            else:
                print(f"Invalid selection: {file_path}/{file_name} - Skipped")
        else:
            print()
            print(f"Download Starting: {file_path}/{file_name}. Please wait...")
            download_status = jelllyfin_download(id,file_path,file_name,jellyfin_url,auth)
            print(download_status)

elif type == "tv show":
    download_all = args.all
    selected_media = tv_season_selection(title,id,jellyfin_url,auth,download_all)
    for season in selected_media:
        for item in season:
            series = item.get("series")
            season = int(item.get("season"))
            if season < 10:
                season = f"0{season}"
            episode = item.get("episode")
            if episode < 10:
                episode = f"0{episode}"
            id = item.get("id")
            file_type = item.get("file_type")
            file_path = (f"{root_destination}/{series}/Season {season}").replace(':','')
            file_name = (f"{series} S{season}E{episode}.{file_type}").replace(':','')
            full_path = f"{file_path}/{file_name}"
            if os.path.exists(full_path):
                print(f"{file_path}/{file_name} - Already exists!")
                if overwrite_media == True:
                    overwrite = "y"
                elif overwrite_media == False:
                    overwrite = "n"
                else:
                    while True:
                        overwrite = (input("Overwrite file? y/(n): ") or "n").lower()
                        if overwrite == 'y' or overwrite == 'n':
                            break
                        else:
                            print("Please type 'y' or 'n'")
                if overwrite == "y":
                    print("Overwriting")
                    print(f"Download Starting: {file_path}/{file_name}. Please wait...")
                    download_status = jelllyfin_download(id,file_path,file_name,jellyfin_url,auth)
                    print(download_status)
                elif overwrite == "n":
                    print(f"{file_path}/{file_name} - Skipped")
                    continue
                else:
                    print(f"Invalid selection: {file_path}/{file_name} - Skipped")
            else:
                print()
                print(f"Download Starting: {file_path}/{file_name}. Please wait...")
                download_status = jelllyfin_download(id,file_path,file_name,jellyfin_url,auth)
                print(download_status)
print()
print("Script Complete")