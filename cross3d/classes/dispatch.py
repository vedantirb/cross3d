##
#	\namespace	blur3d.api.dispatch
#
#	\remarks	Handles conversion of signals between the host software and blur3d
#				TODO: Only enable or disable signals that have a connection to them
#				TODO: Only emit a single ScenePreInvalidated/SceneInvalidated signal on file operations, using a reffrence counter
#	
#	\author		Mikeh@blur.com
#	\author		Blur Studio
#	\date		06/06/11
#

from PyQt4.QtCore import pyqtSignal, QObject
from blurdev import debug

class Dispatch(QObject):
	# scene signals
	sceneClosed				= pyqtSignal()
	sceneExportRequested	= pyqtSignal()
	sceneExportFinished		= pyqtSignal()
	sceneImportRequested	= pyqtSignal()
	sceneImportFinished		= pyqtSignal()
	scenePreInvalidated		= pyqtSignal()			# linked signal before a import, open, or merge operation
	sceneInvalidated		= pyqtSignal()
	sceneMergeRequested		= pyqtSignal()
	sceneMergeFinished		= pyqtSignal()
	sceneNewRequested		= pyqtSignal()
	sceneNewFinished		= pyqtSignal()
	sceneOpenRequested		= pyqtSignal(str)
	sceneOpenFinished		= pyqtSignal(str)
	scenePreReset			= pyqtSignal()
	sceneReset				= pyqtSignal()
	sceneSaveRequested		= pyqtSignal(str)		# <str> The Filename
	sceneSaveFinished		= pyqtSignal(str)		# <str> The Filename
	
	# layer signals
	layerCreated			= pyqtSignal()
	layerDeleted			= pyqtSignal()
	layersModified			= pyqtSignal()
	layerStateChanged		= pyqtSignal()
	
	# object signals
	selectionChanged		= pyqtSignal()
	objectFreeze			= pyqtSignal(object)
	objectUnfreeze			= pyqtSignal(object)
	objectHide				= pyqtSignal(object)
	objectUnHide			= pyqtSignal(object)
	objectRenamed			= pyqtSignal(str, str, object)		# oldName, newName, Object
	valueChanged			= pyqtSignal(object, str, object)
	# object signals that may need disabled during imports, merges, file opening
	newObject				= pyqtSignal()		# linked signal for object creation
	objectCreated			= pyqtSignal(object)
	objectCloned			= pyqtSignal(object)
	objectAdded				= pyqtSignal(object)
	objectDeleted			= pyqtSignal(str)		# returns the name of the object that was just deleted
	objectPreDelete			= pyqtSignal(object)
	objectPostDelete		= pyqtSignal()
	objectParented			= pyqtSignal(object)	# the object that had its parenting changed
	# User props changes
	customPropChanged		= pyqtSignal(object)
	blurTagChanged			= pyqtSignal(object)
	
	# render signals
	rednerFrameRequested	= pyqtSignal(int)
	renderFrameFinished		= pyqtSignal()
	renderSceneRequested	= pyqtSignal(list)
	renderSceneFinished		= pyqtSignal()
	
	# time signals
	currentFrameChanged		= pyqtSignal(int)
	frameRangeChanged		= pyqtSignal()
	
	# application signals
	startupFinished			= pyqtSignal()
	shutdownStarted			= pyqtSignal()
	
	eventCalled = pyqtSignal(list)
	
	_instance = None
	
	def __init__(self):
		QObject.__init__(self)
	
	def __del__(self):
		print 'Removing Dispatch with __del__'
	
	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(Dispatch, cls).__new__(cls, *args, **kwargs)
			global blur3d, blurdev
			import blurdev
			cls._instance._linkedSignals = {}
			cls._process = None
			# Listen for changes to the blurdev environment, ie switching between beta, gold, or local
			blurdev.core.aboutToClearPaths.connect(cls._instance.disconnectSignals)
			import blur3d
		return cls._instance
	
	def disconnectSignals(self):
		"""
			\remarks	Handle cleanup of blur3d code, in this case disable any callbacks/events etc to blur3d.api.Dispatch
		"""
		debug.debugMsg( 'Disconnecting dispatch signals', debug.DebugLevel.Mid )
		try:
			blur3d.api.application.disconnect()
		except:
			pass
		import blurdev
		blurdev.core.aboutToClearPaths.disconnect(self.disconnectSignals)
#		self._instance = None
#		self._process = None
	
	def connect(self, signal, function):
		"""
			\remarks	All connections to software callbacks should be handled through this function. It will be responsible for dynamicly creating callbacks
						in the application only if something cares about it.
			\param		signal	<str>	The name of the signal you wish to connect to
			\param		function	<function>	a pointer to the function needed to run
		"""
		if ( hasattr(self,signal) and type(getattr(self,signal)).__name__ == 'pyqtBoundSignal' ):
			getattr(self,signal).connect(function)
	
	def disconnect(self, signal, function):
		"""
			\remarks	All disconnections to software callbacks should be handled through this function. It will be responsible for dynamicly creating callbacks
						in the application only if something cares about it.
			\param		signal	<str>	The name of the signal you wish to connect to
			\param		function	<function>	a pointer to the function needed to run
		"""
		if ( hasattr(self,signal) and type(getattr(self,signal)).__name__ == 'pyqtBoundSignal' ):
			getattr(self,signal).disconnect(function)
	
	def dispatch( self, signal, *args ):
		"""
			\remarks	dispatches a string based signal through the system from an application
			\param		signal	<str>
			\param		*args	<tuple> additional arguments
		"""
		if ( self.signalsBlocked() ):
			return
			
		# emit a defined pyqtSignal
		if ( hasattr(self,signal) and type(getattr(self,signal)).__name__ == 'pyqtBoundSignal' ):
			getattr(self,signal).emit(*args)
		
		# otherwise emit a custom signal
		else:
			from PyQt4.QtCore import SIGNAL
			self.emit( SIGNAL( signal ), *args )
		
		# emit linked signals
		if ( signal in self._linkedSignals ):
			for trigger in self._linkedSignals[signal]:
				self.dispatch( trigger )
	
	def dispatchObject( self, signal, *args ):
		"""
			\remarks	dispatches a string based signal through the system from an application
			\param		signal	<str>
			\param		*args	<tuple> additional arguments
		"""
		if ( self.signalsBlocked() ):
			return
			
		# emit a defined pyqtSignal
		if ( hasattr(self,signal) and type(getattr(self,signal)).__name__ == 'pyqtBoundSignal' ) and args[0]:
			getattr(self,signal).emit(blur3d.api.SceneObject(blur3d.api.Scene.instance(), args[0]))
		
		# otherwise emit a custom signal
		else:
			from PyQt4.QtCore import SIGNAL
			self.emit( SIGNAL( signal ), *args )
		
		# emit linked signals
		if ( signal in self._linkedSignals ):
			for trigger in self._linkedSignals[signal]:
				self.dispatch( trigger )
	
	def dispatchRename(self, signal, *args):
		if args:
			if len(args) == 3:
				oldName = args[0]
				newName = args[1]
				node = args[2]
			else:
				oldName = args[0][0]
				newName = args[0][1]
				node = args[0][2]
			if node:
				so = blur3d.api.SceneObject(blur3d.api.Scene.instance(), node)
				self.objectRenamed.emit(oldName, newName, so)
	
	def linkSignals( self, signal, trigger ):
		"""
			\remarks	creates a dependency so that when the inputed signal is dispatched, the dependent trigger signal is also dispatched.  This will only work
						for trigger signals that do not take any arguments for the dispatch.
			\param		signal		<str>
			\param		trigger		<str>
		"""
		if ( not signal in self._linkedSignals ):
			self._linkedSignals[ signal ] = [trigger]
		elif ( not trigger in self._linkedSignals[signal] ):
			self._linkedSignals[signal].append(trigger)
	
	def preDelete(self, callback, *args):
		blur3d.api.application.preDeleteObject(callback, *args)
	
	def postDelete(self, callback, *args):
		blur3d.api.application.postDeleteObject(callback, *args)
	
	def process(self):
		return self._process
	
	def setProcess(self, process):
		self._process = process
		self._process.start()
	