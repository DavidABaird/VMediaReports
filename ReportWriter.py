import pandas as pd

from CampaignDataSet import CampaignDataSet

class ReportWriter:
	def __init__ (self, outputFileName, dataSet):
		self.outputFileName = outputFileName
		self.dataSet = dataSet
		self.dataSet.addReportWriterObserver(self)
		self.myColumns = ["data_descriptor", "data"]
		self.reportDataPoints = pd.DataFrame(columns = self.myColumns)
		self.rowNumber = 0

	#adds row to the report
	def addDataPoint(self, categoryName, data):
		self.reportDataPoints.loc[self.rowNumber] = [categoryName,data]
		self.rowNumber+=1
		return data

	#exports report
	def writeReport(self):
		try:
			self.reportDataPoints.to_csv(self.outputFileName)
		except IOError:
			print "Error exporting csv"
			exit()


