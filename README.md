## Python script I use to do things with Jellyfin

# Why?

Jellyfin is one of my favourite open-source projects but it has some floors, so I use the API to to get aroung them.

If I knew C# I would just fix them and make a PR.

# Musicbrainz

Currently, it has features to add the MBID to each track in a album (Musicbrainz Track ID).

For this to work each album must have a MBID assigned to it, Jellyfin does this part with the MusicBrainz plugin.
At the same time it will attempt to make sure each track is assigned to the correct disc as I do not want to make any changes to the original media files.

# Shuffle playlist and create a new playlist from it

When you shuffle a playlist in jellyfin, it only adds 299 songs to the Queue and you cannot save Queues either.

The problem with this is that each time you shuffle a large playlist it is very likely that you will have to listen some songs again.

This script can shuffle a wholelist and create a new one from it. 
All you will have to do is remember the one of the last songs you listened to resume where you left off.