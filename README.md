Gizmo
=====

Gizmo is a lightweight Python Object Graph Mapper (O.G.M.) for [Tinkerpop Blueprints' Rexster](http://www.tinkerpop.com) servers. 

##Table of Contents:


### About

Gizmo starts and ends with Rexster. It is made up of model, mapper, query, request, response, and other object whose jobe is to convert pure Python to a Rexster string to be executed on a server.

### Gremlin

Gremlin is the basis of all interactions between Gizmo and the Rexster server. Gizmo employs [Gremlinpy](https://github.com/emehrkay/gremlinpy) under the hood to aid with translating objects to scripts. 

If you're new to Gremlin there are a few good resources to check out that will help you get the concept and allow you to hit the ground running with this library.

* [Tinkerpop Gremlin](https://github.com/tinkerpop/gremlin/wiki) -- Tinkerpop's Gremlin documenation.
* [SQL2Gremlin](http://sql2gremlin.com) -- A site dedicated to explaing how you can convert some simple SQL into Gremlin/Groovy scripts.
* [GremlinDocs](http://gremlindocs.com) -- A site that goes over the core functions that you will use in your scripts.
* [Tinkerpop mailing list](https://groups.google.com/forum/#!forum/gremlin-users) -- These guys/gals are cool. 

After getting a grasp of the Gremlin/Groovy language, you can now begin to write script via [GremlinPy](https://github.com/emehrkay/gremlinpy) and take full advantage of what Gizmo can do.

### Dependencies

* [GremlinPy](https://github.com/emehrkay/gremlinpy) >= 0.2
* [Requests](http://docs.python-requests.org/en/latest/) -- If you're connecting via HTTP.
* [Rexpro](https://pypi.python.org/pypi/rexpro/) -- If you're connecting via the binary interface.

### Installation

    easy_install gizmo

or 

    pip install gizmo

or

    python setup.py install


### Quickstart

    from gizmo.entity import Vertex
    from gizmo.mapper import Mapper, GenericEdge
    from gizmo.request import Binary
    
    r = BinaryRequest('localhost', 8984, 'gizmo_test')
    g = Gremlin()
    m = Mapper(r, g)
    
    class User(Vertex):
        def __init__(self, data=None):
            self.allow_undefined = True
            super(User, self).__init__(data)
            
        @property
        def _node_type(self):
        	return 'user'
        	
    u = User({'name': 'mark', 'sex': 'male'})
    g = User({'name': 'sadé', 'sex': 'female'})
    d = {'out_v': u, 'in_v': g, 'since': 'last year'}
    e = GenericEdge(d, 'girl')
    
    m.save(e) #this will CRUD all entites
    m.send() #builds query and sends to the server
    
    #the entities have been updated with the response from the server
    print u['_id'], e.data

### Entities

A [graph](http://en.wikipedia.org/wiki/Graph_(mathematics)) is defined as a representation of a set of objects where some pairs of objects are connected by links. The objects are commonly refered to as nodes or vertices and edges. Vertices are your objects and edges are the connections. 

Gizmo's entity module contians definitions for `Vertex` and `Edge` objects. You will extend these to create custom model definitions or you can use the `GenericVertex` for vertices and `GenericEdge` for edges.

#### Models

Gizmo allows you to interact with the graph server by either sending a string to the server, sending a Gremlinpy object, or by invoking models. Using the entity `Vertex` and `Edge` objects for your models will give you more power, flexibility, and control when writing your applications.

Gizmo reuires that you define a `node_type` property with each model. This should be a uniue string amoung your models as it will allow you to easily query for that model at a later date. 

    class Article(Vertex):
        def __init__(self, data):
            super(Article, self).__init__(data)
            
            self.fields.update({
            	'title': String(),
            	'content': String()
            })
            
            self.hydrate(data)
            
        @property
        def _node_type(self):
            return 'custom_article'

You can define an `Edge` in the same way. Most graph databaes allow for both vertices and edges to have data stored on them and you ca
    
##### Fields

Gizmo entities comes with a few predefined fields that will help you structure and query your data once it is saved in your database. By default the fields member defines how your model's data is structured. 

If you want your model to have unstructured data, set the instance member `allow_undefined` to `True` in the `__init__` method before you call super. When this memeber is set to true and an undefined field is set, Gizmo will do its best to figure out what field type to use.

**Field Types**

Gizmo ships whith a few self-describing types for fields. The field object main job is to convert the data from a Python type to a Groovy type (if necessary).

* String
* Integer
* Float
* Boolean
* Map -- converts a Python dict to Grooy map. {'key': 'val'} -> ['key': 'val']
* List -- converts a Python tuple or list to Groovy list. (1, 2, '3') -> [1, 2, '3']
* DateTime
* Enum -- this simply takes a pre-defined list and only allows its members to be used.

These are fields created and populated at class instantiation:

* GIZMO_MODEL _:String_ -- the model that is used for the entity
* GIZMO_CREATED _:DateTime_ -- the original date created. This cannot be overwritten
* GIZMO_MODIFIED _:DateTime_ -- this is updated with every save
* GIZMO_NODE_TYPE _:String_ -- the \_node_type property
* GIZMO_ID _:String_ -- the _id from the graph. It is a string because different graphs store ids differently. OrientDB's ids have a : in them
* GIZMO_LABEL _:String_ -- all edges have a _label member. This defines how the vertices are connected


#### Edges

### Mappers

#### Custom Mappers

#### Queries and Statements

#### Traversal Object

The `mapper.Traversal` object allows you to build a query with a given `Vertex` or `Edge` as the starting point. Its main purpose is to bind the `Gremlin` instance with the `Mapper` and the given Entity.

### Future releases

I wasn't able to fit all of the features that I see will make this library useful in this initial relase.
