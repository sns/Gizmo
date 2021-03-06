import time


GIZMO_MODEL = '__gizmo_model'
GIZMO_CREATED = '__gizmo_created'
GIZMO_MODIFIED = '__gizmo_modified'
GIZMO_NODE_TYPE = '__gizmo_node_type'
GIZMO_TYPE = '_type'
GIZMO_ID = '_id'
GIZMO_LABEL = '_label'
VERTEX = 'vertex'
EDGE = 'edge'
TYPES = {VERTEX: VERTEX, EDGE: EDGE}
IMMUTABLE = {VERTEX: [GIZMO_ID, GIZMO_TYPE], EDGE: [GIZMO_ID, GIZMO_TYPE, GIZMO_LABEL, '_inV', '_outV']}


def get_object_items(obj):
    return [a for a in dir(obj) if not a.startswith('__') and not callable(getattr(obj, a))]


def get_qualified_name(obj):
    return '%s.%s' % (obj.__module__, obj.__name__)


def get_qualified_instance_name(obj):
    return '%s.%s' % (obj.__class__.__module__, obj.__class__.__name__)

def current_date():
    pass

def current_time():
    pass

def current_date_time(offset=0):
    return (int(time.time()) + offset) * 1000

def get_logger(address='/var/run/syslog'):
    import logging
    from logging.handlers import SysLogHandler
    
    logger = logging.getLogger('gizmo_logger')
    handler = SysLogHandler(address=address)
    
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    return logger
