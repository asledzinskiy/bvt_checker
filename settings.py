gerrit_account_name = 'asledzinskiy'
reviews_url = 'https://review.openstack.org/changes/?q=is:open+owner:{0}&q=is:open+reviewer:{0}+-owner:{0}&q=is:closed+owner:{0}+limit:5&o=LABELS'.format(gerrit_account_name)
APPINDICATOR_ID = 'myappindicator'
RELEASE = '8.0'
BVT_JOB = 'https://product-ci.infra.mirantis.net/job/{}.test_all/api/json'.format(RELEASE)
BVT_TEST_JOB = 'https://product-ci.infra.mirantis.net/job/{0}.test_all/{1}/api/json'
