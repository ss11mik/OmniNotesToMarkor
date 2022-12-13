# Converter for notes from Omni Notes format to file structure compatible with Markor
# takes SQLite DB named "omni-notes" in current directory
# and creates the files structure in folder "output/"
# and a zipfile "output.zip" containing the folder
#
# the files have a .md suffix, title and a creation and last modification time
# archived files are marked as hidden (filename starts with dot)
#   and moved to ".archive" subfolder
# trashed files are in ".trash" subfolder
#   if a note is both archived and trashed, it goes to ".trash" as hidden file
# notes without name are saved to a file named with its creation time
# name duplicity is solved by suffixing the latter with an underscore
# attachments are not handled
#
# ss11mik
# 08/12/2022

import sqlite3
import pathlib
import os
import shutil
from datetime import datetime
from zipfile import ZipFile


connection = sqlite3.connect('omni-notes')
cursor = connection.cursor()

# clear the direcotry
try:
    shutil.rmtree("output/")
except FileNotFoundError:
    pass
pathlib.Path("output/").mkdir(exist_ok=True)
pathlib.Path("output/.trash").mkdir(exist_ok=True)
pathlib.Path("output/.archive").mkdir(exist_ok=True)


# create folders for categories

cursor.execute("SELECT name FROM categories")
categories = cursor.fetchall()

for category in categories:
    catName = category[0]
    pathlib.Path("output/" + catName).mkdir(exist_ok=True)
    pathlib.Path("output/" + catName + "/.trash").mkdir(exist_ok=True)
    pathlib.Path("output/" + catName + "/.archive").mkdir(exist_ok=True)


# write the notes to files
cursor.execute("SELECT creation, title, content, archived, trashed, categories.name, last_modification FROM notes LEFT JOIN categories ON notes.category_id = categories.category_id")
notes = cursor.fetchall()

for note in notes:
    # print(note)

    creationTime = datetime.utcfromtimestamp(note[0] // 1000)
    creationTimePretty = creationTime.strftime('%Y/%m/%d %A %H:%M:%S')
    creationTime = creationTime.strftime('%Y-%m-%d_%H-%M-%S')

    lastMod = datetime.utcfromtimestamp(note[6] // 1000).strftime('%Y/%m/%d %A %H:%M:%S')

    noteName = note[1]
    fileName = noteName
    path = ""
    # sanitize possible slashes and backslashes in note title
    fileName = fileName.replace("/", "_").replace("\\", "_")
    if fileName == "":
        # if note has no name, fallback to creation time (which is primary key in Omni Notes)
        fileName = creationTime

    # archived notes
    if note[3] == 1:
        fileName = "." + fileName
        path = ".archive/"

    # trashed notes
    if note[4] == 1:
        path = ".trash/"

    # category of the note
    catName = note[5]
    if catName is not None:
        path = catName + "/" + path


    # fix for notes with duplicate name in the same category
    while os.path.exists(f"output/{path}{fileName}.md"):
        fileName = fileName + "_"

    with open(f"output/{path}{fileName}.md", "w") as outFile:
        if noteName != "":
            outFile.write(f"# {noteName}\n\n")
        outFile.writelines(note[2])

        outFile.write(f"\n\n\nCreated: {creationTimePretty}\n")
        outFile.write(f"Last modification in Omni Notes: {lastMod}")

# zip the folder
shutil.make_archive("output", "zip", "output")
