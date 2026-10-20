# jellyfin-downloader
Python script for downloading media from your own jellyfin server
Script has been tested against jellyfin 12.x

Currently only works for downloading TV and Movies at the moment

### Features
- partial title search
    - Will also show everything on a server if search is left blank
        - dynamic menu system for selecting the exact media to download
- Lets you download individual movies/episodes, entire seasons or an entire series in one go.
- Sets output files to a standard naming convention(output file names are based on metadata from the jellyfin database not source file names)

### How to use:
1. Install python requirement(s)
2. run the script and follow the prompts

### TODO
- Add support for downloading music files
- Add queue system or option for selecting multiple movies or series before it starts the download (basically you have to run the script again once current selection has downloaded.)
