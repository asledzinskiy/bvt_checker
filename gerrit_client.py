import urllib2
import json


def get_json_from_url(url):
    req = urllib2.Request(url)
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    s = opener.open(req).read()
    opener.close()
    return json.loads(s.replace(")]}'", ''))

def get_account_id(gerrit_account_name):
    req = urllib2.Request("https://review.openstack.org/accounts/{0}".format(gerrit_account_name))
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    s = opener.open(req).read()
    opener.close()
    data = json.loads(s.replace(")]}'", ''))
    return data['_account_id']

def get_not_reviewed_patches(gerrit_account_name, reviews_url, skip_lower_than=-2):
    data = get_json_from_url(reviews_url)
    active_reviews = {}
    account_id = get_account_id(gerrit_account_name)
    for review in data[1]:
        code_reviewers = get_json_from_url('https://review.openstack.org/changes/{0}/reviewers'.format(review['id']))

        # Collect all reviewers who set any value to the review
        reviewers_ids = set()
        lowest_value = '0'
        highest_value = '0'
        for rev in code_reviewers:
            for key in rev['approvals']:
                value = rev['approvals'][key]
                # If there any non-zero value?
                if '-' in value or '+' in value:
                    reviewers_ids.add(rev['_account_id'])
                # Get lowest_value
                if int(value) < int(lowest_value):
                    lowest_value = value
                # Get highest_value
                if int(value) > int(highest_value):
                    highest_value = value

        if int(lowest_value) < int(skip_lower_than):
            continue

        # If there is not any value set from the account_id, then show the review
        if not account_id in reviewers_ids:
            active_review = 'https://review.openstack.org/#/c/' + str(review['_number'])
            active_reviews[active_review] = '{1}[CR:{0}] {2} / {3}'.format(highest_value, review["_number"], review["subject"], review["branch"])
    return active_reviews
