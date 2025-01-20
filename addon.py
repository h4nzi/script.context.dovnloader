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
import re

addon = xbmcaddon.Addon()
folder = addon.getSetting("folder")
if folder == '':
    xbmcgui.Dialog().notification("Video Downloader", "Nastavte složku pro stahování", xbmcgui.NOTIFICATION_ERROR, 4000, sound=False)
    sys.exit(0)

if not folder.endswith(os.sep):
    folder += os.sep

if not xbmcvfs.mkdirs(folder):
    xbmcgui.Dialog().notification("Video Downloader", "Nelze vytvořit cílovou složku", xbmcgui.NOTIFICATION_ERROR, 4000, sound=False)
    sys.exit(1)

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

def sanitize_filename(filename):
    # Odstranění formátovacích značek jako [COLOR ...] a [_COLOR]
    filename = re.sub(r'\[.*?\]', '', filename)
    
    # Odstranění nepovolených znaků (například < > : " / \ | ? *)
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Odstranění extra mezer
    filename = filename.strip()
    return filename

def download(url, custom_filename):
    dialog = xbmcgui.DialogProgress()
    u = urlopen(url)
    meta = u.info()
    file_size = int(meta.get("Content-length", 0))
    filename = sanitize_filename(custom_filename if custom_filename else os.path.basename(urlparse(url).path))
    file_path = folder + filename

    # Debug information
    if addon.getSetting("debug") == "true":
        Msg(f"[Video Downloader] Cílová složka: {folder}")
        Msg(f"[Video Downloader] Celá cesta: {file_path}")

    f = xbmcvfs.File(file_path, 'w')
    dialog.create("Video Downloader", "Stahování...")
    file_size_dl = 0
    block_sz = 4096
    canceled = False
    start = time.time()

    if addon.getSetting("debug") == "true":
        Msg(f"[Webshare Downloader]: {u}")
        Msg(f"[Webshare Downloader] size: {file_size} Bytes")
        Msg(f"[Webshare Downloader] filename: {filename}")

    try:
        while True:
            if dialog.iscanceled():
                canceled = True
                break
            buffer = u.read(block_sz)
            if not buffer:
                break
            file_size_dl += len(buffer)
            f.write(bytearray(buffer))

            status = r"%3.2f%%" % (file_size_dl * 100. / file_size) if file_size > 0 else "??%%"
            done = int(50 * file_size_dl / file_size) if file_size > 0 else 0
            speed = "%s" % round((file_size_dl / (time.time() - start) / 1000000), 1)

            dialog.update(
                int(file_size_dl * 100 / file_size) if file_size > 0 else 0,
                "Velikost:  " + convert_size(file_size) + "\n" +
                "Staženo:  " + status + "     Rychlost: " + speed + " Mb/s\n" +
                "Název: " + filename
            )
    except Exception as e:
        xbmc.log(f"Error during download: {str(e)}", level=xbmc.LOGERROR)
        canceled = True
    finally:
        f.close()

    dialog.close()

    if not canceled:
        yes = xbmcgui.Dialog().yesno('Video Downloader', 'Hotovo. Přehrát video?')
        if yes:
            listitem = xbmcgui.ListItem(path=file_path)
            player = xbmc.Player()
            player.play(file_path, listitem)
    else:
        xbmcvfs.delete(file_path)

def main():
    path = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    custom_label = xbmc.getInfoLabel("Skin.String(ShowCustomLabel)")
    if not custom_label:
        custom_label = xbmc.getInfoLabel("ListItem.Label")
    listitem = xbmcgui.ListItem(path=path)
    player = xbmc.Player()
    player.play(path, listitem)
    time.sleep(5)

    while True:
        if player.isPlaying():
            try:
                url = player.getPlayingFile()
                if url:
                    break
            except Exception as e:
                xbmc.log(f"Error while getting playing file: {str(e)}", level=xbmc.LOGERROR)
        else:
            xbmc.log("Player is not currently playing.", level=xbmc.LOGDEBUG)
        time.sleep(0.1)

    player.stop()
    download(url.split("|")[0], custom_label)

if __name__ == "__main__":
    main()
