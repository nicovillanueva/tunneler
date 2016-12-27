import yaml
import sys
import os

conf = sys.argv[1]

with open(conf) as f:
    config = yaml.load(f)

h1 = config.get('hops')[0]
hn = [e for e in h1][0]
h1 = h1.get(hn)
if h1.get('auth') is not None:
    k = h1.get('auth').get('key')
    if k is not None:
        if '~' in k:
            outer = k.replace('~', os.path.expanduser('~'))
            inner = k.replace('~', '/root')
        else:
            inner = k
            outer = k
        print('-v "{}":"{}"'.format(outer, inner))
    else:
        # No key, no mount
        print()
