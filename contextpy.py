# License (MIT License)
# 
# Copyright (c) 2007-2008 Christian Schubert and Michael Perscheid
# michael.perscheid@hpi.uni-potsdam.de, http://www.hpi.uni-potsdam.de/swa/
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys, threading, types

__all__ = ['layer']
__all__ += ['activelayer', 'activelayers', 'inactivelayer', 'inactivelayers']
__all__ += ['proceed']
__all__ += ['before', 'after', 'around', 'base']
__all__ += ['globalActivateLayer', 'globalDeactivateLayer']

__version__ = "1.1"

# tuple with layers that are always active
_baselayers = (None,)

class MyTLS(threading.local):
	def __init__(self):
		self.context = None
		self.activelayers = ()

_tls = MyTLS()

class layer(object):
	def __init__(self, name = None):
		self._name = name or hex(id(self))
	
	def __str__(self):
		return "<layer %s>" % (self._name)

	def __repr__(self):
		args = []
		if self._name != hex(id(self)):
			args.append('name="%s"' % self._name)
		return "layer(%s)" % (", ".join(args))
	
	def getEffectiveLayers(self, activelayers):
		return activelayers
	
class _LayerManager(object):
	def __init__(self, layers):
		self._layers = layers
		self._oldLayers = ()
	
	def _getActiveLayers(self):
		return self._oldLayers

	def __enter__(self):
		self._oldLayers = _tls.activelayers
		_tls.activelayers = tuple(self._getActiveLayers())
	
	def __exit__(self, exc_type, exc_value, exc_tb):
		_tls.activelayers = self._oldLayers

class _LayerActivationManager(_LayerManager):
	def _getActiveLayers(self):
		return [layer for layer in self._oldLayers if layer not in self._layers] + self._layers 

class _LayerDeactivationManager(_LayerManager):
	def _getActiveLayers(self):
		return [layer for layer in self._oldLayers if layer not in self._layers]

def activelayer(layer):
	return _LayerActivationManager([layer])

def inactivelayer(layer):
	return _LayerDeactivationManager([layer])

def activelayers(*layers):
	return _LayerActivationManager(list(layers))

def inactivelayers(*layers):
	return _LayerDeactivationManager(list(layers))
	
class _advice(object):
	def __init__(self, func, next):
		if func:
			self._func = func
		else:
			self._func = None
		self._next = next

	def _invoke(self, context, args, kwargs):
		if ((context[0] == None) and (context[1] == None)):
			# Normal Python function no binding needed
			return self._func(*args, **kwargs)
		# Kind of instance method, class or static mehtod (binding needed)
		return self._func.__get__(context[0], context[1])(*args, **kwargs)

	def __call__(self, context, args, kwargs):
		raise NotImplementedError

	@classmethod
	def createchain(cls, methods):
		if not methods:
			return _stop(None, None)
		method, when = methods[0]
		return when(method, cls.createchain(methods[1:]))

class _before(_advice):
	def __call__(self, context, args, kwargs):
		self._invoke(context, args, kwargs)
		return self._next(context, args, kwargs)

class _around(_advice):
	def __call__(self, context, args, kwargs):
		backup = _tls.context
		_tls.context = context
		context[2] = self._next
		result = self._invoke(context, args, kwargs)
		_tls.context = backup
		return result

class _after(_advice):
	def __call__(self, context, args, kwargs):
		result = self._next(context, args, kwargs)
		kwargs_with_result = dict(__result__ = result, **kwargs)
		return self._invoke(context, args, kwargs_with_result)

class _stop(_advice):
	def __call__(self, context, args, kwargs):
		raise Exception, "called proceed() in innermost function, this probably means that you don't have a base method (`around` advice in None layer) or the base method itself calls proceed()"

def proceed(*args, **kwargs):
	context = _tls.context
	return context[2](context, args, kwargs)

def _true(activelayers):
	return True

class _layeredmethodinvocationproxy(object):
	__slots__ = ("_inst", "_cls", "_descriptor")

	def __init__(self, descriptor, inst, cls):
		self._inst = inst
		self._cls = cls
		self._descriptor = descriptor
	
	def __call__(self, *args, **kwargs):
		activelayers = _baselayers + _tls.activelayers
		advice = self._descriptor._cache.get(activelayers) or self._descriptor.cacheMethods(activelayers)

		context = [self._inst, self._cls, None]
		result = advice(context, args, kwargs)
		return result

	def getMethods(self):
		return self._descriptor.methods
	
	def setMethods(self, methods):
		self._descriptor.methods = methods

	def getName(self):
		return self._descriptor.methods[-1][1].__name__

	def registerMethod(self, f, when = _around, layer_ = None, guard = _true):
		self._descriptor.registerMethod(f, when, layer_, guard)

	def unregisterMethod(self, f, layer_ = None):
		self._descriptor.unregisterMethod(f, layer_)

	methods = property(getMethods, setMethods)
	__name__ = property(getName)

class _layeredmethoddescriptor(object):
	def __init__(self, methods):
		self._methods = methods
		self._cache = {}

	def _clearCache(self):
		for key in self._cache.keys():
			self._cache.pop(key, None)

	def cacheMethods(self, activelayers):
		layers = list(activelayers)
		for layer_ in activelayers:
			if layer_ is not None:
				layers = layer_.getEffectiveLayers(layers)
		layers = list(reversed(layers))

		# For each active layer, get all methods and the when advice class related to this layer
		methods = sum([
			list(reversed(
				[(lmwgm[1], lmwgm[2]) for lmwgm in self._methods if lmwgm[0] is currentlayer and lmwgm[3](activelayers)]
			)) for currentlayer in layers], [])

		self._cache[activelayers] =	result = _advice.createchain(methods)
		return result

	def setMethods(self, methods):
		self._methods[:] = methods
		self._clearCache()

	def getMethods(self):
		return list(self._methods)

	def registerMethod(self, f, when = _around, layer_ = None, guard = _true, methodName = ""):
		if (methodName == ""):
			methodName = f.__name__
		if hasattr(when, "when"):
			when = when.when

		assert isinstance(layer_, (layer, types.NoneType))
		assert issubclass(when, _advice)

		self.methods = self.methods + [
			(layer_, f, when, guard, methodName)]

	def unregisterMethod(self, f, layer_ = None):
		self.methods = [lmwgm for lmwgm in self._descriptor.methods if
			lmwgm[1] is not f or lmwgm[0] is not layer_]

	methods = property(getMethods, setMethods)
	
	def __get__(self, inst, cls = None):
		return _layeredmethodinvocationproxy(self, inst, cls)

	# Used only for functions (no binding or invocation proxy needed)
	def __call__(self, *args, **kwargs):
		activelayers = _baselayers + _tls.activelayers
		advice = self._cache.get(activelayers) or self.cacheMethods(activelayers)

		# 2x None to identify: do not bound this function
		context = [None, None, None]
		result = advice(context, args, kwargs)
		return result

def createlayeredmethod(base, partial):
	if base:
		return _layeredmethoddescriptor([(None, base, _around, _true)] + partial)
	else:
		return _layeredmethoddescriptor(partial)

# Needed for a hack to get the name of the class/static method object
class _dummyClass:
	pass

def getMethodName(method):
	if (type(method) in (classmethod, staticmethod)):
		# Bound the method to a dummy class to retrieve the original name
		return method.__get__(None, _dummyClass).__name__
	else:
		return method.__name__	

def __common(layer_, guard, when):
	assert isinstance(layer_, (layer, types.NoneType)), "layer_ argument must be a layer instance or None"
	assert callable(guard), "guard must be callable"
	assert issubclass(when, _advice)

	vars = sys._getframe(2).f_locals

	def decorator(method):
		methodName = getMethodName(method)
		currentMethod = vars.get(methodName)
		if (issubclass(type(currentMethod), _layeredmethoddescriptor)):
			#Append the new method
			currentMethod.registerMethod(method, when, layer_, guard, methodName)
		else:
			currentMethod = createlayeredmethod(currentMethod, [(layer_, method, when, guard, methodName)])
		return currentMethod

	return decorator

def before(layer_ = None, guard = _true):
	return __common(layer_, guard, _before)
def around(layer_ = None, guard = _true):
	return __common(layer_, guard, _around)
def after(layer_ = None, guard = _true):
	return __common(layer_, guard, _after)

def base(method):
	# look for the current entry in the __dict__ (class or module)
	vars = sys._getframe(1).f_locals
	methodName = getMethodName(method)
	currentMethod = vars.get(methodName)
	if (issubclass(type(currentMethod), _layeredmethoddescriptor)):
		# add the first entry of the layered method with the base entry
		currentMethod.methods = [(None, method, _around, _true)] + currentMethod.methods  
		return currentMethod
	return method

before.when = _before
around.when = _around
after.when = _after

def globalActivateLayer(layer):
	global _baselayers
	if layer in _baselayers:
		raise ValueError("layer is already active")
	_baselayers += (layer,)
	return _baselayers

def globalDeactivateLayer(layer):
	global _baselayers
	t = list(_baselayers)
	if layer not in t:
		raise ValueError("layer is not active")
	i = t.index(layer)
	_baselayers = tuple(t[:i] + t[i+1:])
	return _baselayers
