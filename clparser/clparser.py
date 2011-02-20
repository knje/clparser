#!/usr/bin/env python3.1
'''
Created on Sep 21, 2010

@author: kannan.jeyakumar
'''

import datetime
import logging
import urllib.parse
import lxml.html
import re

def ParseListingText(text, get_jsonable=False):
    doc = lxml.html.document_fromstring(text)
    
    apt_info = {}
    # price from heading
    sel = doc.cssselect("h2")
    for item in sel:
        logging.log(logging.DEBUG, item.text_content())
        matched =  re.match("\$[0-9]*", item.text_content())
        amount = -1
        if matched:
            amount = matched.group(0).replace("$", "")
            apt_info["price"] = int(amount) 
    
    # address from map url
    sel = doc.cssselect("small a:nth-child(1)")
    for item in sel:
        logging.log(logging.DEBUG, item.text_content())
        map_url = item.get("href").replace("http://maps.google.com/?q=loc", "")
        logging.log(logging.DEBUG, map_url)
        address = urllib.parse.unquote(map_url).replace(":+", "").replace("+", " ")
        apt_info["address"] = address
    
    # mail url (to get craigslist url)
    sel = doc.cssselect("a:nth-child(8)")
    url = None
    for item in filter(lambda x: "mailto" in x.get("href"), sel):
        logging.log(logging.DEBUG, item.text_content())
        mail_url         = item.get("href")
        logging.log(logging.DEBUG, mail_url)
        decoded_mail_url = urllib.parse.unquote(mail_url)
        matched          =  re.search("http(.)*craigslist(.)*", decoded_mail_url)
        if matched:
            url = matched.group(0)
        apt_info["url"] = url
        
    sel = doc.cssselect(".bchead")
    for item in sel:
        for child in item.getchildren():
            if child.text_content() == "apts/housing for rent":
                url_head = child.get("href")
                pid_match = re.search("pID = (?P<id>[0-9]*);", text)
                if pid_match:
                    post_id = pid_match.group("id")
                    url2 = "%s%s.html" % (url_head, post_id)
                    apt_info["url"] = url2
        
    #cats and dogs
    apt_info["cats"] = False
    # look for <!-- CLTAG catsAreOK=on -->
    cat_match = re.search("<!--(\s)*CLTAG(\s)*catsAreOK(\s)*=(\s)*on(\s)*-->", text)
    if cat_match:
        apt_info["cats"] = True
    apt_info["dogs"] = False
    #look for <!-- CLTAG dogsAreOK=on -->
    dog_match = re.search("<!--(\s)*CLTAG(\s)*dogsAreOK(\s)*=(\s)*on(\s)*-->", text)
    if dog_match:
        apt_info["dogs"] = True
    

    # crazy long regex to match
    # Date: 2010-11-04, 10:26AM PDT
    date_match = re.search( "Date: (?P<year>([0-9]){4})-(?P<month>([0-9]){2})-(?P<day>([0-9]){2}),(\s)*(?P<hour>([0-9]){1,2}):(?P<min>([0-9]){2})(A|P)?M(\s)*[a-zA-Z]{0,3}", 
                            doc.text_content())
    if date_match:
        year   = int(date_match.group("year"))
        month  = int(date_match.group("month"))
        day    = int(date_match.group("day"))
        hour   = int(date_match.group("hour"))
        min    = int(date_match.group("min"))
        # ex: 8:30 AM = 8:30, 12:15 PM = 12:15, 5:50PM = 17:50
        if "PM" in date_match.group() and hour<12:
            hour = hour+12
        date = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=min)
        # convert time to utc (only has US time zones)
        if "PDT" in date_match.group() or "MST" in date_match.group():
            date = date + datetime.timedelta(hours=7)
        elif "MDT" in date_match.group() or "CST" in date_match.group():
            date = date + datetime.timedelta(hours=6)
        elif "EST" in date_match.group() or "CDT" in date_match.group():
            date = date + datetime.timedelta(hours=5)
        elif "EDT" in date_match.group():
            date = date + datetime.timedelta(hours=4)
        elif "PST" in date_match.group():
            date = date + datetime.timedelta(hours=8)
        if get_jsonable:
            apt_info["posted_on"] = date.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            apt_info["posted_on"] = date
    
    logging.log(logging.DEBUG, apt_info)
    return apt_info
        

