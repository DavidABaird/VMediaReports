class DataSet(object):
	def __init__ (self):		
		#using the observer pattern for report writers allows encapsulation of
		#dataset objects and allows multiple reports to respond to single data sets
		#saving the memory and execution time associated with replicant datasets
		self.reportWriterObservers = []
		result = self.loadDataSet()
		if result < 0:
			print "Exception raised while reading one or more input files."
			exit()

	def loadDataSet(self):
		raise NotImplementedError

	#adds a reportWriterObserver
	def addReportWriterObserver(self, observer):
		self.reportWriterObservers.append(observer)

	#callback for report to add data to output csv
	def addDataToReport(self, categoryName, data):
		for obs in self.reportWriterObservers:
			obs.addDataPoint(categoryName, str(data))