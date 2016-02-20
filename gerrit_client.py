import urllib2
import json

url = 'https://review.openstack.org/changes/?q=is:open+owner:asledzinskiy&q=is:open+reviewer:asledzinskiy+-owner:asledzinskiy&q=is:closed+owner:asledzinskiy+limit:5&o=LABELS'

def get_account_id():
    req = urllib2.Request("https://review.openstack.org/accounts/asledzinskiy")
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    s = opener.open(req).read()
    opener.close()
    data = json.loads(s.replace(")]}'", ''))
    return data['_account_id']

def get_not_reviewed_patches():
    req = urllib2.Request(url)
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    s = opener.open(req).read()
    opener.close()
    data = json.loads(s.replace(")]}'", ''))
    review_ids = []
    account_id = get_account_id()
    for review in data[1]:
        for value in review['labels']['Code-Review'].values():
            reviewers_ids = []
            if type(value) == dict:
                if '_account_id' in value:
                    reviewers_ids.append(value['_account_id'])
        if not account_id in reviewers_ids:
            review_ids.append('https://review.openstack.org/#/c/' + str(review['_number']))
    return review_ids

