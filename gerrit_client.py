import urllib2
import json
import threading
import Queue


def get_json_from_url(url):
    try:
        req = urllib2.Request(url)
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        s = opener.open(req).read()
        opener.close()
        return json.loads(s.replace(")]}'", ''))
    except:
        return None


def get_account_id(gerrit_account_name):
    req = urllib2.Request("https://review.openstack.org/accounts/{0}".format(gerrit_account_name))
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    s = opener.open(req).read()
    opener.close()
    data = json.loads(s.replace(")]}'", ''))
    return data['_account_id']


def gerrit_read(review_id, q):
    url = 'https://review.openstack.org/changes/{0}/reviewers'.format(review_id)
    print url
    q.put((review_id, get_json_from_url(url)))


def get_not_reviewed_patches(gerrit_account_name, reviews_url, skip_lower_than=-2):
    data = get_json_from_url(reviews_url)
    active_reviews = {}
    account_id = get_account_id(gerrit_account_name)

    # Start multiple threads to read from Gerrit in parallel
    q = Queue.Queue()
    gerrit_read_threads = []
    for review in data[1]:
        gerrit_read_thread = threading.Thread(target=gerrit_read, args=(review['id'], q))
        gerrit_read_thread.start()
        gerrit_read_threads.append(gerrit_read_thread)

    workers = len(gerrit_read_threads)

    # Wait while all threads are finished
    for gerrit_read_thread in gerrit_read_threads:
        gerrit_read_thread.join()

    gerrit_read_results = {}
    for x in range(workers):
        res = q.get()  # (review_id , code_reviewers)
        gerrit_read_results[res[0]] = res[1]

    # Parse code_reviewers for each review
    for review in data[1]:
        code_reviewers = gerrit_read_results[review['id']]

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
