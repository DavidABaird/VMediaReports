import pandas as pd
import collections
import json

from DataSet import DataSet

class CampaignDataSet(DataSet):
	def __init__(self, mainDataFile, mediaTypeDataFile):
		self.mainDataFile = mainDataFile
		self.mediaTypeDataFile = mediaTypeDataFile
		DataSet.__init__(self)

	'''
		Function to load designated file into the CampaignDataSet's pandas data frame.

		The following few lines of code split date and campaign columns into 
		3 separate columns respectively.They take a while to execute
		on large data sets but allow me to justify my decision.

		Given a prompt such as "How many unique campaigns ran in February" 
		one would have to take the date string of the format "XX-XX-XXXX"
		and analyze with regex, etc for each part of the (presumably massive 
		and potentially ongoing) report.  This is admittedly not a huge deal
		within the context of this exercise.

		However, in production (report generating) code it is safe to assume a wider 
		range and larger quantity of evaluations would be performed justifying 
		spending more time loading the data in order to lower the work necessary to process it.

		Additionally it improves readability of the rest of the codebase.
	'''
	def loadDataSet(self):
		print "Reading files..."
		try:
			self.dataSet = pd.read_csv(self.mainDataFile)
			mediaTemp = pd.read_csv(self.mediaTypeDataFile).drop_duplicates()
		except IOError:
			return -1
		print "Organizing data..."
		print "   -Dividing campaign names"

		dateColumnSplitter = lambda x: pd.Series([y for y in x.split('-')])
		campaignDescriptionSplitter = lambda x: pd.Series([y for y in x.split('_')])

		splitDates = self.dataSet['date'].apply(dateColumnSplitter).rename(columns={0:'year', 1: 'month', 2: 'day'})

		splitCampaignDescriptors = self.dataSet['campaign'].apply(campaignDescriptionSplitter).rename(columns={0:'initiative', 1: 'audience', 2: 'asset'})
		self.dataSet = pd.concat([self.dataSet, splitDates, splitCampaignDescriptors], axis = 1)

		#perform an eval() on each action string for a new col containing the resulting dictionaries
		print "   -Evaluating dictionaries"
		self.dataSet["action_array"] = self.dataSet["actions"].apply(eval)

		#rest of the function merges the object_type field from "source2" into the main data frame of
		#the CampaignDataSet
		print "   -Assigning object_type(s)"
		self.dataSet["object_type"] = "none"

		#since all assets seemed to be uniquely assets, initiatives=>initiatives etc
		#i took the liberty of simply designating categories to order the (potentially)
		#scrambled campaign names in "source2" type files
		initiativeTypes = self.dataSet['initiative'].unique()
		audienceTypes = self.dataSet['audience'].unique()
		assetTypes = self.dataSet['asset'].unique()
		
		#builds campaign name which conforms to the standards established for "source1" type files
		#then sets all object_type for all members of the dataset with the built campaign name
		print("   -Discerning campaign types (video/image)")
		for index, row in mediaTemp.iterrows():
			thisCampaignSplit = row.campaign.split("_")
			orderedCampaignBuilder = ["","",""]
			for campaignPart in thisCampaignSplit:
				if campaignPart in initiativeTypes:
					orderedCampaignBuilder[0] = campaignPart
				elif campaignPart in audienceTypes:
					orderedCampaignBuilder[1] = campaignPart
				elif campaignPart in assetTypes:
					orderedCampaignBuilder[2] = campaignPart
			orderedCampaignName = orderedCampaignBuilder[0] + "_" + orderedCampaignBuilder[1] + "_" + orderedCampaignBuilder[2]
			self.dataSet.ix[self.dataSet.campaign == orderedCampaignName, 'object_type'] = row.object_type

		return 1

	#returns the number of unique campaigns which occur durring the month (int 1-12) passed
	def uniqueCampaignsInMonth(self, month):
		monthStr = str(month)
		if len(monthStr) < 2:
			monthStr = "0" + monthStr
		ret = len(self.dataSet.loc[self.dataSet['month'] == monthStr].drop_duplicates('campaign'))
		self.addDataToReport("Unique campaigns in month " + str(month), ret)
		return ret
	
	#takes an initiative string and action string
	#returns the total number times that action occured in to/in conjunction with that initiative
	def countActionsOnInitiative(self, initiative, action):
		initiatives = self.dataSet.loc[self.dataSet['initiative'] == initiative]
		totalActions = 0
		for index, row in initiatives.iterrows():
			for a in row.action_array:
				if a["action"] == action:
					for member in a:
						if member != "action":
							totalActions+=a[member]
		self.addDataToReport("Total " + action + " actions performed on " + initiative + " initiative.", totalActions)
		return totalActions

	#finds the least Audience X Asset union with the cheapest conversions
	#
	#the docs were not entirely clear so i took the liberty of assuming that 
	#"the cheapest conversions" reffered to campaign which yeilds the best 
	#average (CPM || CPV)/(total conversions for this campaign instance) "ratio"
	def leastExpensiveConversionAudienceByAsset(self):
		conversionCostHash = {}
		for index, row in self.dataSet.iterrows():
			indexString = row.asset + "_" + row.audience

			#sum conversions/views for current campaign instance
			totalCampaignConv = 0
			totalCampaignViews = 0
			for a in row.action_array:
				if a["action"] == "conversions":
					for member in a:
						if member != "action":
							totalCampaignConv+=a[member]
				elif a["action"] == "views":
					for member in a:
						if member != "action":
							totalCampaignViews+=a[member]
			#ignore campaigns with no conversions
			if totalCampaignConv > 0:
				cost = 0
				#calc cost (CPM/CPV) for this conversion instance
				if row.object_type == "video" and totalCampaignViews > 0:
					cost = self.calculateCPV(totalCampaignViews, row.spend)
				else:
					cost = self.calculateCPM(row.impressions, row.spend)
				cost = cost / totalCampaignConv

				if indexString in conversionCostHash:
					conversionCostHash[indexString].append(cost)
				else:
					conversionCostHash[indexString] = [cost]

		avgCostSet = {}
		for costs in conversionCostHash:
			avgCostSet[costs] = sum(conversionCostHash[costs])/len(conversionCostHash[costs])

		minName = ""
		minVal = -1
		for combo in avgCostSet:
			if avgCostSet[combo] < minVal:
				minVal = avgCostSet[combo]
				minName = combo
			elif minVal == -1:
				minVal = avgCostSet[combo]
				minName = combo
		self.addDataToReport("Least Expensive Conversion (AudienceXAsset)", minName)
		return minName

	#calculate average cost per video view
	def averageCostPerVideoView(self):
		videoCampaignInstances = self.dataSet.loc[self.dataSet['object_type'] == "video"]
		viewCosts = []
		for index, row in videoCampaignInstances.iterrows():

			#find sum of views
			totalCampaignViews = 0
			for a in row.action_array:
				if a["action"] == "views":
					for member in a:
						if member != "action":
							totalCampaignViews+=a[member]

			if totalCampaignViews > 0:
				viewCosts.append(self.calculateCPV(totalCampaignViews, row.spend))
		ret = sum(viewCosts)/len(viewCosts)
		self.addDataToReport("Average cost per video view", ret)
		return ret


	def calculateCPM(self, impressions, spend):
		return spend/impressions * 1000

	def calculateCPV(self, views, spend):
		return spend/views