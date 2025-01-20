# -*- coding: utf-8 -*-
import os
import xbmc
import xbmcaddon
import xbmcgui
import sys
import time
import xbmcvfs
from urllib.request import urlopen
from urllib.parse import urlparse


addon = xbmcaddon.Addon()
folder = addon.getSetting("folder")
if folder == '':
    xbmcgui.Dialog().notification("Video Downloader","Nastavte složku pro stahování", xbmcgui.NOTIFICATION_ERROR, 4000, sound = False)
    sys.exit(0)

def Msg(message):
    xbmc.log(message, level=xbmc.LOGINFO)

def convert_size(number_of_bytes):
    if number_of_bytes < 0:
        raise ValueError("!!! number_of_bytes can't be smaller than 0 !!!")
    step_to_greater_unit = 1024.
    number_of_bytes = float(number_of_bytes)
    unit = 'bytes'
    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'KB'
    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'MB'
    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'GB'
    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'TB'
    precision = 1
    number_of_bytes = round(number_of_bytes, precision)
    return str(number_of_bytes) + ' ' + unit


def download(url):
    dialog = xbmcgui.DialogProgress()
    u = urlopen(url)
    meta = u.info()
    file_size = int(meta.get("Content-length"))
    filename = os.path.basename(urlparse(url).path)
    f = xbmcvfs.File(folder + filename, 'w')
    dialog.create("Video Downloader","Stahování...")
    file_size_dl = 0
    block_sz = 4096
    canceled = False
    start = time.time()
    if addon.getSetting("debug") == "true":
        Msg(f"[Webshare Downloader]: {u}")
        Msg(f"[Webshare Downloader size: {file_size}")
        Msg(f"[Webshare Downloader filename: {filename}")
    while True:
        if dialog.iscanceled():
            canceled = True
            break
        buffer = u.read(block_sz)
        if not buffer: break
        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%3.2f%%" % (file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        done = int(50 * file_size_dl / file_size)
        speed = "%s" % round((file_size_dl//(time.time() - start) / 100000), 1)
        dialog.update(int(file_size_dl*100 /file_size), "Velikost:  " + convert_size(file_size) + "\n" + "Staženo:  " + status + "     Rychlost: " + speed + " Mb/s\n" + filename)
    f.close()
    dialog.close()
    if canceled == False:
        yes = xbmcgui.Dialog().yesno('Video Downloader', 'Hotovo. Přehrát video?')
        if yes:
            path = folder + filename
            listitem = xbmcgui.ListItem(path=path)
            player = xbmc.Player()
            player.play(path, listitem)
    else:
        xbmcvfs.delete(folder + filename)


def main():
    path = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    listitem = xbmcgui.ListItem(path=path)
    player = xbmc.Player()
    player.play(path, listitem)
    time.sleep(5)
    while True:
        try:
            url = player.getPlayingFile()
            if url:
                break
        except:
            pass
    player.stop()
    download(url.split("|")[0])


if (__name__ == "__main__"):
    main()
