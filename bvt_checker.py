#!/usr/bin/python

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
import signal
import os
import time
from gi.repository import GObject as gobject
import urllib2
import json
import gerrit_client
import settings
import sys


def get_last_build():
    req = urllib2.Request(settings.BVT_JOB + '/api/json')
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    s = opener.open(req).read()
    opener.close()
    job_data = json.loads(s)
    build_numbers = [build["number"] for build in job_data["builds"]]
    return max(build_numbers)

def get_latest_job_url():
    last_bvt = get_last_build()
    return '{0}/{1}'.format(settings.BVT_JOB, last_bvt)

def bvt_health():
    test_job_url = get_latest_job_url()
    req = urllib2.Request(test_job_url + '/api/json')
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    s = opener.open(req).read()
    opener.close()
    job_data = json.loads(s)
    return job_data['result']

def is_bvt_ok():
    res = bvt_health()
    if res is None:
        return -1
    if res == 'FAILURE':
        return 0
    return 1


class SystemTray(object):

    def __init__(self):
        self.indicator = appindicator.Indicator.new(
            settings.APPINDICATOR_ID,
            os.path.abspath('green.png'),
            appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu({}))
        self.set_icon()
        gobject.timeout_add_seconds(settings.POLLING_INTERVAL, self.set_icon)
        gtk.main()

    def build_menu(self, active_reviews):
        menu = gtk.Menu()
        for review in active_reviews.keys():
            item_review = gtk.MenuItem(active_reviews[review])
            item_review.connect('activate', self.open_url, review)
            menu.append(item_review)

        item_test = gtk.MenuItem("Open results for '{0}'".format(settings.RELEASE))
        item_test.connect('activate', self.open_url, get_latest_job_url())
        menu.append(item_test)

        item_quit = gtk.MenuItem('Quit')
        item_quit.connect('activate', self.quit)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def quit(self, source):
        gtk.main_quit()
        sys.exit()

    def open_url(self, source, url):
        # Show OpenStack logo while status updating by pooling interval
        self.indicator.set_icon(os.path.abspath('openstack.png'))
        os.system('python -m webbrowser -t "{0}"'.format(url))

    def choose_icon(self, active_reviews):
        bvt_result = is_bvt_ok()
        if bvt_result == -1:
            return 'wait.png'
        elif bvt_result == 0:
            return 'red.png'
        elif active_reviews and bvt_result == 1:
            return 'yellow.png'
        return 'green.png'

    def set_icon(self):
        active_reviews = gerrit_client.get_not_reviewed_patches(
            settings.gerrit_account_name,
            settings.reviews_url,
            settings.SKIP_LOWER_THAN)
        self.indicator.set_menu(self.build_menu(active_reviews))
        icon = self.choose_icon(active_reviews)
        self.indicator.set_icon(os.path.abspath(icon))
        return True

if __name__ == "__main__":
    SystemTray()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    gtk.main()
