#! /bin/sh

gae_root='/usr/local/google_appengine'

PYTHONPATH=$gae_root
PYTHONPATH=$PYTHONPATH:$gae_root/lib/antlr3
PYTHONPATH=$PYTHONPATH:$gae_root/lib/cacerts
PYTHONPATH=$PYTHONPATH:$gae_root/lib/ipaddr
#PYTHONPATH=$PYTHONPATH:$gae_root/lib/webob
#PYTHONPATH=$PYTHONPATH:$gae_root/lib/webob_0_9
PYTHONPATH=$PYTHONPATH:$gae_root/lib/webob_1_1_1
PYTHONPATH=$PYTHONPATH:$gae_root/lib/yaml/lib
PYTHONPATH=$PYTHONPATH:$gae_root/lib/django_1_3
export PYTHONPATH

echo 'Set Google appengine to PYTHONPATH.'
