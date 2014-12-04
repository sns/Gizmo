from utils import gizmo_import, get_qualified_name, IMMUTABLE, GIZMO_MODEL
from element import Edge, Vertex, General, _MAP
from gremlinpy.gremlin import Gremlin, Function


_MAPPER_MAP = {}
GENERIC_MAPPER = 'generic.mapper'


class _RootMapper(type):
    def __new__(cls, name, bases, attrs):
        cls = super(_RootMapper, cls).__new__(cls, name, bases, attrs)
        
        model = attrs.pop('model', None)
        
        if model:
            map_name = '%s.%s' % (model.__module__, model.__name__)
            _MAPPER_MAP[map_name] = cls
        elif name == '_GenericMapper':
            _MAPPER_MAP[GENERIC_MAPPER] = cls
        
        return cls
        
class _GenericMapper(object):
    __metaclass__ = _RootMapper
    
    def __init__(self, gremlin=None):
        self.gremlin = gremlin
        self.queries = []
        self.models  = {}
        self.params  = {}

    def enqueue(self, query, bind_return=True):
        for entry in query.queries:
            self.count += 1
            script = entry['script']
            
            if bind_return:
                variable = '%s_%s' % (self.VARIABLE, self.count)
                script   = '%s = %s' % (variable, script)
                
                if 'model' in entry:
                    self.models[variable] = entry['model']
            
            self.queries.append(script)
            self.params.update(entry['params'])
        
        return self
        
    def save(self, model, bind_return=True, lookup=True):
        query = Query(self.gremlin)
        query.save(model)
        
        return self.enqueue(query, bind_return)
    
    def delete(self, model, lookup=True):
        query = Query(self.gremlin)
        
        query.delete(model)
        
        return self.enqueue(query, False)
        
    def create_model(self, data=None, model_class=None):
        """
        Method used to create a new model based on the data that is passed in.
        If the kwagrg model_class is passed in, it will be used to create the model
        else if pygwai.element.PYGWAI_MODEL is in data, that will be used
        finally, pygwai.model.element.General will be used to construct the model
        
        """
        check = True
        
        if data is None:
            data = {}

        if model_class is not None:
            try:
                model = model_class(data)
                check = False
            except Exception as e:
                pass

        if check:
            try:
                if GIZMO_MODEL in data:
                    name  = data[GIZMO_MODEL]
                    model = _MAP[name](data)
                else:
                    raise
            except Exception as e:
                model = General(data)

        return model

class Mapper(object):
    __metaclass__ = _RootMapper
    
    VARIABLE = 'gizmo_var'
    registrations = {}
    
    def __init__(self, request, gremlin=None, auto_commit=False):
        if gremlin is None:
            gremlin = Gremlin()

        self.count = -1
        self.request = request
        self.gremlin = gremlin
        self.auto_commit = auto_commit
        self.reset()
        
    def reset(self):
        self.queries = []
        self.models  = {}
        self.params  = {}
        
    def _get_mapper(self, model=None, name=GENERIC_MAPPER):
        if model is not None:
            name = get_qualified_name(model)

        if name not in _MAPPER_MAP:
            name = GENERIC_MAPPER
            
        return _MAPPER_MAP[name](self.gremlin)
        
    def _enqueue_mapper(self, mapper):
        self.queries = mapper.queries
        self.models.update(mapper.models)
        self.params.update(mapper.params)
        
        return self
        
    def enqueue(self, query, bind_return=True):
        for entry in query.queries:
            self.count += 1
            script = entry['script']
            
            if bind_return:
                variable = '%s_%s' % (self.VARIABLE, self.count)
                script   = '%s = %s' % (variable, script)
                
                if 'model' in entry:
                    self.models[variable] = entry['model']
            
            self.queries.append(script)
            self.params.update(entry['params'])
        
        return self
    
    def _save(self, model, bind_return=True):
        mapper = self._get_mapper(model)
        
        mapper.save(model, bind_return)
        
        return self._enqueue_mapper(mapper)
    
    def save(self, model, bind_return=True, lookup=True):
        query = Query(self.gremlin)
        query.save(model)
        
        return self.enqueue(query, bind_return)
    
    def _delete(self, model):
        mapper = self._get_mapper(model)
        
        mapper.delete(model)
        
        return self.enqueue(mapper)
    
    def delete(self, model, lookup=True):
        query = Query(self.gremlin)
        
        query.delete(model)
        
        return self.enqueue(query, False)

    def create_model(self, data=None, model_class=None):
        if data is None:
            data = {}
        
        if model_class:
            mapper = self._get_mapper(model_class)
        else:
            name   = data.get(GIZMO_MODEL, GENERIC_MAPPER)
            mapper = self._get_mapper(name=name)

        args = (data,)
        
        if type(mapper) == _GenericMapper:
            args = args + (model_class,)
        
        return mapper.create_model(*args)

    def _create_model(self, data=None, model_class=None):
        """
        Method used to create a new model based on the data that is passed in.
        If the kwagrg model_class is passed in, it will be used to create the model
        else if pygwai.element.PYGWAI_MODEL is in data, that will be used
        finally, pygwai.model.element.General will be used to construct the model
        
        """
        check = True
        
        if data is None:
            data = {}

        if model_class is not None:
            name = get_qualified_name(model_class)
            
            if name in _MAPPER_MAP:
                try:
                    mapper = _MAPPER_MAP[name](self.request, self.gremlin)
                    model = mapper._create_model(data)
                    check = False
                except Exception, e:
                    pass
            
            if check:
                try:
                    model = model_class(data)
                    check = False
                except Exception as e:
                    pass

        if check:
            try:
                if GIZMO_MODEL in data:
                    name  = data[GIZMO_MODEL]
                    model = _MAP[name](data)
                else:
                    raise
            except Exception as e:
                model = General(data)

        return model
        
    def _build_queries(self):
        if self.auto_commit is False:
            commit = '.'.join([self.gremlin.gv, 'commit()'])
            
            self.queries.append(commit)
            
        if len(self.models) > 0:
            returns = []
            
            for k in self.models.keys():
                returns.append("'%s': %s" % (k ,k))

            ret = '[%s]' % ','.join(returns)
            
            self.queries.append(ret)
        
        return self
        
    def start(self, model):
        return Traversal(mapper, model)
        
    def apply_statement(self, statement):
        self.gremlin.apply_statement(statement)
        
        return self
        
    def send(self, script=None, params=None, gremlin=None):
        if gremlin is not None:
            script = str(gremlin)
            params = gremlin.bound_params
        elif script is None:
            self._build_queries()
            
            script = ";\n".join(self.queries)
            params = self.params

        if script is None:
            script = ''
            
        if params is None:
            params = {}

        response = self.request.send(script, params)
        
        if len(self.models) > 0:
            response.update_models(self.models)
        
        return Collection(self, response)



class Query(object):
    QUERY_VAR = 'query_var'
    
    def __init__(self, gremlin):
        self.gremlin = gremlin
        self.fields  = []
        self.queries = []
        self.count   = -1
        
    def reset(self):
        self.fields = []

        self.gremlin.reset()
        
        return self
        
    def next_var(self):
        self.count += 1
        
        return '%s_%s' % (self.QUERY_VAR, self.count)
        
    def add_query(self, script, params=None, model=None):
        if params is None:
            params = {}
            
        self.queries.append({
            'script': script,
            'params': params,
            'model': model
        })
        
        return self
        
    def add_gremlin_query(self, model=None):
        script = str(self.gremlin)
        params = self.gremlin.bound_params
        
        self.add_query(script, params, model)
        
        return self.reset()
        
    def build_fields(self, data, immutable):
        gremlin = self.gremlin
        
        for key, val in data.iteritems():
            if key not in immutable:
                value = val
                if type(val) is dict or type(val) is list:
                    listed = self.iterable_to_map(val)
                    value  = "[%s]" % listed
                    
                    self.fields.append(value)
                else:
                    bound = gremlin.bind_param(value)

                    self.fields.append("'%s': %s" % (key, bound[0]))
        
        return self
        
    def update_fields(self, data, immutable):
        gremlin = self.gremlin
        
        for k, v in data.iteritems():
            if k not in immutable:
                if type(v) is dict or type(v) is list:
                    gmap  = self.iterable_to_map(v)
                    entry = "it.setProperty('%s', %s)" % (k, gmap)
                else:
                    bound = self.gremlin.bind_param(v)
                    entry = "it.setProperty('%s', %s)" % (k, bound[0])
                    
                self.fields.append(entry)
                
        return self
        
    def iterable_to_map(self, iterable):
        gremlin = self.gremlin
        gmap = []
        
        for k, v in enumerate(iterable):
            if type(v) is dict or type(v) is list:
                gmap.append(self.iterable_to_map(v))
            else:
                bound = gremlin.bind_param(v)
                entry = "'%s': %s" % (k, bound[0])
                
                gmap.append(entry)
        
        return ','.join(gmap)
        
    def add_vertex(self, model, set_variable=False):
        if model._type is None:
            raise Exception('Models need to have a type defined')
        
        model.fields.data_type = 'graph'
        gremlin = self.gremlin
        
        if set_variable:
            gremlin.set_ret_variable(set_variable)
        
        self.build_fields(model.data, IMMUTABLE['vertex'])
        
        script = '%s.addVertex([%s])' % (gremlin.gv, ', '.join(self.fields))

        gremlin.set_graph_variable('').raw(script)
        
        return self.add_gremlin_query(model)
        
    def add_edge(self, model, set_variable=False):
        if model['_label'] is None:
            raise Exception('The edge must have a label before saving')
        
        model.fields.data_type = 'graph'
        gremlin     = self.gremlin
        out_v, in_v = self._get_or_create_edge_vertices(model)
        label_bound = gremlin.bind_param(model['_label'])
        edge_fields = ''
        
        if set_variable:
            gremlin.set_ret_variable(set_variable)
        
        self.build_fields(model.data, IMMUTABLE['edge'])
        
        if len(self.fields) > 0:
            edge_fields = ', [%s]' % ', '.join(self.fields)

        script = '%s.addEdge(%s, %s, %s%s)' % (gremlin.gv, out_v, in_v, label_bound[0], edge_fields)
        
        gremlin.set_graph_variable('').raw(script)
        
        return self.add_gremlin_query(model)

    def _get_or_create_edge_vertices(self, edge):
        out_v     = edge.out_v
        out_v_ref = self.next_var()
        in_v      = edge.in_v
        in_v_ref  = self.next_var()
        
        if out_v is None or in_v is None:
            error = 'Both out and in vertices must be set before saving \
                the edge'
                
            raise Exception(error)
        
        self.save(out_v, out_v_ref)
        self.save(in_v, in_v_ref)
        
        return out_v_ref, in_v_ref
    
    def update(self, model, set_variable=False):
        if model._type is None:
            raise Exception()
            
        if model['_id'] is None:
            raise Exception()
            
        gremlin = self.gremlin
        model.fields.data_type = 'graph'
        model_type = 'e' if model._type == 'edge' else 'v'
        
        if set_variable:
            gremlin.set_ret_variable(set_variable)
            
        self.update_fields(model.data, model._immutable)

        next_func = Function(gremlin, 'next')
        
        getattr(gremlin, model_type)(model['_id'])._().sideEffect.close('; '.join(self.fields)).add_token(next_func)

        model.fields.data_type = 'python'
        
        return self.add_gremlin_query(model)

    def save(self, model, set_variable=False):
        if model._type is None:
            raise Exception('The model does not have a _type defined')
        
        id        = model['_id']
        immutable = model._immutable

        if id is None:
            if model._type == 'vertex':
                self.add_vertex(model, set_variable)
            else:
                self.add_edge(model, set_variable)
        else:
            self.update(model, set_variable)
            
        return self

    def delete(self, model):
        gremlin = self.gremlin

        id = model['_id']
        
        if id is None:
            raise Exception('Models must have an _id before they are deleted')
            
        if model._type is None:
            raise Exception('Models need to have a type defined')
        
        element = 'e' if model._type == 'edge' else 'v'

        getattr(gremlin, element)(id).remove()
        
        return self.add_query(str(gremlin), gremlin.bound_params, model)


class Traversal(Gremlin):
    """
    class used to start a traversal query based on a given model
    
    example:
        
    """
    
    def __init__(self, mapper, model, graph_variable='G'):
        super(Traversal, self).__init__(graph_variable)
        self._mapper = mapper
        self._model = model


class Collection(object):
    def __init__(self, mapper, response):
        self.mapper = mapper
        self.response = response
        self._models = {}
        self._index = 0
    
    def __getitem__(self, key):
        model = self._models.get(key, None)
        
        if model is None:
            try:
                data = self.response[key]
                
                if data is not None:
                    model = self.mapper.create_model(data=data)
                    self._models[key] = model
                else:
                    raise
            except:
                raise StopIteration()
        
        return model
    
    def __setitem__(self, key, value):
        self._models[key] = value
    
    def __delitem__(self, key):
        if key in self._models:
            del self._models[key]
